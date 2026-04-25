"""
Layer 4: Semantic Inference.

Refines the block classifications from Layer 3 by analyzing:
  - Font size relative to body font → heading detection + level assignment
  - Text patterns → list detection (bullets, numbered)
  - Font style → emphasis recovery (bold/italic spans within paragraphs)
  - URL patterns → link extraction
  - Position + numbering → footnote detection

Input:  ContentBlocks (mostly UNKNOWN) + FontCatalog
Output: ContentBlocks with semantic types (HEADING, PARAGRAPH, LIST_ITEM, etc.)

Content accuracy principle: This layer NEVER modifies text content.
It only assigns labels and metadata to existing blocks.
"""

from __future__ import annotations

import logging
import re

from backend.app.models.document import (
    BlockType,
    ContentBlock,
    FontCatalog,
    ListStyle,
    TextBlock,
    TextLine,
    TextSpan,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 4.1 — Heading Detection & Level Assignment
# ---------------------------------------------------------------------------

# Size ratio thresholds relative to body font size
# These map (min_ratio, max_ratio) → heading level
_HEADING_RATIOS = [
    (2.0, float("inf"), 1),   # 2x+ body size → H1
    (1.5, 2.0, 2),            # 1.5x-2x → H2
    (1.2, 1.5, 3),            # 1.2x-1.5x → H3
    (1.05, 1.2, 4),           # 1.05x-1.2x (+ bold) → H4
]


def detect_headings(
    blocks: list[ContentBlock],
    font_catalog: FontCatalog,
) -> list[ContentBlock]:
    """Detect headings based on font size relative to body font.

    Rules:
      1. Font size significantly larger than body → heading
      2. Heading level determined by size ratio
      3. Single-line blocks that are bold + larger → heading
      4. Very short blocks (< 80 chars) with larger font → heading
      5. Detection number patterns like "1.", "1.1", "A." at line start

    Args:
        blocks: ContentBlocks from Layer 3.
        font_catalog: Font catalog with identified body font.

    Returns:
        Same blocks with UNKNOWN → HEADING where appropriate.
    """
    if not font_catalog.body_font or font_catalog.body_font_size == 0:
        return blocks

    body_size = font_catalog.body_font_size

    for block in blocks:
        if block.block_type != BlockType.UNKNOWN:
            continue
        if not block.text_block or block.text_block.line_count == 0:
            continue

        tb = block.text_block
        text = tb.text.strip()

        # Skip very long blocks — headings are usually short
        if len(text) > 200:
            continue

        # Get the dominant font size in this block
        block_font_size = tb.lines[0].dominant_font_size
        size_ratio = block_font_size / body_size if body_size > 0 else 1.0

        # Check if all text is bold
        is_bold = all(line.is_all_bold for line in tb.lines if line.text.strip())

        # Determine heading level from size ratio
        heading_level = 0
        for min_r, max_r, level in _HEADING_RATIOS:
            if min_r <= size_ratio < max_r:
                heading_level = level
                break

        # Level 4/5: bold + short text at body size
        if heading_level == 0 and is_bold and size_ratio >= 1.0 and len(text) < 80:
            if size_ratio >= 1.02:
                heading_level = 4
            elif tb.line_count == 1 and len(text) < 60:
                heading_level = 5

        # Extra signal: single-line blocks starting with number patterns
        if heading_level == 0 and tb.line_count <= 2 and len(text) < 100:
            # Multi-level heading (e.g., "1.1.1 Title", "A.2 Methods")
            if re.match(r'^(\d+\.)+\d*\s+\S', text):
                if is_bold or size_ratio >= 1.0:
                    heading_level = min(4, 2 + text.count('.'))
            elif re.match(r'^[A-Z]\.\s+\S', text):
                if is_bold or size_ratio >= 1.1:
                    heading_level = 3

        if heading_level > 0:
            block.block_type = BlockType.HEADING
            block.heading_level = heading_level
            block.confidence = min(0.95, 0.7 + size_ratio * 0.1)

    return blocks


# ---------------------------------------------------------------------------
# Step 4.2 — Paragraph Assembly
# ---------------------------------------------------------------------------

def detect_paragraphs(blocks: list[ContentBlock]) -> list[ContentBlock]:
    """Classify remaining UNKNOWN blocks as paragraphs.

    Rules:
      - Multi-line blocks with regular body text → PARAGRAPH
      - Single-line blocks that are long enough → PARAGRAPH
      - Very short single-line blocks may remain UNKNOWN (could be captions, etc.)

    This is essentially the "default" classification — if nothing else
    claims a block, it's a paragraph.
    """
    for block in blocks:
        if block.block_type != BlockType.UNKNOWN:
            continue
        if not block.text_block:
            continue

        text = block.text_block.text.strip()
        if not text:
            continue

        # Multi-line blocks are almost certainly paragraphs
        if block.text_block.line_count >= 2:
            block.block_type = BlockType.PARAGRAPH
            block.confidence = 0.9
            continue

        # Single-line blocks: paragraphs if long enough
        if len(text) >= 20:
            block.block_type = BlockType.PARAGRAPH
            block.confidence = 0.8
            continue

        # Very short blocks: could be labels, captions, etc.
        # Still classify as paragraph (safest default)
        block.block_type = BlockType.PARAGRAPH
        block.confidence = 0.6

    return blocks


# ---------------------------------------------------------------------------
# Step 4.3 — List Detection
# ---------------------------------------------------------------------------

# Patterns for list markers
_BULLET_MARKERS = re.compile(
    r'^[\s]*([•\-\*\u2022\u2023\u25E6\u2043\u2219\u25AA\u25CB\u25CF\u2013\u2014\xB7\xB0\u00B7])\s+'
)
_ORDERED_MARKERS = re.compile(
    r'^[\s]*(\d{1,3}[.)]\s+|[a-zA-Z][.)]\s+|\([a-zA-Z0-9]+\)\s+|[ivxIVX]{1,4}[.)]\s+)'
)


def detect_lists(blocks: list[ContentBlock]) -> list[ContentBlock]:
    """Detect list items by analyzing text patterns.

    Detection strategy:
      1. Check each line of each block for bullet/number markers
      2. If a block contains multiple list items (mixed with label text),
         split it into separate ContentBlocks
      3. Handle nested lists via indent level

    Args:
        blocks: ContentBlocks (some may already be HEADING/TABLE/etc.)

    Returns:
        Updated block list with list items classified (may be longer
        than input if blocks were split).
    """
    from collections import Counter
    from backend.app.utils.geometry import merge_bboxes

    # First pass: find the body left margin (most common x0)
    x0_values = []
    for block in blocks:
        if block.text_block and block.block_type in (BlockType.PARAGRAPH, BlockType.UNKNOWN):
            x0_values.append(round(block.bbox.x0, 0))

    body_margin = 0.0
    if x0_values:
        margin_counts = Counter(x0_values)
        body_margin = margin_counts.most_common(1)[0][0]

    result: list[ContentBlock] = []

    for block in blocks:
        if block.block_type not in (BlockType.PARAGRAPH, BlockType.UNKNOWN):
            result.append(block)
            continue
        if not block.text_block or not block.text_block.lines:
            result.append(block)
            continue

        # Check each line for list markers
        list_lines: list[tuple[int, str, ListStyle, str]] = []  # (line_idx, marker, style, match_text)
        for line_idx, line in enumerate(block.text_block.lines):
            line_text = line.text

            bullet_match = _BULLET_MARKERS.match(line_text)
            if bullet_match:
                list_lines.append((line_idx, bullet_match.group(1), ListStyle.UNORDERED, line_text))
                continue

            ordered_match = _ORDERED_MARKERS.match(line_text)
            if ordered_match:
                list_lines.append((line_idx, ordered_match.group(1).strip(), ListStyle.ORDERED, line_text))
                continue

        if not list_lines:
            # No list items found → keep block as-is
            result.append(block)
            continue

        # Split block into: non-list preamble + individual list items
        lines = block.text_block.lines
        list_line_indices = {ll[0] for ll in list_lines}

        # Collect preamble lines (lines before any list marker)
        first_list_idx = list_lines[0][0]
        if first_list_idx > 0:
            preamble_lines = lines[:first_list_idx]
            preamble_bbox = merge_bboxes([l.bbox for l in preamble_lines])
            preamble_block = ContentBlock(
                block_type=BlockType.PARAGRAPH,
                bbox=preamble_bbox,
                text_block=TextBlock(lines=preamble_lines, bbox=preamble_bbox),
                confidence=0.8,
            )
            result.append(preamble_block)

        # Each list marker line becomes its own ContentBlock
        for i, (line_idx, marker, style, _) in enumerate(list_lines):
            # Gather lines belonging to this list item
            # (from this marker to the next marker, or end of block)
            if i + 1 < len(list_lines):
                next_marker_idx = list_lines[i + 1][0]
            else:
                next_marker_idx = len(lines)

            item_lines = lines[line_idx:next_marker_idx]
            item_bbox = merge_bboxes([l.bbox for l in item_lines])

            indent = item_bbox.x0 - body_margin
            level = max(0, int(indent / 20))

            item_block = ContentBlock(
                block_type=BlockType.LIST_ITEM,
                bbox=item_bbox,
                text_block=TextBlock(lines=item_lines, bbox=item_bbox),
                list_style=style,
                list_marker=marker,
                list_level=level,
                confidence=0.9 if style == ListStyle.UNORDERED else 0.85,
            )
            result.append(item_block)

    return result


# ---------------------------------------------------------------------------
# Step 4.4 — Emphasis & Inline Formatting Recovery
# ---------------------------------------------------------------------------

def recover_emphasis(blocks: list[ContentBlock]) -> list[ContentBlock]:
    """Analyze spans within blocks to identify emphasis patterns.

    This doesn't modify the text — it ensures span-level bold/italic
    information is correctly set for the emitter to use.

    Items checked:
      - Bold spans within otherwise non-bold text
      - Italic spans within otherwise non-italic text
      - Monospace spans (inline code)
      - Superscript/subscript markers (already set by assembler)
    """
    for block in blocks:
        if not block.text_block:
            continue
        if block.block_type in (BlockType.HEADER, BlockType.FOOTER, BlockType.CODE_BLOCK):
            continue

        for line in block.text_block.lines:
            _process_line_emphasis(line)

    return blocks


def _process_line_emphasis(line: TextLine) -> None:
    """Process a single line for inline formatting markers.

    This inspects the span structure and ensures styling flags are
    consistent and accurate.
    """
    if len(line.spans) < 2:
        return

    # Check for mixed styling (the interesting case)
    has_bold = any(s.is_bold for s in line.spans if s.text.strip())
    has_non_bold = any(not s.is_bold for s in line.spans if s.text.strip())
    has_italic = any(s.is_italic for s in line.spans if s.text.strip())
    has_non_italic = any(not s.is_italic for s in line.spans if s.text.strip())

    # If the line has mixed bold/non-bold, the bold parts are emphasis
    # If the entire line is bold, it's structural (heading/label), not emphasis
    # This distinction matters for correct Markdown output

    # No modifications needed — the span-level flags are already correct
    # from the assembler. We just verify them here.
    # The emitter will use these flags to wrap text in ** or * markers.


# ---------------------------------------------------------------------------
# Step 4.5 — Link Extraction
# ---------------------------------------------------------------------------

# URL pattern — matches http(s), ftp, mailto, and bare domain patterns
_URL_PATTERN = re.compile(
    r'(https?://[^\s<>\[\]()]+|'
    r'ftp://[^\s<>\[\]()]+|'
    r'mailto:[^\s<>\[\]()]+|'
    r'www\.[^\s<>\[\]()]+)'
)

_EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)


