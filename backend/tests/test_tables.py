"""
Tests for Layer 5: Table Extraction.

Verifies:
  - Bordered table extraction via pdfplumber
  - Cell content accuracy (every value correct)
  - Header row detection
  - Table → Markdown conversion
  - Table matching with ContentBlocks from Layer 3
  - No false tables on non-table PDFs
"""

import sys
from pathlib import Path

import pytest
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.pipeline.extractor import extract_page_glyphs, extract_page_vectors, extract_page_images
from backend.app.pipeline.assembler import assemble
from backend.app.pipeline.layout_analyzer import HeaderFooterMask, analyze_layout
from backend.app.pipeline.semantic_analyzer import analyze_semantics
from backend.app.pipeline.table_extractor import (
    extract_tables_from_page,
    table_to_markdown,
    _raw_table_to_table_data,
)
from backend.app.models.document import BlockType, TableData, TableCell

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent / "test_output"


def _full_pipeline_with_tables(filename: str, page_num: int = 0):
    """Run extraction → assembly → layout → semantics → tables."""
    doc = fitz.open(str(FIXTURES / filename))
    page = doc.load_page(page_num)
    glyphs = extract_page_glyphs(page)
    vectors = extract_page_vectors(page)
    images = extract_page_images(page, doc, OUTPUT / "table_test", page_num)
    width = page.rect.width
    height = page.rect.height
    doc.close()

    blocks, catalog = assemble(glyphs)
    mask = HeaderFooterMask()
    content_blocks = analyze_layout(blocks, vectors, images, width, height, mask)
    content_blocks = analyze_semantics(content_blocks, catalog, height)

    # Run table extraction
    content_blocks = extract_tables_from_page(
        FIXTURES / filename, page_num, content_blocks
    )

    return content_blocks, catalog


class TestBorderedTableExtraction:
    """Step 5.1 — Bordered Table Extraction."""

    def test_table_extracted(self):
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.block_type == BlockType.TABLE and b.table_data]
        assert len(table_blocks) >= 1, "Should extract at least one table"

    def test_table_dimensions(self):
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        if table_blocks:
            td = table_blocks[0].table_data
            assert td.num_rows >= 4, f"Table should have ≥4 rows, got {td.num_rows}"
            assert td.num_cols >= 3, f"Table should have ≥3 cols, got {td.num_cols}"

    def test_cell_content_accuracy(self):
        """Critical: every cell value must be correct."""
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        assert len(table_blocks) >= 1

        td = table_blocks[0].table_data

        # Collect all cell text
        all_cells_text = [c.text for c in td.cells if c.text]

        # These exact values MUST appear
        required = ["Name", "Age", "City", "Alice", "Bob", "Charlie",
                     "30", "25", "35", "New York", "London", "Tokyo"]
        combined = " ".join(all_cells_text)
        for s in required:
            assert s in combined, f"Required cell value '{s}' not found in table"

    def test_header_row_detected(self):
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        if table_blocks:
            td = table_blocks[0].table_data
            header_cells = [c for c in td.cells if c.is_header]
            assert len(header_cells) >= 3, "Should have header cells"

    def test_no_table_in_simple_text(self):
        """Simple text PDF should not produce table data."""
        blocks, _ = _full_pipeline_with_tables("simple_text.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        assert len(table_blocks) == 0, "Simple text should have no tables"


class TestTableToMarkdown:
    """Step 5.4 — Table → Markdown Conversion."""

    def test_markdown_output(self):
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        if not table_blocks:
            pytest.skip("No table data extracted")

        md = table_to_markdown(table_blocks[0].table_data)
        assert md, "Markdown output should not be empty"

        lines = md.strip().split("\n")
        assert len(lines) >= 3, "Should have header + separator + data rows"

    def test_markdown_has_pipes(self):
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        if not table_blocks:
            pytest.skip("No table data extracted")

        md = table_to_markdown(table_blocks[0].table_data)
        for line in md.strip().split("\n"):
            assert line.startswith("|"), f"Row should start with |: {line}"
            assert line.endswith("|"), f"Row should end with |: {line}"

    def test_markdown_separator_row(self):
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        if not table_blocks:
            pytest.skip("No table data extracted")

        md = table_to_markdown(table_blocks[0].table_data)
        lines = md.strip().split("\n")
        # Second line should be separator (dashes)
        assert len(lines) >= 2
        sep = lines[1]
        assert "---" in sep or "- -" in sep, f"Separator row missing: {sep}"

    def test_markdown_content_accuracy(self):
        """Markdown table must contain all original cell values."""
        blocks, _ = _full_pipeline_with_tables("bordered_table.pdf")

        table_blocks = [b for b in blocks if b.table_data]
        if not table_blocks:
            pytest.skip("No table data extracted")

        md = table_to_markdown(table_blocks[0].table_data)
        required = ["Alice", "Bob", "Charlie", "30", "25", "35",
                     "New York", "London", "Tokyo"]
        for s in required:
            assert s in md, f"Required value '{s}' not in markdown table"

    def test_synthetic_table_to_markdown(self):
        """Test markdown conversion with synthetic data."""
        cells = [
            TableCell(text="Col1", row=0, col=0, is_header=True),
            TableCell(text="Col2", row=0, col=1, is_header=True),
            TableCell(text="A", row=1, col=0),
            TableCell(text="B", row=1, col=1),
            TableCell(text="C", row=2, col=0),
            TableCell(text="D", row=2, col=1),
        ]
        td = TableData(cells=cells, num_rows=3, num_cols=2)
        md = table_to_markdown(td)

        assert "Col1" in md
        assert "Col2" in md
        assert "A" in md
        assert "D" in md
        assert md.count("|") >= 9  # 3 rows × 3 pipes each

    def test_empty_cells_handled(self):
        """Tables with empty cells should not crash."""
        cells = [
            TableCell(text="H1", row=0, col=0, is_header=True),
            TableCell(text="H2", row=0, col=1, is_header=True),
            TableCell(text="", row=1, col=0),  # Empty cell
            TableCell(text="data", row=1, col=1),
        ]
        td = TableData(cells=cells, num_rows=2, num_cols=2)
        md = table_to_markdown(td)

        assert "H1" in md
        assert "data" in md

    def test_pipe_in_cell_escaped(self):
        """Pipe characters in cell text must be escaped."""
        cells = [
            TableCell(text="A|B", row=0, col=0, is_header=True),
            TableCell(text="C", row=0, col=1, is_header=True),
            TableCell(text="x", row=1, col=0),
            TableCell(text="y", row=1, col=1),
        ]
        td = TableData(cells=cells, num_rows=2, num_cols=2)
        md = table_to_markdown(td)

        assert "A\\|B" in md, "Pipe in cell text should be escaped"


class TestRawTableConversion:
    """Test _raw_table_to_table_data helper."""

    def test_basic_conversion(self):
        raw = [
            ["Name", "Value"],
            ["x", "1"],
            ["y", "2"],
        ]
        td = _raw_table_to_table_data(raw)

        assert td is not None
        assert td.num_rows == 3
        assert td.num_cols == 2

    def test_none_cells(self):
        raw = [
            ["A", "B"],
            [None, "C"],
        ]
        td = _raw_table_to_table_data(raw)
        assert td is not None

        cell = td.get_cell(1, 0)
        assert cell is not None
        assert cell.text == ""  # None → empty string

    def test_empty_table(self):
        td = _raw_table_to_table_data([])
        assert td is None
