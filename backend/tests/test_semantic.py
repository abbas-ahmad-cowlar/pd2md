"""
Tests for Layer 4: Semantic Inference.

Verifies:
  - Heading detection and level assignment
  - Paragraph classification
  - List detection (bullet and numbered)
  - Emphasis recovery (bold/italic spans)
  - Link extraction
  - Full pipeline integration from extraction → semantics
  - Content accuracy preservation through all layers
"""

import sys
from pathlib import Path

import pytest
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.pipeline.extractor import extract_page_glyphs, extract_page_vectors, extract_page_images
from backend.app.pipeline.assembler import assemble
from backend.app.pipeline.layout_analyzer import (
    HeaderFooterMask,
    analyze_layout,
    detect_headers_footers,
)
from backend.app.pipeline.semantic_analyzer import (
    analyze_semantics,
    detect_headings,
    detect_lists,
    detect_paragraphs,
    extract_links,
    recover_emphasis,
)
from backend.app.models.document import BlockType, ListStyle

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent / "test_output"


def _full_pipeline(filename: str, page_num: int = 0):
    """Run extraction → assembly → layout → return blocks + catalog."""
    doc = fitz.open(str(FIXTURES / filename))
    page = doc.load_page(page_num)
    glyphs = extract_page_glyphs(page)
    vectors = extract_page_vectors(page)
    images = extract_page_images(page, doc, OUTPUT / "semantic_test", page_num)
    width = page.rect.width
    height = page.rect.height
    doc.close()

    blocks, catalog = assemble(glyphs)
    mask = HeaderFooterMask()
    content_blocks = analyze_layout(blocks, vectors, images, width, height, mask)

    return content_blocks, catalog, height


class TestHeadingDetection:
    """Step 4.1 — Heading Detection & Level Assignment."""

    def test_headings_detected(self):
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = detect_headings(blocks, catalog)

        headings = [b for b in blocks if b.block_type == BlockType.HEADING]
        assert len(headings) >= 1, "Should detect at least one heading"

    def test_heading_levels_assigned(self):
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = detect_headings(blocks, catalog)

        headings = [b for b in blocks if b.block_type == BlockType.HEADING]
        for h in headings:
            assert 1 <= h.heading_level <= 6, f"Heading level should be 1-6, got {h.heading_level}"

    def test_title_is_highest_level(self):
        """Document title should get the lowest heading number (highest priority)."""
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = detect_headings(blocks, catalog)

        headings = [b for b in blocks if b.block_type == BlockType.HEADING]
        if len(headings) >= 2:
            # Title "Document Title" should have a lower level number than section headings
            title_heading = None
            for h in headings:
                if "Document Title" in h.text:
                    title_heading = h
                    break

            if title_heading:
                other_headings = [h for h in headings if h != title_heading]
                for oh in other_headings:
                    assert title_heading.heading_level <= oh.heading_level, (
                        f"Title (level {title_heading.heading_level}) should be ≤ "
                        f"section heading '{oh.text[:30]}' (level {oh.heading_level})"
                    )

    def test_body_text_not_heading(self):
        """Regular body text should NOT be headings."""
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = detect_headings(blocks, catalog)

        for block in blocks:
            if "first paragraph" in block.text.lower():
                assert block.block_type != BlockType.HEADING, (
                    "Body paragraph should not be classified as heading"
                )


class TestParagraphDetection:
    """Step 4.2 — Paragraph Assembly."""

    def test_paragraphs_detected(self):
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = detect_headings(blocks, catalog)
        blocks = detect_paragraphs(blocks)

        paragraphs = [b for b in blocks if b.block_type == BlockType.PARAGRAPH]
        assert len(paragraphs) >= 2, "Should detect multiple paragraphs"

    def test_no_unknown_blocks_remain(self):
        """After paragraph detection, no UNKNOWN blocks should remain."""
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        unknown = [b for b in blocks
                   if b.block_type == BlockType.UNKNOWN
                   and b.text_block and b.text_block.text.strip()]
        assert len(unknown) == 0, (
            f"Should have no UNKNOWN blocks after full analysis, "
            f"got: {[b.text[:30] for b in unknown]}"
        )