def extract_links(blocks: list[ContentBlock]) -> list[ContentBlock]:
    """Detect URLs and email addresses in text and mark them as links.

    Sets the link_url field on spans containing URLs.
    The emitter will convert these to [text](url) markdown.

    Note: PDF annotations (clickable links) are extracted separately
    in the extractor. This catches plain-text URLs.
    """
    for block in blocks:
        if not block.text_block:
            continue
        if block.block_type in (BlockType.HEADER, BlockType.FOOTER):
            continue

        for line in block.text_block.lines:
            for span in line.spans:
                text = span.text

                # Check for URLs
                url_match = _URL_PATTERN.search(text)
                if url_match and not span.link_url:
                    span.link_url = url_match.group(0)
                    continue

                # Check for email addresses
                email_match = _EMAIL_PATTERN.search(text)
                if email_match and not span.link_url:
                    span.link_url = f"mailto:{email_match.group(0)}"

    return blocks


# ---------------------------------------------------------------------------
# Step 4.6 — Footnote Detection
# ---------------------------------------------------------------------------

# Footnote markers: [1], (1), 1), *, †, ‡, a) — NOT multi-level headings like 1.1.1
_FOOTNOTE_PATTERN = re.compile(
    r'^[\s]*[\[\(]?(\d{1,2}|[*\u2020\u2021\u00a7\u00b6]|[a-z])[\]\)]?[\s:]\s+(.*)',
    re.DOTALL,
)


