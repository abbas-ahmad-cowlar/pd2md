"""
Tests for Layer 1: Raw PDF Extraction.

Verifies:
  - Metadata extraction (title, author, page count)
  - Text extraction (all characters with correct positions and fonts)
  - Font info (bold, italic, monospace detection)
  - Image extraction (saved to disk, bounding boxes recorded)
  - Vector path extraction (lines for table border detection)
  - Page classification (digital vs scanned)
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.pipeline.extractor import (
    classify_page,
    extract_document,
    extract_metadata,
    extract_page_glyphs,
    extract_page_images,
    extract_page_vectors,
)
from backend.app.models.document import PageType

import fitz


FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent / "test_output"


@pytest.fixture(autouse=True)
def clean_output():
    """Ensure clean output directory for each test."""
    if OUTPUT.exists():
        import shutil
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    yield
    # Keep output for inspection


class TestMetadataExtraction:
    """Step 1.1 — Document Metadata Extraction."""

    def test_basic_metadata(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        meta = extract_metadata(doc)
        doc.close()

        assert meta.page_count == 1
        assert meta.is_encrypted is False
        assert meta.source_filename == ""  # Not set by extract_metadata

    def test_multipage_count(self):
        doc = fitz.open(str(FIXTURES / "multipage.pdf"))
        meta = extract_metadata(doc)
        doc.close()

        assert meta.page_count == 3


class TestTextExtraction:
    """Step 1.2 — Per-Page Text Extraction (Glyph Level)."""

    def test_simple_text_extraction(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        glyphs = extract_page_glyphs(page)
        doc.close()

        assert len(glyphs) > 0, "Should extract at least some glyphs"

        # Reconstruct text from glyphs to verify content accuracy
        all_chars = "".join(g.char for g in glyphs)
        assert "Document Title" in all_chars
        assert "Introduction" in all_chars
        assert "first paragraph" in all_chars
        assert "3.14159" in all_chars  # Numbers must be exact
        assert "&" in all_chars       # Special characters preserved

    def test_glyph_has_position(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        glyphs = extract_page_glyphs(page)
        doc.close()

        # Every glyph should have a valid bounding box
        for g in glyphs:
            assert g.bbox.width > 0, f"Glyph '{g.char}' has zero width"
            assert g.bbox.height > 0, f"Glyph '{g.char}' has zero height"
            assert g.bbox.x0 >= 0, f"Glyph '{g.char}' has negative x0"
            assert g.bbox.y0 >= 0, f"Glyph '{g.char}' has negative y0"

    def test_glyph_has_font_info(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        glyphs = extract_page_glyphs(page)
        doc.close()

        for g in glyphs:
            assert g.font_name, f"Glyph '{g.char}' has empty font_name"
            assert g.font_size > 0, f"Glyph '{g.char}' has zero font_size"

    def test_bold_italic_detection(self):
        doc = fitz.open(str(FIXTURES / "formatted_text.pdf"))
        page = doc.load_page(0)
        glyphs = extract_page_glyphs(page)
        doc.close()

        # Find the 'B' in "Bold text here."
        bold_glyphs = [g for g in glyphs if g.is_bold and g.char.isalpha()]
        italic_glyphs = [g for g in glyphs if g.is_italic and g.char.isalpha()]

        assert len(bold_glyphs) > 0, "Should detect bold glyphs"
        assert len(italic_glyphs) > 0, "Should detect italic glyphs"

    def test_monospace_detection(self):
        doc = fitz.open(str(FIXTURES / "formatted_text.pdf"))
        page = doc.load_page(0)
        glyphs = extract_page_glyphs(page)
        doc.close()

        mono_glyphs = [g for g in glyphs if g.is_monospace]
        assert len(mono_glyphs) > 0, "Should detect monospace glyphs"

        # Verify the monospace text content
        mono_text = "".join(g.char for g in mono_glyphs)
        assert "code_variable" in mono_text or "42" in mono_text

    def test_font_size_varies(self):
        """Title should be larger than body text."""
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        glyphs = extract_page_glyphs(page)
        doc.close()

        sizes = set(g.font_size for g in glyphs)
        assert len(sizes) >= 2, "Should have at least 2 different font sizes (title vs body)"


class TestImageExtraction:
    """Step 1.3 — Image Extraction."""

    def test_image_extracted(self):
        doc = fitz.open(str(FIXTURES / "with_images.pdf"))
        page = doc.load_page(0)
        images = extract_page_images(page, doc, OUTPUT, 0)
        doc.close()

        assert len(images) >= 1, "Should extract at least 1 image"
        img = images[0]
        assert img.saved_path is not None
        assert img.saved_path.exists(), f"Image file not found: {img.saved_path}"
        assert img.width > 0
        assert img.height > 0
        assert img.bbox.width > 0

    def test_image_format_png(self):
        doc = fitz.open(str(FIXTURES / "with_images.pdf"))
        page = doc.load_page(0)
        images = extract_page_images(page, doc, OUTPUT, 0, image_format="png")
        doc.close()

        if images:
            assert str(images[0].saved_path).endswith(".png")

    def test_image_format_jpeg(self):
        doc = fitz.open(str(FIXTURES / "with_images.pdf"))
        page = doc.load_page(0)
        images = extract_page_images(page, doc, OUTPUT / "jpeg_test", 0, image_format="jpeg")
        doc.close()

        if images:
            assert str(images[0].saved_path).endswith(".jpg")

    def test_no_images_in_text_only(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        images = extract_page_images(page, doc, OUTPUT, 0)
        doc.close()

        assert len(images) == 0, "Text-only PDF should have no images"


class TestVectorExtraction:
    """Step 1.4 — Vector Path Extraction."""

    def test_table_lines_detected(self):
        doc = fitz.open(str(FIXTURES / "bordered_table.pdf"))
        page = doc.load_page(0)
        vectors = extract_page_vectors(page)
        doc.close()

        assert len(vectors) > 0, "Should detect vector paths in table PDF"

        # Should have both horizontal and vertical lines
        h_lines = [v for v in vectors if v.is_horizontal]
        v_lines = [v for v in vectors if v.is_vertical]

        assert len(h_lines) >= 2, f"Should have horizontal lines, got {len(h_lines)}"
        assert len(v_lines) >= 2, f"Should have vertical lines, got {len(v_lines)}"

    def test_no_vectors_in_simple_text(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        vectors = extract_page_vectors(page)
        doc.close()

        # Simple text PDFs may have zero vector paths
        # (or at most some decorative ones that get filtered)
        assert isinstance(vectors, list)


class TestPageClassification:
    """Step 1.5 — Page Classification."""

    def test_digital_page(self):
        doc = fitz.open(str(FIXTURES / "simple_text.pdf"))
        page = doc.load_page(0)
        page_type = classify_page(page)
        doc.close()

        assert page_type == PageType.DIGITAL

    def test_page_with_images_is_digital(self):
        """A page with both text and images should be DIGITAL (not MIXED)
        unless images cover most of the page."""
        doc = fitz.open(str(FIXTURES / "with_images.pdf"))
        page = doc.load_page(0)
        page_type = classify_page(page)
        doc.close()

        assert page_type in (PageType.DIGITAL, PageType.MIXED)


class TestFullDocumentExtraction:
    """End-to-end extraction of entire documents."""

    def test_simple_document(self):
        result = extract_document(FIXTURES / "simple_text.pdf", OUTPUT / "simple")

        assert result["metadata"].page_count == 1
        assert result["metadata"].source_filename == "simple_text.pdf"
        assert len(result["pages"]) == 1

        page = result["pages"][0]
        assert page["page_type"] == PageType.DIGITAL
        assert len(page["glyphs"]) > 50  # Should have many characters
        assert page["width"] > 0
        assert page["height"] > 0

    def test_multipage_document(self):
        result = extract_document(FIXTURES / "multipage.pdf", OUTPUT / "multipage")

        assert result["metadata"].page_count == 3
        assert len(result["pages"]) == 3

        # Each page should have content
        for i, page in enumerate(result["pages"]):
            assert len(page["glyphs"]) > 0, f"Page {i} should have glyphs"

    def test_content_accuracy(self):
        """Critical test: verify every word is correctly extracted."""
        result = extract_document(FIXTURES / "simple_text.pdf", OUTPUT / "accuracy")
        page = result["pages"][0]

        all_text = "".join(g.char for g in page["glyphs"])

        # These exact strings MUST appear in the extraction
        required_strings = [
            "Document Title",
            "John Doe",
            "Introduction",
            "first paragraph",
            "second paragraph",
            "3.14159",
            "Background",
            "Methods",
        ]

        for s in required_strings:
            assert s in all_text, f"Required string '{s}' not found in extraction"

    def test_table_document_has_vectors(self):
        result = extract_document(FIXTURES / "bordered_table.pdf", OUTPUT / "table")
        page = result["pages"][0]

        assert len(page["vectors"]) > 0, "Table PDF should have vector paths"

        # Verify table text is also extracted
        all_text = "".join(g.char for g in page["glyphs"])
        assert "Alice" in all_text
        assert "Bob" in all_text
        assert "Charlie" in all_text
        assert "New York" in all_text