class TestListDetection:
    """Step 4.3 — List Detection."""

    def test_bullets_detected(self):
        blocks, catalog, height = _full_pipeline("with_lists.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        list_items = [b for b in blocks if b.block_type == BlockType.LIST_ITEM]
        assert len(list_items) >= 1, "Should detect list items"

    def test_unordered_list_style(self):
        blocks, catalog, height = _full_pipeline("with_lists.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        unordered = [b for b in blocks
                     if b.block_type == BlockType.LIST_ITEM
                     and b.list_style == ListStyle.UNORDERED]
        assert len(unordered) >= 1, "Should detect unordered list items"

    def test_ordered_list_style(self):
        blocks, catalog, height = _full_pipeline("with_lists.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        ordered = [b for b in blocks
                   if b.block_type == BlockType.LIST_ITEM
                   and b.list_style == ListStyle.ORDERED]
        assert len(ordered) >= 1, "Should detect ordered list items"

    def test_list_content_preserved(self):
        """List item text content must be preserved."""
        blocks, catalog, height = _full_pipeline("with_lists.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        all_text = " ".join(b.text for b in blocks if b.text_block)
        assert "First item" in all_text
        assert "Alpha step" in all_text


class TestEmphasisRecovery:
    """Step 4.4 — Emphasis & Inline Formatting Recovery."""

    def test_bold_spans_present(self):
        blocks, catalog, height = _full_pipeline("formatted_text.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        bold_spans = []
        for block in blocks:
            if block.text_block:
                for line in block.text_block.lines:
                    for span in line.spans:
                        if span.is_bold and span.text.strip():
                            bold_spans.append(span)

        assert len(bold_spans) > 0, "Should have bold spans in formatted text"

    def test_italic_spans_present(self):
        blocks, catalog, height = _full_pipeline("formatted_text.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        italic_spans = []
        for block in blocks:
            if block.text_block:
                for line in block.text_block.lines:
                    for span in line.spans:
                        if span.is_italic and span.text.strip():
                            italic_spans.append(span)

        assert len(italic_spans) > 0, "Should have italic spans in formatted text"


class TestLinkExtraction:
    """Step 4.5 — Link Extraction."""

    def test_no_false_links(self):
        """Simple text without URLs should have no links."""
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = extract_links(blocks)

        linked_spans = []
        for block in blocks:
            if block.text_block:
                for line in block.text_block.lines:
                    for span in line.spans:
                        if span.link_url:
                            linked_spans.append(span)

        assert len(linked_spans) == 0, "Simple text should have no URLs"


class TestFullSemanticPipeline:
    """End-to-end semantic analysis."""

    def test_simple_text_semantics(self):
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        # Should have headings and paragraphs
        types = {b.block_type for b in blocks if b.text_block and b.text_block.text.strip()}
        assert BlockType.HEADING in types, "Should detect headings"
        assert BlockType.PARAGRAPH in types, "Should detect paragraphs"

    def test_content_accuracy_through_all_layers(self):
        """Critical: content must survive four layers of processing."""
        blocks, catalog, height = _full_pipeline("simple_text.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        all_text = " ".join(b.text for b in blocks if b.text_block)

        required = [
            "Document Title", "John Doe", "Introduction",
            "first paragraph", "3.14159", "&",
            "Background", "Methods",
        ]
        for s in required:
            assert s in all_text, (
                f"Required text '{s}' lost after semantic analysis"
            )

    def test_table_pdf_semantics(self):
        blocks, catalog, height = _full_pipeline("bordered_table.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        all_text = " ".join(b.text for b in blocks if b.text_block)
        assert "Alice" in all_text
        assert "Table Example" in all_text

    def test_formatted_text_semantics(self):
        blocks, catalog, height = _full_pipeline("formatted_text.pdf")
        blocks = analyze_semantics(blocks, catalog, height)

        types = {b.block_type for b in blocks}
        # Should have at least heading + other content
        assert len(types) >= 2

    def test_multipage_semantics(self):
        """Each page of multipage doc should get semantics."""
        doc = fitz.open(str(FIXTURES / "multipage.pdf"))
        all_blocks = []
        page_dims = []

        for i in range(doc.page_count):
            page = doc.load_page(i)
            glyphs = extract_page_glyphs(page)
            vectors = extract_page_vectors(page)
            images = extract_page_images(page, doc, OUTPUT / "semantic_mp", i)
            blocks, catalog = assemble(glyphs)
            all_blocks.append(blocks)
            page_dims.append((page.rect.width, page.rect.height))
        doc.close()

        mask = detect_headers_footers(all_blocks, [h for _, h in page_dims])

        for i, (blocks, dims) in enumerate(zip(all_blocks, page_dims)):
            width, height = dims
            content = analyze_layout(blocks, [], [], width, height, mask)
            content = analyze_semantics(content, catalog, height)

            # Every page should have at least one classified content block
            classified = [b for b in content
                          if b.block_type not in (BlockType.HEADER, BlockType.FOOTER, BlockType.UNKNOWN)]
            assert len(classified) > 0, f"Page {i} should have classified content"