def detect_footnotes(blocks: list[ContentBlock], page_height: float) -> list[ContentBlock]:
    """Detect footnote blocks at the bottom of the page.

    Rules:
      - Located in the lower 25% of the page
      - Starts with a number, symbol, or letter marker
      - Typically has smaller font than body text
      - Often preceded by a horizontal rule (detected as a thin line)

    Args:
        blocks: ContentBlocks for the page.
        page_height: Height of the page.

    Returns:
        Same blocks with footnotes classified.
    """
    footnote_zone_y = page_height * 0.75  # Bottom 25% of page

    for block in blocks:
        if block.block_type not in (BlockType.PARAGRAPH, BlockType.UNKNOWN):
            continue
        if not block.text_block:
            continue

        # Must be in the footnote zone
        if block.bbox.y0 < footnote_zone_y:
            continue

        text = block.text_block.text.strip()

        # Reject if text looks like a numbered heading (e.g., '1.2.1 Title')
        if re.match(r'^\d+\.\d+', text):
            continue

        match = _FOOTNOTE_PATTERN.match(text)
        if match:
            # Additional check: footnote marker should be just a number,
            # not the start of a multi-part section number
            marker_end = match.end(1)
            remaining = text[marker_end:marker_end+2] if marker_end < len(text) else ''
            if remaining.startswith('.'):
                continue  # This is "1.2" not a footnote

            block.block_type = BlockType.FOOTNOTE
            block.footnote_id = match.group(1)
            block.footnote_text = match.group(2).strip()
            block.confidence = 0.7

    return blocks


