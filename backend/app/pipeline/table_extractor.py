"""
Layer 5: Table Extraction.

Extracts structured table data from PDF pages:
  - Bordered tables via pdfplumber (line-based detection)
  - Borderless tables via text alignment analysis
  - Merged cell detection
  - Table → Markdown conversion

Uses pdfplumber as the primary engine for table detection and cell extraction,
falling back to heuristic text-alignment for borderless tables.

Content accuracy principle: Every cell value must be character-perfect.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

from backend.app.models.document import (
    BBox,
    BlockType,
    ContentBlock,
    TableCell,
    TableData,
    TextBlock,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 5.1 — Bordered Table Extraction (pdfplumber)
# ---------------------------------------------------------------------------

def extract_tables_from_page(
    pdf_path: Path,
    page_number: int,
    content_blocks: list[ContentBlock],
) -> list[ContentBlock]:
    """Extract structured table data for TABLE-classified blocks.

    Uses pdfplumber to detect and extract tables from the page,
    then matches them to TABLE ContentBlocks from Layer 3/4.

    Args:
        pdf_path: Path to the PDF file.
        page_number: 0-based page number.
        content_blocks: ContentBlocks for this page (some typed TABLE).

    Returns:
        Updated ContentBlocks with TableData populated for TABLE blocks.
    """
    # Check if any blocks are classified as TABLE
    table_blocks = [b for b in content_blocks if b.block_type == BlockType.TABLE]
    if not table_blocks:
        return content_blocks

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            if page_number >= len(pdf.pages):
                logger.warning(f"Page {page_number} out of range for pdfplumber")
                return content_blocks

            page = pdf.pages[page_number]

            # Extract all tables on the page
            tables = page.extract_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 5,
                    "join_tolerance": 5,
                    "edge_min_length": 10,
                    "min_words_vertical": 1,
                    "min_words_horizontal": 1,
                }
            )

            if not tables:
                # Fallback 1: Try lines_strict with relaxed thresholds (booktabs)
                tables = page.extract_tables(
                    table_settings={
                        "vertical_strategy": "text",
                        "horizontal_strategy": "lines",
                        "snap_tolerance": 8,
                        "join_tolerance": 8,
                        "edge_min_length": 5,
                        "min_words_vertical": 2,
                    }
                )

            if not tables:
                # Fallback 2: Try fully text-based strategy
                tables = page.extract_tables(
                    table_settings={
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 5,
                        "join_tolerance": 5,
                    }
                )

            if not tables:
                logger.info(f"No tables found by pdfplumber on page {page_number}")
                # Convert TABLE blocks back to paragraphs
                for block in table_blocks:
                    block.block_type = BlockType.PARAGRAPH
                return content_blocks

            # Also get table bounding boxes for matching
            table_finder = page.find_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 5,
                    "join_tolerance": 5,
                    "edge_min_length": 10,
                }
            )

            # Match pdfplumber tables to our TABLE ContentBlocks
            for tbl_idx, raw_table in enumerate(tables):
                if not raw_table or len(raw_table) < 2:
                    continue

                # Get bounding box if available
                tbl_bbox = None
                if tbl_idx < len(table_finder):
                    tb = table_finder[tbl_idx]
                    tbl_bbox = BBox(
                        x0=tb.bbox[0], y0=tb.bbox[1],
                        x1=tb.bbox[2], y1=tb.bbox[3],
                    )

                # Build TableData from raw table
                table_data = _raw_table_to_table_data(raw_table, tbl_bbox)

                if table_data:
                    # Find the best matching TABLE block
                    best_block = _find_matching_table_block(
                        table_blocks, tbl_bbox, tbl_idx
                    )

                    if best_block:
                        best_block.table_data = table_data
                        best_block.confidence = 0.9

            # Remove text_block from TABLE blocks that now have table_data
            # (the text was just the raw cell text, now structured)
            for block in table_blocks:
                if block.table_data:
                    block.text_block = None

    except Exception as e:
        logger.error(f"pdfplumber table extraction failed on page {page_number}: {e}")

    return content_blocks


def _raw_table_to_table_data(
    raw_table: list[list[str | None]],
    bbox: BBox | None = None,
) -> TableData | None:
    """Convert pdfplumber's raw table output to our TableData model.

    pdfplumber returns a list of rows, where each row is a list of cell strings.
    None values indicate empty cells or merged cells.

    Args:
        raw_table: Raw table from pdfplumber (list of rows of strings).
        bbox: Optional bounding box of the table.

    Returns:
        TableData object, or None if the table is invalid.
    """
    if not raw_table:
        return None

    num_rows = len(raw_table)
    num_cols = max(len(row) for row in raw_table) if raw_table else 0

    if num_rows < 1 or num_cols < 1:
        return None

    cells: list[TableCell] = []

    for row_idx, row in enumerate(raw_table):
        for col_idx, cell_text in enumerate(row):
            # Normalize cell content
            text = (cell_text or "").strip()
            text = text.replace("\n", " ")  # Flatten multi-line cells

            cell = TableCell(
                text=text,
                row=row_idx,
                col=col_idx,
                rowspan=1,
                colspan=1,
                is_header=(row_idx == 0),  # First row assumed header
                alignment=_detect_alignment(text),
            )
            cells.append(cell)

    # Detect merged cells (Step 5.3)
    cells = _detect_merged_cells(cells, raw_table, num_rows, num_cols)

    return TableData(
        cells=cells,
        num_rows=num_rows,
        num_cols=num_cols,
        has_header=True,
        bbox=bbox,
    )


def _detect_alignment(text: str) -> str:
    """Detect text alignment from content patterns."""
    if not text:
        return "left"
    # Numbers are typically right-aligned
    stripped = text.strip().replace(",", "").replace(".", "").replace("-", "")
    if stripped.isdigit():
        return "right"
    return "left"


# ---------------------------------------------------------------------------
# Step 5.3 — Merged Cell Detection
# ---------------------------------------------------------------------------

def _detect_merged_cells(
    cells: list[TableCell],
    raw_table: list[list[str | None]],
    num_rows: int,
    num_cols: int,
) -> list[TableCell]:
    """Detect and mark merged cells.

    Strategy: If a cell is None/empty and its neighbor directly above or left
    has text, it's likely merged. Expand the span of the non-empty cell.

    This is a heuristic — perfect merged cell detection requires PDF
    structure analysis which pdfplumber handles for bordered tables.
    """
    # Build a grid for quick lookup
    grid: dict[tuple[int, int], TableCell] = {}
    for cell in cells:
        grid[(cell.row, cell.col)] = cell

    # Check for vertical merges (same text repeated vertically = merge)
    for col in range(num_cols):
        row = 0
        while row < num_rows:
            cell = grid.get((row, col))
            if cell and cell.text:
                # Count how many rows below have empty cells in this column
                span = 1
                for r in range(row + 1, num_rows):
                    next_cell = grid.get((r, col))
                    if next_cell and not next_cell.text:
                        span += 1
                    else:
                        break
                if span > 1:
                    cell.rowspan = span
                row += span
            else:
                row += 1

    return cells


def _find_matching_table_block(
    table_blocks: list[ContentBlock],
    tbl_bbox: BBox | None,
    table_index: int,
) -> ContentBlock | None:
    """Find the ContentBlock that best matches a pdfplumber table.

    Uses bounding box overlap if available, otherwise assigns by index.
    """
    if not table_blocks:
        return None

    if tbl_bbox:
        # Find block with best bbox overlap
        best_overlap = 0.0
        best_block = None
        for block in table_blocks:
            if block.table_data:  # Already assigned
                continue
            if block.bbox.overlaps(tbl_bbox):
                # Calculate overlap area ratio
                overlap_x = min(block.bbox.x1, tbl_bbox.x1) - max(block.bbox.x0, tbl_bbox.x0)
                overlap_y = min(block.bbox.y1, tbl_bbox.y1) - max(block.bbox.y0, tbl_bbox.y0)
                if overlap_x > 0 and overlap_y > 0:
                    overlap = overlap_x * overlap_y
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_block = block
        if best_block:
            return best_block

    # Fallback: assign by index
    unassigned = [b for b in table_blocks if not b.table_data]
    if table_index < len(unassigned):
        return unassigned[table_index]

    return unassigned[0] if unassigned else None


# ---------------------------------------------------------------------------
# Step 5.4 — Table → Markdown Conversion
# ---------------------------------------------------------------------------

def table_to_markdown(table_data: TableData) -> str:
    """Convert structured TableData to Markdown table syntax.

    Produces a GFM-compatible table with:
      - Header row (first row, bold)
      - Separator row with alignment markers
      - Data rows

    Args:
        table_data: Structured table data.

    Returns:
        Markdown table string.
    """
    if not table_data.cells or table_data.num_cols == 0:
        return ""

    # Build a 2D grid
    grid: list[list[str]] = []
    for row_idx in range(table_data.num_rows):
        row_cells = table_data.get_row(row_idx)
        row_texts = []
        for col_idx in range(table_data.num_cols):
            cell = table_data.get_cell(row_idx, col_idx)
            text = cell.text if cell else ""
            # Escape pipe characters in cell content
            text = text.replace("|", "\\|")
            row_texts.append(text)
        grid.append(row_texts)

    if not grid:
        return ""

    # Calculate column widths for alignment
    col_widths = [3] * table_data.num_cols  # Minimum 3 chars for separator
    for row in grid:
        for col_idx, text in enumerate(row):
            if col_idx < len(col_widths):
                col_widths[col_idx] = max(col_widths[col_idx], len(text))

    # Get alignments from header row
    alignments = []
    for col_idx in range(table_data.num_cols):
        cell = table_data.get_cell(0, col_idx)
        alignments.append(cell.alignment if cell else "left")

    lines: list[str] = []

    # Header row
    header = "| " + " | ".join(
        grid[0][i].ljust(col_widths[i]) if i < len(grid[0]) else " " * col_widths[i]
        for i in range(table_data.num_cols)
    ) + " |"
    lines.append(header)

    # Separator row
    sep_parts = []
    for i in range(table_data.num_cols):
        w = col_widths[i]
        if alignments[i] == "right":
            sep_parts.append("-" * (w - 1) + ":")
        elif alignments[i] == "center":
            sep_parts.append(":" + "-" * (w - 2) + ":")
        else:
            sep_parts.append("-" * w)
    separator = "| " + " | ".join(sep_parts) + " |"
    lines.append(separator)

    # Data rows
    for row_idx in range(1, len(grid)):
        row = "| " + " | ".join(
            grid[row_idx][i].ljust(col_widths[i])
            if i < len(grid[row_idx])
            else " " * col_widths[i]
            for i in range(table_data.num_cols)
        ) + " |"
        lines.append(row)

    return "\n".join(lines)
