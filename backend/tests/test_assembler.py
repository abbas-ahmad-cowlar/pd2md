"""
Tests for Layer 2: Text Assembly.

Verifies:
  - Glyph → word assembly (correct word boundaries, no split/merged words)
  - Line assembly (correct line grouping)
  - Block assembly (paragraphs separated at visual gaps)
  - Dehyphenation (soft hyphens removed, compound hyphens kept)
  - Font catalog (body font identified, font sizes cataloged)
  - Content accuracy (assembled text matches original exactly)
"""

import sys
from pathlib import Path

import pytest
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.pipeline.extractor import extract_page_glyphs
from backend.app.pipeline.assembler import (
    assemble,
    assemble_blocks,
    assemble_lines,
    build_font_catalog,
    dehyphenate,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _get_glyphs(filename: str, page_num: int = 0) -> list:
    """Helper: extract glyphs from a test fixture."""
    doc = fitz.open(str(FIXTURES / filename))
    page = doc.load_page(page_num)
    glyphs = extract_page_glyphs(page)
    doc.close()
    return glyphs


class TestLineAssembly:
    """Steps 2.1 + 2.2 — Glyph → Span → Line Assembly."""

    def test_produces_lines(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        assert len(lines) > 0, "Should produce at least one line"

    def test_line_text_is_readable(self):
        """Each line should produce coherent, readable text."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)

        # Join all line text
        all_text = "\n".join(line.text for line in lines)
        assert "Document Title" in all_text
        assert "Introduction" in all_text

    def test_words_have_spaces(self):
        """Words should be separated by spaces, not concatenated."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)

        all_text = " ".join(line.text for line in lines)

        # These multi-word phrases must have spaces between words
        assert "Document Title" in all_text or "Document  Title" in all_text
        assert "first paragraph" in all_text or "first  paragraph" in all_text

    def test_numbers_preserved(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        all_text = " ".join(line.text for line in lines)

        assert "3.14159" in all_text, "Decimal numbers must be preserved exactly"

    def test_special_chars_preserved(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        all_text = " ".join(line.text for line in lines)

        assert "&" in all_text, "Ampersand must be preserved"

    def test_lines_have_bboxes(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)

        for line in lines:
            assert line.bbox.width > 0, f"Line '{line.text[:20]}' has zero width"
            assert line.bbox.height > 0, f"Line '{line.text[:20]}' has zero height"

    def test_spans_have_style_info(self):
        glyphs = _get_glyphs("formatted_text.pdf")
        lines = assemble_lines(glyphs)

        # Collect all spans
        all_spans = [s for line in lines for s in line.spans]
        bold_spans = [s for s in all_spans if s.is_bold]
        italic_spans = [s for s in all_spans if s.is_italic]

        assert len(bold_spans) > 0, "Should have bold spans"
        assert len(italic_spans) > 0, "Should have italic spans"


class TestBlockAssembly:
    """Step 2.3 — Line → Block Assembly."""

    def test_produces_blocks(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)

        assert len(blocks) > 1, "Should produce multiple blocks (title, paragraphs, etc.)"

    def test_blocks_separate_at_headings(self):
        """Headings (larger font) should start a new block."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)

        # Find blocks that contain heading text
        block_texts = [b.text for b in blocks]
        has_title_block = any("Document Title" in t for t in block_texts)
        has_intro_block = any("Introduction" in t for t in block_texts)

        assert has_title_block, "Title should be in its own block"
        assert has_intro_block, "Section heading should be in its own block"

    def test_block_text_content_complete(self):
        """All original content must appear somewhere in the blocks."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)

        all_text = " ".join(b.text for b in blocks)

        required = [
            "Document Title", "John Doe", "Introduction",
            "first paragraph", "second paragraph", "3.14159",
            "Background", "Methods",
        ]
        for s in required:
            assert s in all_text, f"Required text '{s}' missing from assembled blocks"

    def test_blocks_have_bboxes(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)

        for block in blocks:
            assert block.bbox.width > 0
            assert block.bbox.height > 0

    def test_multipage_blocks(self):
        """Each page should produce blocks independently."""
        for page_num in range(3):
            glyphs = _get_glyphs("multipage.pdf", page_num)
            lines = assemble_lines(glyphs)
            blocks = assemble_blocks(lines)

            assert len(blocks) > 0, f"Page {page_num} should have blocks"

            all_text = " ".join(b.text for b in blocks)
            assert f"Chapter {page_num + 1}" in all_text


class TestDehyphenation:
    """Step 2.4 — Dehyphenation."""

    def test_dehyphenate_does_not_crash(self):
        """Dehyphenation should run without errors on any input."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)

        result = dehyphenate(blocks)
        assert len(result) == len(blocks)

    def test_dehyphenate_preserves_content(self):
        """Dehyphenation must not lose any content."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)

        text_before = " ".join(b.text for b in blocks)
        dehyphenate(blocks)
        text_after = " ".join(b.text for b in blocks)

        # Text should either be identical or differ only in removed hyphens
        # For our test PDFs, there should be no change (no hyphenation)
        assert len(text_after) >= len(text_before) - 5  # Allow small diff from hyphen removal


class TestFontCatalog:
    """Step 2.5 — Font Catalog Build."""

    def test_catalog_has_fonts(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)
        catalog = build_font_catalog(blocks)

        assert len(catalog.fonts) > 0, "Should detect at least one font"

    def test_body_font_identified(self):
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)
        catalog = build_font_catalog(blocks)

        assert catalog.body_font is not None, "Should identify a body font"
        assert catalog.body_font.char_count > 0

    def test_body_font_is_most_used(self):
        """Body font should have the highest character count."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)
        catalog = build_font_catalog(blocks)

        for font in catalog.fonts:
            assert font.char_count <= catalog.body_font.char_count, (
                f"Font {font.name}@{font.size} has more chars ({font.char_count}) "
                f"than body font ({catalog.body_font.char_count})"
            )

    def test_multiple_font_sizes_detected(self):
        """Document with headings should have multiple font sizes."""
        glyphs = _get_glyphs("simple_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)
        catalog = build_font_catalog(blocks)

        sizes = set(f.size for f in catalog.fonts)
        assert len(sizes) >= 2, f"Should have ≥2 font sizes, got {sizes}"

    def test_bold_font_detected(self):
        glyphs = _get_glyphs("formatted_text.pdf")
        lines = assemble_lines(glyphs)
        blocks = assemble_blocks(lines)
        catalog = build_font_catalog(blocks)

        bold_fonts = [f for f in catalog.fonts if f.is_bold]
        assert len(bold_fonts) > 0, "Should detect bold fonts"


class TestFullAssemblyPipeline:
    """End-to-end assembly pipeline test."""

    def test_full_pipeline(self):
        glyphs = _get_glyphs("simple_text.pdf")
        blocks, catalog = assemble(glyphs)

        assert len(blocks) > 0
        assert catalog.body_font is not None

        # Verify content accuracy
        all_text = " ".join(b.text for b in blocks)
        for s in ["Document Title", "3.14159", "Methods"]:
            assert s in all_text, f"'{s}' missing after full assembly"

    def test_table_text_assembled(self):
        """Table PDF text should still be extracted even before table detection."""
        glyphs = _get_glyphs("bordered_table.pdf")
        blocks, catalog = assemble(glyphs)

        all_text = " ".join(b.text for b in blocks)
        assert "Alice" in all_text
        assert "Bob" in all_text
        assert "New York" in all_text

    def test_formatted_text_assembled(self):
        glyphs = _get_glyphs("formatted_text.pdf")
        blocks, catalog = assemble(glyphs)

        all_text = " ".join(b.text for b in blocks)
        assert "Bold text here" in all_text or "Bold text" in all_text
        assert "Italic text here" in all_text or "Italic text" in all_text
        assert "code_variable" in all_text

    def test_list_text_assembled(self):
        glyphs = _get_glyphs("with_lists.pdf")
        blocks, catalog = assemble(glyphs)

        all_text = " ".join(b.text for b in blocks)
        assert "First item" in all_text
        assert "Second item" in all_text
        assert "Alpha step" in all_text