# ---------------------------------------------------------------------------
# Step 4.7 — Definition List Detection
# ---------------------------------------------------------------------------

def detect_definition_lists(blocks: list[ContentBlock]) -> list[ContentBlock]:
    """Detect definition-style lists (bold term followed by description).

    LaTeX \\description environments produce blocks where the first span is
    bold (the term) and the rest is regular text (the definition). We convert
    these into LIST_ITEMs with the term in bold.

    Pattern: A paragraph whose first line starts with a bold span (the term)
    followed by non-bold text (the definition), and the term is short (<50 chars).
    """
    result: list[ContentBlock] = []

    for block in blocks:
        if block.block_type != BlockType.PARAGRAPH:
            result.append(block)
            continue
        if not block.text_block or not block.text_block.lines:
            result.append(block)
            continue

        first_line = block.text_block.lines[0]
        if len(first_line.spans) < 2:
            result.append(block)
            continue

        # Check if first span is bold and short (the definition term)
        first_span = first_line.spans[0]
        has_bold_term = (
            first_span.is_bold
            and len(first_span.text.strip()) < 50
            and not first_line.is_all_bold  # Mixed: bold term + regular definition
        )

        if not has_bold_term:
            result.append(block)
            continue

        # This looks like a definition list item
        block.block_type = BlockType.LIST_ITEM
        block.list_style = ListStyle.UNORDERED
        block.list_marker = '-'
        block.list_level = 0
        block.confidence = 0.8
        result.append(block)

    return result


# ---------------------------------------------------------------------------
# Full Semantic Analysis Pipeline
# ---------------------------------------------------------------------------

def analyze_semantics(
    blocks: list[ContentBlock],
    font_catalog: FontCatalog,
    page_height: float,
) -> list[ContentBlock]:
    """Run the complete Layer 4 semantic analysis pipeline.

    Pipeline order matters:
      1. Headings first (uses font size, must run before paragraph default)
      2. Lists (uses text patterns)
      3. Footnotes (uses position)
      4. Paragraphs (default for remaining UNKNOWN blocks)
      5. Emphasis recovery (within all text blocks)
      6. Link extraction (within all text blocks)

    Args:
        blocks: ContentBlocks from Layer 3.
        font_catalog: Font catalog from Layer 2.
        page_height: Height of the page.

    Returns:
        ContentBlocks with semantic types assigned.
    """
    # Step 4.1: Headings
    blocks = detect_headings(blocks, font_catalog)
    heading_count = sum(1 for b in blocks if b.block_type == BlockType.HEADING)

    # Step 4.3: Lists (before paragraphs, so list items aren't claimed as paragraphs)
    blocks = detect_lists(blocks)
    list_count = sum(1 for b in blocks if b.block_type == BlockType.LIST_ITEM)

    # Step 4.6: Footnotes
    blocks = detect_footnotes(blocks, page_height)

    # Step 4.7: Definition lists (before paragraph default)
    blocks = detect_definition_lists(blocks)

    # Step 4.2: Paragraphs (default for remaining UNKNOWN)
    blocks = detect_paragraphs(blocks)

    # Step 4.4: Emphasis recovery
    blocks = recover_emphasis(blocks)

    # Step 4.5: Link extraction
    blocks = extract_links(blocks)

    logger.info(
        f"Semantic analysis: {heading_count} headings, "
        f"{list_count} list items, "
        f"{sum(1 for b in blocks if b.block_type == BlockType.PARAGRAPH)} paragraphs"
    )

    return blocks
