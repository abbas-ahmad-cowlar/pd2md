"""
Layer 2: Text Assembly.

Transforms raw glyphs (Layer 1 output) into structured text:
    Glyphs → Spans (styled text runs) → Lines → Blocks

This layer handles:
  - Word boundary detection via inter-glyph gap analysis
  - Line grouping via y-coordinate clustering
  - Block grouping via vertical gap analysis
  - Span merging (adjacent chars with same style → single span)
  - Dehyphenation (rejoin words split across line breaks)
  - Font catalog construction (identify body font, heading fonts, etc.)

Content accuracy principle: The text content produced here must be
character-perfect. Every word, number, and symbol must match the PDF.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from backend.app.models.document import (
    BBox,
    FontCatalog,
    FontInfo,
    RawGlyph,
    TextBlock,
    TextLine,
    TextSpan,
)
from backend.app.utils.geometry import merge_bboxes

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 2.1 — Glyph → Span Assembly (with word boundary detection)
# ---------------------------------------------------------------------------

def _glyphs_to_line_groups(glyphs: list[RawGlyph]) -> list[list[RawGlyph]]:
    """Group glyphs into horizontal line groups by y-coordinate similarity.

    Glyphs are on the same line if their vertical centers are within
    a tolerance of each other (half font size).

    Returns:
        List of glyph groups, each group is one visual line, 
        sorted top-to-bottom then left-to-right within each line.
    """
    if not glyphs:
        return []

    # Sort by vertical position (top to bottom), then horizontal (left to right)
    sorted_glyphs = sorted(glyphs, key=lambda g: (g.bbox.center_y, g.bbox.x0))

    lines: list[list[RawGlyph]] = []
    current_line: list[RawGlyph] = [sorted_glyphs[0]]
    current_y = sorted_glyphs[0].bbox.center_y

    for glyph in sorted_glyphs[1:]:
        # Tolerance: half the font size adapts to varying text sizes
        tolerance = max(glyph.font_size, current_line[-1].font_size) * 0.4
        if abs(glyph.bbox.center_y - current_y) <= tolerance:
            current_line.append(glyph)
        else:
            # Sort the completed line left-to-right
            current_line.sort(key=lambda g: g.bbox.x0)
            lines.append(current_line)
            current_line = [glyph]
            current_y = glyph.bbox.center_y

    # Don't forget the last line
    current_line.sort(key=lambda g: g.bbox.x0)
    lines.append(current_line)

    return lines


def _detect_word_boundaries(line_glyphs: list[RawGlyph]) -> list[TextSpan]:
    """Convert a line of glyphs into TextSpans with word boundaries detected.

    Word boundaries are detected by comparing inter-glyph gaps against
    the average character width. A gap significantly larger than normal
    kerning indicates a space/word boundary.

    This also merges adjacent characters with the same styling into
    single TextSpan objects (avoiding character-level spans).
    """
    if not line_glyphs:
        return []

    spans: list[TextSpan] = []

    # Calculate average character width for this line
    char_widths = [g.bbox.width for g in line_glyphs if g.bbox.width > 0]
    avg_char_width = sum(char_widths) / len(char_widths) if char_widths else 5.0

    # Space threshold: gap > 30% of average char width
    # This is conservative to avoid inserting false spaces
    space_threshold = avg_char_width * 0.3

    # Build spans by accumulating characters with same style
    current_text = line_glyphs[0].char
    current_glyphs = [line_glyphs[0]]
    current_style = _glyph_style_key(line_glyphs[0])

    for i in range(1, len(line_glyphs)):
        prev = line_glyphs[i - 1]
        curr = line_glyphs[i]

        # Calculate gap between previous glyph's right edge and current's left edge
        gap = curr.bbox.x0 - prev.bbox.x1

        # Check if style changed
        new_style = _glyph_style_key(curr)

        if gap > space_threshold or new_style != current_style:
            # Emit the accumulated span
            span = _create_span(current_text, current_glyphs, line_glyphs)
            spans.append(span)

            # Start new span, with space prefix if there's a gap
            if gap > space_threshold and new_style == current_style:
                # Same style: add space and continue
                current_text = " " + curr.char
                current_glyphs = [curr]
            elif gap > space_threshold:
                # Different style with gap: emit space in prev style, then start new
                current_text = " " + curr.char
                current_glyphs = [curr]
                current_style = new_style
            else:
                # Style change without gap
                current_text = curr.char
                current_glyphs = [curr]
                current_style = new_style
        else:
            current_text += curr.char
            current_glyphs.append(curr)

    # Emit final span
    if current_text:
        span = _create_span(current_text, current_glyphs, line_glyphs)
        spans.append(span)

    return spans


def _glyph_style_key(glyph: RawGlyph) -> tuple:
    """Create a hashable style key for grouping same-styled characters."""
    return (
        glyph.font_name,
        round(glyph.font_size, 1),
        glyph.is_bold,
        glyph.is_italic,
        glyph.is_monospace,
        glyph.color,
    )


def _create_span(
    text: str,
    span_glyphs: list[RawGlyph],
    line_glyphs: list[RawGlyph],
) -> TextSpan:
    """Create a TextSpan from accumulated text and glyph metadata."""
    # Use the first glyph for style info (all should be same style)
    ref = span_glyphs[0]

    # Compute bounding box from all glyphs in this span
    bbox = merge_bboxes([g.bbox for g in span_glyphs])

    # Detect superscript/subscript by comparing baseline with line average
    line_baseline = sum(g.origin_y for g in line_glyphs) / len(line_glyphs)
    avg_size = sum(g.font_size for g in line_glyphs) / len(line_glyphs)
    span_baseline = sum(g.origin_y for g in span_glyphs) / len(span_glyphs)

    is_superscript = (
        ref.font_size < avg_size * 0.8
        and span_baseline < line_baseline - avg_size * 0.15
    )
    is_subscript = (
        ref.font_size < avg_size * 0.8
        and span_baseline > line_baseline + avg_size * 0.15
    )

    return TextSpan(
        text=text,
        bbox=bbox,
        font_name=ref.font_name,
        font_size=ref.font_size,
        is_bold=ref.is_bold,
        is_italic=ref.is_italic,
        is_monospace=ref.is_monospace,
        is_superscript=is_superscript,
        is_subscript=is_subscript,
        color=ref.color,
    )


# ---------------------------------------------------------------------------
# Step 2.2 — Spans → TextLine Assembly
# ---------------------------------------------------------------------------

def assemble_lines(glyphs: list[RawGlyph]) -> list[TextLine]:
    """Assemble raw glyphs into TextLines.

    Pipeline:
      1. Group glyphs by y-coordinate into line groups
      2. For each line group, detect word boundaries and create spans
      3. Package spans into TextLine objects with computed bounding boxes

    Args:
        glyphs: Raw glyphs from Layer 1.

    Returns:
        List of TextLine objects, sorted top-to-bottom.
    """
    if not glyphs:
        return []

    line_groups = _glyphs_to_line_groups(glyphs)

    # Split lines that span multiple columns (large horizontal gap within a line)
    line_groups = _split_column_lines(line_groups)

    text_lines: list[TextLine] = []

    for line_glyphs in line_groups:
        spans = _detect_word_boundaries(line_glyphs)
        if not spans:
            continue

        line_bbox = merge_bboxes([s.bbox for s in spans])
        text_lines.append(TextLine(spans=spans, bbox=line_bbox))

    return text_lines


def _split_column_lines(line_groups: list[list[RawGlyph]]) -> list[list[RawGlyph]]:
    """Split lines that have a large horizontal gap (column gutter).

    In two-column PDFs, glyphs at the same Y but in different columns
    get grouped into one line. This splits such lines at the gutter into
    separate lines.

    A gap is considered a column gutter if it's > 3x the average character
    width within that line.
    """
    result: list[list[RawGlyph]] = []

    for line_glyphs in line_groups:
        if len(line_glyphs) < 4:
            result.append(line_glyphs)
            continue

        # Calculate inter-glyph gaps sorted by position
        sorted_g = sorted(line_glyphs, key=lambda g: g.bbox.x0)
        gaps = []
        for i in range(1, len(sorted_g)):
            gap = sorted_g[i].bbox.x0 - sorted_g[i - 1].bbox.x1
            gaps.append((gap, i))

        if not gaps:
            result.append(line_glyphs)
            continue

        # Average character width as reference
        char_widths = [g.bbox.width for g in sorted_g if g.bbox.width > 0]
        avg_cw = sum(char_widths) / len(char_widths) if char_widths else 5.0

        # Find any gap > 5x average char width AND > 40pt — that's a column gutter
        # (Not just any large gap — must be truly massive like a column separator)
        # Real column gutters are typically 30-60pt. Table columns are ~10-25pt.
        gutter_threshold = max(avg_cw * 5.0, 40.0)
        split_points = [i for gap, i in gaps if gap > gutter_threshold]

        if not split_points:
            result.append(line_glyphs)
        else:
            # Split the line at gutter points
            prev = 0
            for sp in split_points:
                segment = sorted_g[prev:sp]
                if segment:
                    result.append(segment)
                prev = sp
            remainder = sorted_g[prev:]
            if remainder:
                result.append(remainder)

    return result


# ---------------------------------------------------------------------------
# Step 2.3 — TextLine → TextBlock Assembly
# ---------------------------------------------------------------------------

def assemble_blocks(lines: list[TextLine]) -> list[TextBlock]:
    """Group consecutive lines into TextBlocks based on vertical spacing.

    Lines that are closely spaced (normal line spacing) belong to the same
    block. A gap significantly larger than normal indicates a new block
    (new paragraph, new section, etc.).

    The threshold adapts to the dominant font size in each line pair.

    Args:
        lines: TextLines sorted top-to-bottom.

    Returns:
        List of TextBlock objects.
    """
    if not lines:
        return []

    blocks: list[TextBlock] = []
    current_block_lines: list[TextLine] = [lines[0]]

    for i in range(1, len(lines)):
        prev_line = lines[i - 1]
        curr_line = lines[i]

        # Calculate vertical gap between lines
        gap = curr_line.bbox.y0 - prev_line.bbox.y1

        # Normal line spacing is approximately font_size * 0.2 to font_size * 0.5
        # A gap larger than font_size * 0.8 suggests a new block
        avg_font_size = (prev_line.dominant_font_size + curr_line.dominant_font_size) / 2
        block_gap_threshold = avg_font_size * 0.8

        # Also check for significant left-indent change (new block)
        indent_change = abs(curr_line.bbox.x0 - prev_line.bbox.x0)
        has_indent_change = indent_change > avg_font_size * 2.0

        # Also check for font size change (e.g., heading after paragraph)
        size_ratio = curr_line.dominant_font_size / prev_line.dominant_font_size if prev_line.dominant_font_size > 0 else 1.0
        has_size_change = size_ratio > 1.3 or size_ratio < 0.75

        if gap > block_gap_threshold or has_indent_change or has_size_change:
            # Start a new block
            block_bbox = merge_bboxes([l.bbox for l in current_block_lines])
            blocks.append(TextBlock(lines=current_block_lines, bbox=block_bbox))
            current_block_lines = [curr_line]
        else:
            current_block_lines.append(curr_line)

    # Final block
    if current_block_lines:
        block_bbox = merge_bboxes([l.bbox for l in current_block_lines])
        blocks.append(TextBlock(lines=current_block_lines, bbox=block_bbox))

    return blocks


# ---------------------------------------------------------------------------
# Step 2.4 — Dehyphenation
# ---------------------------------------------------------------------------

# Common English words for simple dictionary check
# In production, we'd use a proper dictionary (enchant, nltk wordnet, etc.)
# For now, we use a heuristic: if joined word doesn't contain weird chars, accept it
_COMPOUND_WORD_PREFIXES = {
    "well", "self", "non", "pre", "post", "anti", "co", "re", "ex",
    "all", "cross", "half", "high", "low", "mid", "multi", "over",
    "pan", "semi", "sub", "super", "trans", "ultra", "un", "under",
}


def dehyphenate(blocks: list[TextBlock]) -> list[TextBlock]:
    """Rejoin words that were hyphenated at line breaks.

    Rules:
      - If a line ends with '-' and the next line starts with a lowercase letter,
        attempt to join the word fragments.
      - If the hyphenated form looks like a compound word (well-known, self-aware),
        keep the hyphen.
      - Otherwise, remove the hyphen and join.

    This modifies the spans in-place within the blocks.
    """
    for block in blocks:
        if len(block.lines) < 2:
            continue

        for i in range(len(block.lines) - 1):
            curr_line = block.lines[i]
            next_line = block.lines[i + 1]

            if not curr_line.spans or not next_line.spans:
                continue

            last_span = curr_line.spans[-1]
            first_span = next_line.spans[0]

            last_text = last_span.text.rstrip()
            first_text = first_span.text.lstrip()

            if not last_text.endswith("-") or not first_text:
                continue

            # Check if next line starts with lowercase (suggests hyphenation, not real hyphen)
            if not first_text[0].islower():
                continue

            # Extract the word parts
            word_before = last_text[:-1]  # Remove trailing hyphen
            # Get just the first word of next line
            first_word = first_text.split()[0] if first_text.split() else first_text

            # Check for compound words — keep the hyphen
            word_before_lower = word_before.lower().split()[-1] if word_before.split() else ""
            if word_before_lower in _COMPOUND_WORD_PREFIXES:
                continue  # Keep the hyphen (likely "well-known", "self-aware", etc.)

            # Join the word: remove hyphen from end of current line
            last_span.text = last_text[:-1]

    return blocks


# ---------------------------------------------------------------------------
# Step 2.5 — Font Catalog Build
# ---------------------------------------------------------------------------

def build_font_catalog(blocks: list[TextBlock]) -> FontCatalog:
    """Build a catalog of all fonts used, identifying the dominant body font.

    The body font is the most-used (font_name, font_size, bold, italic) combination
    by character count. All other fonts are classified relative to it:
      - Larger + bold → heading candidate
      - Same size + bold → emphasis
      - Monospace → code

    Args:
        blocks: TextBlocks from assembly.

    Returns:
        FontCatalog with all fonts and the identified body font.
    """
    # Count characters per font style
    font_counts: dict[tuple, int] = defaultdict(int)

    for block in blocks:
        for line in block.lines:
            for span in line.spans:
                text_len = len(span.text.replace(" ", ""))  # Don't count spaces
                if text_len == 0:
                    continue
                key = (
                    span.font_name,
                    round(span.font_size, 1),
                    span.is_bold,
                    span.is_italic,
                    span.is_monospace,
                )
                font_counts[key] += text_len

    # Build FontInfo list
    fonts: list[FontInfo] = []
    for (name, size, bold, italic, mono), count in font_counts.items():
        fonts.append(FontInfo(
            name=name,
            size=size,
            is_bold=bold,
            is_italic=italic,
            is_monospace=mono,
            char_count=count,
        ))

    catalog = FontCatalog(fonts=fonts)
    catalog.identify_body_font()

    if catalog.body_font:
        logger.info(
            f"Body font: {catalog.body_font.name} @ {catalog.body_font.size}pt "
            f"({catalog.body_font.char_count} chars), "
            f"total fonts: {len(fonts)}"
        )

    return catalog


# ---------------------------------------------------------------------------
# Full Assembly Pipeline
# ---------------------------------------------------------------------------

def assemble(glyphs: list[RawGlyph]) -> tuple[list[TextBlock], FontCatalog]:
    """Run the complete Layer 2 assembly pipeline.

    Pipeline: Glyphs → Lines → Blocks → Dehyphenate → Font Catalog

    Args:
        glyphs: Raw glyphs from Layer 1 extraction.

    Returns:
        Tuple of (assembled TextBlocks, FontCatalog).
    """
    # Step 2.1 + 2.2: Glyphs → Lines (with word boundary detection)
    lines = assemble_lines(glyphs)
    logger.info(f"Assembled {len(lines)} lines from {len(glyphs)} glyphs")

    # Step 2.3: Lines → Blocks
    blocks = assemble_blocks(lines)
    logger.info(f"Grouped into {len(blocks)} blocks")

    # Step 2.4: Dehyphenation
    blocks = dehyphenate(blocks)

    # Step 2.5: Font catalog
    catalog = build_font_catalog(blocks)

    return blocks, catalog
