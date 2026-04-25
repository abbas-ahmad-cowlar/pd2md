"""
Layer 3: Layout Analysis.

Detects page-level structural elements from assembled text blocks:
  - Headers/footers (repeated text across pages)
  - Multi-column layouts (gutter detection)
  - Table regions (bordered via vectors, borderless via alignment)
  - Image regions (with caption association)
  - Code blocks (monospace font regions)
  - Reading order determination

This layer classifies TextBlocks into ContentBlocks with semantic types,
preparing them for Layer 4 (fine-grained semantic inference).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from backend.app.models.document import (
    BBox,
    BlockType,
    ContentBlock,
    ExtractedImage,
    TextBlock,
    VectorPath,
)
from backend.app.utils.geometry import merge_bboxes

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------

@dataclass
class ColumnLayout:
    """Detected column structure for a page."""
    num_columns: int = 1
    gutter_positions: list[float] = field(default_factory=list)
    column_ranges: list[tuple[float, float]] = field(default_factory=list)  # (x_start, x_end)


@dataclass
class TableRegion:
    """A detected table region on a page."""
    bbox: BBox
    is_bordered: bool = True
    h_lines: list[VectorPath] = field(default_factory=list)
    v_lines: list[VectorPath] = field(default_factory=list)
    confidence: float = 0.8


@dataclass
class HeaderFooterMask:
    """Identifies which blocks are headers/footers to exclude from content."""
    header_y_threshold: float = 0.0   # Blocks above this y are headers
    footer_y_threshold: float = 0.0   # Blocks below this y are footers
    header_texts: set[str] = field(default_factory=set)
    footer_texts: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Step 3.1 — Header/Footer Detection
# ---------------------------------------------------------------------------

def detect_headers_footers(
    all_pages_blocks: list[list[TextBlock]],
    page_heights: list[float],
) -> HeaderFooterMask:
    """Detect running headers and footers by finding repeated text across pages.

    Strategy:
      1. Look at text in the top 10% and bottom 10% of each page
      2. Find text that repeats at similar positions across ≥60% of pages
      3. Detect page numbers (sequential numbers at consistent positions)

    Args:
        all_pages_blocks: List of block-lists, one per page.
        page_heights: Height of each page.

    Returns:
        HeaderFooterMask identifying repeated header/footer content.
    """
    if len(all_pages_blocks) < 2:
        # Need at least 2 pages to detect repetition
        return HeaderFooterMask()

    mask = HeaderFooterMask()
    num_pages = len(all_pages_blocks)
    threshold = max(2, int(num_pages * 0.5))  # Must appear on ≥50% of pages

    # Analyze top and bottom regions
    top_texts: dict[str, int] = {}
    bottom_texts: dict[str, int] = {}

    for page_idx, (blocks, page_h) in enumerate(zip(all_pages_blocks, page_heights)):
        top_cutoff = page_h * 0.08
        bottom_cutoff = page_h * 0.92

        for block in blocks:
            text = block.text.strip()
            if not text or len(text) > 100:  # Skip very long blocks
                continue

            # Normalize: remove page numbers for comparison
            normalized = re.sub(r'\b\d{1,4}\b', '#', text).strip()

            if block.bbox.y0 < top_cutoff:
                top_texts[normalized] = top_texts.get(normalized, 0) + 1
            elif block.bbox.y1 > bottom_cutoff:
                bottom_texts[normalized] = bottom_texts.get(normalized, 0) + 1

    # Texts appearing on enough pages are headers/footers
    for text, count in top_texts.items():
        if count >= threshold:
            mask.header_texts.add(text)

    for text, count in bottom_texts.items():
        if count >= threshold:
            mask.footer_texts.add(text)

    if mask.header_texts:
        logger.info(f"Detected {len(mask.header_texts)} header pattern(s)")
    if mask.footer_texts:
        logger.info(f"Detected {len(mask.footer_texts)} footer pattern(s)")

    return mask


def is_header_or_footer(
    block: TextBlock,
    mask: HeaderFooterMask,
    page_height: float,
) -> BlockType | None:
    """Check if a specific block is a header or footer.

    Args:
        block: The text block to check.
        mask: The detected header/footer patterns.
        page_height: Height of the page.

    Returns:
        BlockType.HEADER, BlockType.FOOTER, or None if it's regular content.
    """
    text = block.text.strip()
    if not text:
        return None

    normalized = re.sub(r'\b\d{1,4}\b', '#', text).strip()

    # Check position + text repetition
    if block.bbox.y0 < page_height * 0.08 and normalized in mask.header_texts:
        return BlockType.HEADER
    if block.bbox.y1 > page_height * 0.92 and normalized in mask.footer_texts:
        return BlockType.FOOTER

    # Standalone page numbers at top or bottom
    if re.match(r'^\s*\d{1,4}\s*$', text):
        if block.bbox.y0 < page_height * 0.06 or block.bbox.y1 > page_height * 0.94:
            return BlockType.FOOTER

    return None


# ---------------------------------------------------------------------------
# Step 3.2 — Column Detection
# ---------------------------------------------------------------------------

def detect_columns(
    blocks: list[TextBlock],
    page_width: float,
    page_height: float,
) -> ColumnLayout:
    """Detect multi-column layout by finding vertical gutters.

    Strategy:
      1. Collect left and right edges of all content blocks
      2. Find the largest horizontal gap between right-edges and left-edges
         in the middle zone of the page (not margins)
      3. Validate that both sides of the gap have significant content

    Args:
        blocks: TextBlocks on a single page.
        page_width: Width of the page.
        page_height: Height of the page.

    Returns:
        ColumnLayout describing the detected column structure.
    """
    if not blocks or len(blocks) < 4:
        return ColumnLayout(num_columns=1)

    # Filter out very short blocks (headers, page numbers)
    content_blocks = [b for b in blocks if b.bbox.height > 5]
    if len(content_blocks) < 4:
        return ColumnLayout(num_columns=1)

    # Collect all right-edges and left-edges of blocks
    # A gutter is a gap where blocks END (right edge) and START (left edge)
    # at roughly the same x but with a gap between them.
    # Exclude wide blocks (>55% page width) — these are full-width titles/headers
    # that span both columns and would confuse gutter detection.
    max_col_width = page_width * 0.55
    narrow_blocks = [b for b in content_blocks if b.bbox.width < max_col_width]
    if len(narrow_blocks) < 6:
        return ColumnLayout(num_columns=1)

    # Find the best vertical split that divides blocks into two groups.
    # Strategy: try candidate split points and pick the one where both sides
    # have the most blocks. A true column gutter has many blocks on each side
    # with consistent right-edges on the left and consistent left-edges on the right.
    middle_zone_start = page_width * 0.25
    middle_zone_end = page_width * 0.75

    # Collect candidate x-centers of gaps between blocks
    # For each block, we have x0 (left edge) and x1 (right edge)
    x_centers = sorted(b.bbox.center_x for b in narrow_blocks)

    best_score = 0
    best_split_x = 0.0

    # Try each midpoint between consecutive block centers as a split
    for i in range(len(x_centers) - 1):
        split_x = (x_centers[i] + x_centers[i + 1]) / 2
        if split_x < middle_zone_start or split_x > middle_zone_end:
            continue

        left_count = sum(1 for b in narrow_blocks if b.bbox.center_x < split_x)
        right_count = sum(1 for b in narrow_blocks if b.bbox.center_x >= split_x)

        # Score: prefer splits that are balanced AND have many blocks
        score = min(left_count, right_count)
        if score > best_score:
            best_score = score
            best_split_x = split_x

    # Need at least 3 blocks on each side
    if best_score < 3:
        return ColumnLayout(num_columns=1)

    # Verify there's actually a gap (not just a random split within text)
    # Use the median right-edge of left blocks and median left-edge of right blocks
    # to determine the gutter position. Using median (not max/min) to be robust
    # against outlier blocks like centered titles or page numbers.
    left_blocks_final = [b for b in narrow_blocks if b.bbox.center_x < best_split_x]
    right_blocks_final = [b for b in narrow_blocks if b.bbox.center_x >= best_split_x]

    left_x1_values = sorted(b.bbox.x1 for b in left_blocks_final)
    right_x0_values = sorted(b.bbox.x0 for b in right_blocks_final)

    # Use the 75th percentile of left x1 and 25th percentile of right x0
    # This ignores outliers on both sides
    p75_idx = int(len(left_x1_values) * 0.75)
    p25_idx = int(len(right_x0_values) * 0.25)
    typical_left_x1 = left_x1_values[min(p75_idx, len(left_x1_values) - 1)]
    typical_right_x0 = right_x0_values[min(p25_idx, len(right_x0_values) - 1)]

    if typical_right_x0 <= typical_left_x1:
        # Columns overlap — not a real column layout
        return ColumnLayout(num_columns=1)

    # Final validation: each column must span significant vertical extent.
    # Table cells may create a perfect horizontal split, but they don't
    # span much of the page height. True columns span ≥30% of the page.
    left_y_range = max(b.bbox.y1 for b in left_blocks_final) - min(b.bbox.y0 for b in left_blocks_final)
    right_y_range = max(b.bbox.y1 for b in right_blocks_final) - min(b.bbox.y0 for b in right_blocks_final)
    min_vertical_extent = page_height * 0.30

    if left_y_range < min_vertical_extent or right_y_range < min_vertical_extent:
        return ColumnLayout(num_columns=1)

    gutter_x = (typical_left_x1 + typical_right_x0) / 2

    return ColumnLayout(
        num_columns=2,
        gutter_positions=[gutter_x],
        column_ranges=[
            (0, gutter_x),
            (gutter_x, page_width),
        ],
    )



# ---------------------------------------------------------------------------
# Step 3.3 — Table Region Detection
# ---------------------------------------------------------------------------

def detect_table_regions(
    blocks: list[TextBlock],
    vectors: list[VectorPath],
    page_width: float,
    page_height: float,
) -> list[TableRegion]:
    """Detect table regions using vector lines and text alignment.

    Strategy A — Bordered tables:
      Find clusters of horizontal + vertical lines forming a grid.

    Strategy B — Borderless tables:
      Find text blocks with consistent column-like alignment.

    Args:
        blocks: TextBlocks on a single page.
        vectors: Vector paths from Layer 1.
        page_width: Width of the page.
        page_height: Height of the page.

    Returns:
        List of TableRegion objects.
    """
    regions: list[TableRegion] = []

    # ---- Strategy A: Bordered tables via line detection ----
    h_lines = [v for v in vectors if v.is_horizontal and v.bbox.width > 30]
    v_lines = [v for v in vectors if v.is_vertical and v.bbox.height > 15]

    if len(h_lines) >= 3 and len(v_lines) >= 2:
        # Find clusters of lines that form a grid
        # Group horizontal lines that are close together vertically (same table)
        h_lines_sorted = sorted(h_lines, key=lambda l: l.bbox.center_y)

        # Find tables by grouping lines with similar x-ranges
        table_groups = _cluster_table_lines(h_lines_sorted, v_lines)

        for h_group, v_group in table_groups:
            if len(h_group) >= 3 and len(v_group) >= 2:
                all_bboxes = [l.bbox for l in h_group] + [l.bbox for l in v_group]
                table_bbox = merge_bboxes(all_bboxes)

                # Verify: table shouldn't span the entire page
                if table_bbox.height < page_height * 0.9:
                    regions.append(TableRegion(
                        bbox=table_bbox,
                        is_bordered=True,
                        h_lines=h_group,
                        v_lines=v_group,
                        confidence=0.9,
                    ))

    # ---- Strategy B: Borderless tables (simpler heuristic) ----
    # Look for consecutive blocks with similar multi-column alignment
    # This is a simplified version; Phase 5 does the heavy lifting
    if not regions:
        borderless = _detect_borderless_tables(blocks)
        regions.extend(borderless)

    return regions


def _cluster_table_lines(
    h_lines: list[VectorPath],
    v_lines: list[VectorPath],
) -> list[tuple[list[VectorPath], list[VectorPath]]]:
    """Cluster horizontal and vertical lines into table groups.

    Lines belong to the same table if they share x-range (horizontal)
    or y-range (vertical) and are spatially close.
    """
    if not h_lines or not v_lines:
        return []

    # Simple approach: all lines within a spatial region form one table
    all_bboxes = merge_bboxes([l.bbox for l in h_lines + v_lines])

    # Filter v_lines that overlap with h_lines' horizontal range
    matching_v = [
        v for v in v_lines
        if v.bbox.x0 >= all_bboxes.x0 - 5 and v.bbox.x1 <= all_bboxes.x1 + 5
    ]
    matching_h = [
        h for h in h_lines
        if h.bbox.y0 >= all_bboxes.y0 - 5 and h.bbox.y1 <= all_bboxes.y1 + 5
    ]

    if matching_h and matching_v:
        return [(matching_h, matching_v)]
    return []


def _detect_borderless_tables(blocks: list[TextBlock]) -> list[TableRegion]:
    """Simple borderless table detection via column alignment.

    Looks for 3+ consecutive single-line blocks with similar multi-gap patterns.
    """
    # This is a placeholder — full borderless detection is complex
    # Phase 5 (TableExtractor) handles the deep analysis
    return []


# ---------------------------------------------------------------------------
# Step 3.4 — Image Region Detection
# ---------------------------------------------------------------------------

def detect_image_regions(
    images: list[ExtractedImage],
    blocks: list[TextBlock],
) -> list[ExtractedImage]:
    """Associate extracted images with their captions.

    Strategy:
      - Find text blocks near an image (above or below, within proximity)
      - Text matching patterns like "Fig.", "Figure", "Image" → caption
      - Associate the caption with the image

    Args:
        images: Extracted images from Layer 1.
        blocks: TextBlocks on the same page.

    Returns:
        Images with captions populated where detected.
    """
    caption_pattern = re.compile(
        r'^(fig\.?|figure|image|photo|illustration|diagram|chart|table)\s*\d*',
        re.IGNORECASE,
    )

    for image in images:
        best_caption = None
        best_distance = float('inf')

        for block in blocks:
            text = block.text.strip()
            if not text or len(text) > 200:
                continue

            # Check if text matches caption pattern
            if not caption_pattern.match(text):
                continue

            # Calculate distance from image to block
            # Prefer blocks immediately below the image
            if block.bbox.y0 >= image.bbox.y1:
                # Below the image
                distance = block.bbox.y0 - image.bbox.y1
            elif block.bbox.y1 <= image.bbox.y0:
                # Above the image
                distance = image.bbox.y0 - block.bbox.y1
            else:
                distance = 0  # Overlapping

            # Must be within reasonable proximity (50pt ≈ 0.7 inches)
            if distance < 50 and distance < best_distance:
                best_distance = distance
                best_caption = text

        if best_caption:
            image.caption = best_caption

    return images


# ---------------------------------------------------------------------------
# Step 3.5 — Code Block Detection
# ---------------------------------------------------------------------------

def detect_code_blocks(
    blocks: list[TextBlock],
    vectors: list[VectorPath],
) -> set[int]:
    """Detect which blocks are code blocks.

    Signals:
      - All text in monospace font
      - Multiple consecutive lines with consistent indentation
      - Background shading rectangle behind the text

    Args:
        blocks: TextBlocks on a single page.
        vectors: Vector paths (for background shading detection).

    Returns:
        Set of block indices that are code blocks.
    """
    code_indices: set[int] = set()

    # Detect background rectangles (potential code block backgrounds)
    bg_rects = [
        v for v in vectors
        if v.path_type == "rect" and v.fill_color is not None
        and v.bbox.area > 500  # Minimum size
    ]

    # First pass: detect code by monospace ratio
    mono_ratios: dict[int, float] = {}

    for idx, block in enumerate(blocks):
        if block.line_count == 0:
            continue

        # Check monospace ratio by character count (not span count)
        # This is more accurate when line-number spans (non-mono) are short
        all_spans = [s for line in block.lines for s in line.spans]
        non_space_spans = [s for s in all_spans if s.text.strip()]

        if not non_space_spans:
            continue

        total_chars = sum(len(s.text.strip()) for s in non_space_spans)
        mono_chars = sum(len(s.text.strip()) for s in non_space_spans if s.is_monospace)
        mono_ratio = mono_chars / total_chars if total_chars > 0 else 0
        mono_ratios[idx] = mono_ratio

        if mono_ratio >= 0.60:
            # Strong signal: majority of characters are monospace
            code_indices.add(idx)
            continue

        # Check for background shading
        for rect in bg_rects:
            if rect.bbox.contains(block.bbox) or (
                rect.bbox.overlaps(block.bbox)
                and mono_ratio >= 0.4
            ):
                code_indices.add(idx)
                break

    # Second pass: adjacency propagation
    # If a block is sandwiched between two code blocks, it's likely also code.
    # For blocks with some monospace content (≥30%), absorb if between code blocks.
    # For very short blocks (≤3 chars, e.g., bare line numbers like "4"), absorb
    # unconditionally if sandwiched — they're likely PDF line numbers.
    changed = True
    while changed:
        changed = False
        for idx in range(len(blocks)):
            if idx in code_indices:
                continue
            # Check if adjacent blocks (within 2 positions) are code
            has_code_before = any(i in code_indices for i in range(max(0, idx - 2), idx))
            has_code_after = any(i in code_indices for i in range(idx + 1, min(len(blocks), idx + 3)))
            if not (has_code_before and has_code_after):
                continue

            block_text = blocks[idx].text.strip() if blocks[idx].lines else ""
            is_short = len(block_text) <= 3
            has_mono = mono_ratios.get(idx, 0) >= 0.3

            if has_mono or is_short:
                code_indices.add(idx)
                changed = True

    return code_indices

# ---------------------------------------------------------------------------
# Step 3.5b — Column-Aware Block Splitting & Merging
# ---------------------------------------------------------------------------

def _merge_column_blocks(
    classified: list[tuple[TextBlock, BlockType, int]],
    column_layout: ColumnLayout,
) -> list[tuple[TextBlock, BlockType, int]]:
    """Split blocks that span both columns, then merge same-column blocks.

    In two-column PDFs, the assembler may create blocks whose lines
    come from both columns (because lines at the same Y get grouped).
    This function:
      1) Splits such blocks into separate left/right column blocks
      2) Merges adjacent blocks within the same column
    """
    if not classified or column_layout.num_columns < 2:
        return classified

    gutter_x = column_layout.gutter_positions[0]

    # Step 1: Split any UNKNOWN blocks that have lines in both columns
    split_result: list[tuple[TextBlock, BlockType, int]] = []

    for block, btype, idx in classified:
        if btype != BlockType.UNKNOWN or not block.lines:
            split_result.append((block, btype, idx))
            continue

        left_lines = []
        right_lines = []

        for line in block.lines:
            # Each line's center determines its column
            line_center_x = (line.bbox.x0 + line.bbox.x1) / 2
            if line_center_x < gutter_x:
                left_lines.append(line)
            else:
                right_lines.append(line)

        if left_lines and right_lines:
            # Block spans both columns — split
            left_bbox = merge_bboxes([l.bbox for l in left_lines])
            right_bbox = merge_bboxes([l.bbox for l in right_lines])
            left_block = TextBlock(lines=left_lines, bbox=left_bbox)
            right_block = TextBlock(lines=right_lines, bbox=right_bbox)
            split_result.append((left_block, BlockType.UNKNOWN, idx))
            split_result.append((right_block, BlockType.UNKNOWN, idx))
        else:
            split_result.append((block, btype, idx))

    # Step 2: Merge adjacent same-column UNKNOWN blocks
    merged: list[tuple[TextBlock, BlockType, int]] = []
    i = 0

    while i < len(split_result):
        block, btype, idx = split_result[i]

        if btype != BlockType.UNKNOWN:
            merged.append(split_result[i])
            i += 1
            continue

        is_left = block.bbox.center_x < gutter_x
        group = [split_result[i]]
        j = i + 1

        while j < len(split_result):
            nb, nt, ni = split_result[j]
            if nt != BlockType.UNKNOWN:
                break
            nb_is_left = nb.bbox.center_x < gutter_x
            if nb_is_left != is_left:
                j += 1
                continue  # skip blocks from the other column
            # Same column — check Y proximity
            last_b = group[-1][0]
            y_gap = nb.bbox.y0 - last_b.bbox.y1
            if y_gap > last_b.bbox.height * 3:
                break
            group.append(split_result[j])
            # Remove from the position we consumed
            split_result.pop(j)

        if len(group) == 1:
            merged.append(group[0])
        else:
            all_lines = []
            for gb, _, _ in group:
                all_lines.extend(gb.lines)
            all_lines.sort(key=lambda l: l.bbox.y0)
            grp_bbox = merge_bboxes([gb.bbox for gb, _, _ in group])
            merged_block = TextBlock(lines=all_lines, bbox=grp_bbox)
            merged.append((merged_block, BlockType.UNKNOWN, group[0][2]))

        i += 1

    return merged


# ---------------------------------------------------------------------------
# Step 3.6 — Reading Order Determination
# ---------------------------------------------------------------------------

def determine_reading_order(
    blocks: list[TextBlock],
    column_layout: ColumnLayout,
    table_regions: list[TableRegion],
    images: list[ExtractedImage],
    code_indices: set[int],
    hf_mask: HeaderFooterMask,
    page_height: float,
) -> list[ContentBlock]:
    """Establish the correct reading order and classify blocks.

    For single-column: sort by y-coordinate (top-to-bottom).
    For multi-column: process left column first, then right column.
    Headers/footers are marked but excluded from content flow.

    Args:
        blocks: TextBlocks on a single page.
        column_layout: Detected column layout.
        table_regions: Detected table regions.
        images: Extracted images.
        code_indices: Indices of blocks that are code.
        hf_mask: Header/footer detection mask.
        page_height: Height of the page.

    Returns:
        List of ContentBlock in correct reading order.
    """
    content_blocks: list[ContentBlock] = []

    # First pass: classify each block
    classified: list[tuple[TextBlock, BlockType, int]] = []

    for idx, block in enumerate(blocks):
        # Check header/footer
        hf_type = is_header_or_footer(block, hf_mask, page_height)
        if hf_type:
            classified.append((block, hf_type, idx))
            continue

        # Check code block
        if idx in code_indices:
            classified.append((block, BlockType.CODE_BLOCK, idx))
            continue

        # Check if block is inside a table region
        in_table = False
        for region in table_regions:
            if region.bbox.contains(block.bbox) or region.bbox.overlaps(block.bbox):
                in_table = True
                break
        if in_table:
            classified.append((block, BlockType.TABLE, idx))
            continue

        # Default: unclassified content (will be refined in Layer 4)
        classified.append((block, BlockType.UNKNOWN, idx))

    # Column-aware merge: in multi-column layouts, merge adjacent
    # single-line blocks that belong to the same column into multi-line blocks.
    if column_layout.num_columns > 1:
        classified = _merge_column_blocks(classified, column_layout)

    # Second pass: sort by reading order
    if column_layout.num_columns == 1:
        # Single column: simple top-to-bottom sort
        ordered = sorted(classified, key=lambda x: x[0].bbox.y0)
    else:
        # Multi-column: correct reading order
        # Full-width blocks first (at their Y position), then left col, then right col
        gutter_x = column_layout.gutter_positions[0]

        # Separate headers/footers
        headers_footers = [(b, t, i) for b, t, i in classified
                           if t in (BlockType.HEADER, BlockType.FOOTER)]
        content = [(b, t, i) for b, t, i in classified
                   if t not in (BlockType.HEADER, BlockType.FOOTER)]

        # Full-width: block spans over 60% of page or crosses the gutter
        full_width = []
        left_col = []
        right_col = []

        for item in content:
            b = item[0]
            block_width = b.bbox.x1 - b.bbox.x0
            page_w = column_layout.column_ranges[-1][1] if column_layout.column_ranges else 612
            spans_gutter = b.bbox.x0 < gutter_x and b.bbox.x1 > gutter_x
            is_wide = block_width > page_w * 0.55

            if spans_gutter or is_wide:
                full_width.append(item)
            elif b.bbox.center_x < gutter_x:
                left_col.append(item)
            else:
                right_col.append(item)

        # Sort each group top-to-bottom
        full_width.sort(key=lambda x: x[0].bbox.y0)
        left_col.sort(key=lambda x: x[0].bbox.y0)
        right_col.sort(key=lambda x: x[0].bbox.y0)

        # Interleave full-width blocks at their correct Y positions
        # relative to column content
        ordered = []
        li, ri, fi = 0, 0, 0
        col_items = left_col + right_col  # Left then right

        # First: emit all full-width blocks that come before any column content
        all_col_min_y = min((b.bbox.y0 for b, _, _ in col_items), default=9999)
        while fi < len(full_width) and full_width[fi][0].bbox.y0 <= all_col_min_y:
            ordered.append(full_width[fi])
            fi += 1

        # Then: left column content
        ordered.extend(left_col)

        # Then: any full-width blocks between columns
        left_max_y = max((b.bbox.y1 for b, _, _ in left_col), default=0)
        right_min_y = min((b.bbox.y0 for b, _, _ in right_col), default=9999)
        while fi < len(full_width) and full_width[fi][0].bbox.y0 <= right_min_y:
            ordered.append(full_width[fi])
            fi += 1

        # Then: right column content
        ordered.extend(right_col)

        # Then: remaining full-width blocks
        while fi < len(full_width):
            ordered.append(full_width[fi])
            fi += 1

        # Headers/footers at the end (they're excluded from output anyway)
        ordered.extend(headers_footers)

    # Third pass: create ContentBlocks
    for block, block_type, idx in ordered:
        content_block = ContentBlock(
            block_type=block_type,
            bbox=block.bbox,
            text_block=block,
            confidence=0.8 if block_type == BlockType.UNKNOWN else 0.9,
        )

        if block_type == BlockType.CODE_BLOCK:
            content_block.code_language = _guess_code_language(block.text)

        content_blocks.append(content_block)

    # Add image blocks at appropriate positions
    for image in images:
        img_block = ContentBlock(
            block_type=BlockType.IMAGE,
            bbox=image.bbox,
            image_ref=image,
            confidence=0.95,
        )
        # Insert after the last block that's above the image
        insert_pos = 0
        for i, cb in enumerate(content_blocks):
            if cb.bbox.y1 <= image.bbox.y0 and cb.block_type not in (
                BlockType.HEADER, BlockType.FOOTER
            ):
                insert_pos = i + 1
        content_blocks.insert(insert_pos, img_block)

    return content_blocks


def _guess_code_language(text: str) -> str:
    """Simple heuristic to guess programming language from code content."""
    text_lower = text.lower()
    if "def " in text_lower or "import " in text_lower or "class " in text_lower:
        return "python"
    if "function " in text_lower or "const " in text_lower or "var " in text_lower:
        return "javascript"
    if "#include" in text_lower or "int main" in text_lower:
        return "c"
    if "public class" in text_lower or "System.out" in text_lower:
        return "java"
    if "fn " in text_lower or "let mut" in text_lower:
        return "rust"
    return ""


# ---------------------------------------------------------------------------
# Full Layout Analysis Pipeline
# ---------------------------------------------------------------------------

def analyze_layout(
    page_blocks: list[TextBlock],
    vectors: list[VectorPath],
    images: list[ExtractedImage],
    page_width: float,
    page_height: float,
    hf_mask: HeaderFooterMask,
) -> list[ContentBlock]:
    """Run the complete Layer 3 layout analysis for a single page.

    Pipeline:
      1. Detect columns
      2. Detect table regions
      3. Associate image captions
      4. Detect code blocks
      5. Determine reading order and classify blocks

    Args:
        page_blocks: Assembled TextBlocks for this page.
        vectors: Vector paths for this page.
        images: Extracted images for this page.
        page_width: Width of the page.
        page_height: Height of the page.
        hf_mask: Header/footer detection results (from multi-page analysis).

    Returns:
        List of ContentBlocks in correct reading order.
    """
    # Step 3.2: Column detection
    columns = detect_columns(page_blocks, page_width, page_height)
    if columns.num_columns > 1:
        logger.info(f"Detected {columns.num_columns}-column layout")

    # Step 3.3: Table region detection
    table_regions = detect_table_regions(page_blocks, vectors, page_width, page_height)
    if table_regions:
        logger.info(f"Detected {len(table_regions)} table region(s)")

    # Step 3.4: Image caption association
    images = detect_image_regions(images, page_blocks)

    # Step 3.5: Code block detection
    code_indices = detect_code_blocks(page_blocks, vectors)
    if code_indices:
        logger.info(f"Detected {len(code_indices)} code block(s)")

    # Step 3.6: Reading order + classification
    content_blocks = determine_reading_order(
        page_blocks, columns, table_regions, images,
        code_indices, hf_mask, page_height,
    )

    return content_blocks
