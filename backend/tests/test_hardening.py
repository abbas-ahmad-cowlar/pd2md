"""
Tests for Phase 8: Hardening.

Verifies:
  - Input validation (corrupt files, empty files, wrong format)
  - Error handling resilience
  - Content accuracy validation
  - Edge case handling (minimal PDFs, large text)
  - Logging and timing data
"""

import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.pipeline.orchestrator import PipelineOrchestrator, ConversionError
from backend.app.pipeline.validator import validate_conversion, ValidationReport
from backend.app.models.document import (
    BBox,
    BlockType,
    ContentBlock,
    DocumentMetadata,
    DocumentResult,
    PageResult,
    TextBlock,
    TextLine,
    TextSpan,
)

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent / "test_output"


# ─── Helper: create minimal test PDFs ─────────────────────────

def _create_empty_pdf(path: Path):
    """Create a valid PDF with zero text content."""
    doc = fitz.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()


def _create_minimal_pdf(path: Path, text: str = "Hello"):
    """Create a minimal 1-page PDF with given text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()


def _create_not_a_pdf(path: Path):
    """Create a file that is NOT a PDF."""
    path.write_text("This is not a PDF file.")


def _create_empty_file(path: Path):
    """Create an empty (0-byte) file."""
    path.write_bytes(b"")


# ─── Phase 8.1 — Content Accuracy Validation ──────────────────

class TestContentValidation:
    """Step 8.1 — Content accuracy validation."""

    def test_validation_passes_simple(self):
        output = OUTPUT / "val_simple"
        pipe = PipelineOrchestrator(FIXTURES / "simple_text.pdf", output)
        result = pipe.convert()

        assert pipe.validation_report is not None
        report = pipe.validation_report
        assert report.overall_score > 0.5, f"Score too low: {report.overall_score}"

    def test_validation_counts_blocks(self):
        output = OUTPUT / "val_blocks"
        pipe = PipelineOrchestrator(FIXTURES / "simple_text.pdf", output)
        result = pipe.convert()

        report = pipe.validation_report
        assert report.total_blocks > 0
        assert report.classified_blocks > 0

    def test_validation_report_summary(self):
        output = OUTPUT / "val_summary"
        pipe = PipelineOrchestrator(FIXTURES / "simple_text.pdf", output)
        pipe.convert()

        report = pipe.validation_report
        summary = report.summary()
        assert "Score:" in summary
        assert "Blocks:" in summary

    def test_validation_for_table_pdf(self):
        output = OUTPUT / "val_table"
        pipe = PipelineOrchestrator(FIXTURES / "bordered_table.pdf", output)
        pipe.convert()

        report = pipe.validation_report
        assert report.overall_score > 0.5

    def test_validation_can_be_disabled(self):
        output = OUTPUT / "val_disabled"
        pipe = PipelineOrchestrator(
            FIXTURES / "simple_text.pdf", output, validate=False
        )
        pipe.convert()
        assert pipe.validation_report is None


# ─── Phase 8.2 — Error Handling & Resilience ──────────────────

class TestErrorHandling:
    """Step 8.2 — Error handling & resilience."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            pipe = PipelineOrchestrator(Path("nonexistent.pdf"), OUTPUT / "err_fnf")
            pipe.convert()

    def test_empty_file(self):
        path = OUTPUT / "err_empty" / "empty.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        _create_empty_file(path)

        with pytest.raises(ConversionError, match="empty"):
            pipe = PipelineOrchestrator(path, OUTPUT / "err_empty_out")
            pipe.convert()

    def test_not_a_pdf(self):
        path = OUTPUT / "err_notpdf" / "fake.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        _create_not_a_pdf(path)

        with pytest.raises(ConversionError, match="valid PDF"):
            pipe = PipelineOrchestrator(path, OUTPUT / "err_notpdf_out")
            pipe.convert()

    def test_conversion_error_is_exception(self):
        """ConversionError should be a proper exception."""
        err = ConversionError("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)


# ─── Phase 8.3 — Edge Case Handling ───────────────────────────

class TestEdgeCases:
    """Step 8.3 — Edge case handling."""

    def test_empty_pdf_no_crash(self):
        """PDF with blank pages should not crash."""
        path = OUTPUT / "edge_blank" / "blank.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        _create_empty_pdf(path)

        pipe = PipelineOrchestrator(path, OUTPUT / "edge_blank_out")
        result = pipe.convert()
        assert result is not None
        assert len(result.pages) == 1

    def test_minimal_text(self):
        """PDF with a single word should convert cleanly."""
        path = OUTPUT / "edge_minimal" / "mini.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        _create_minimal_pdf(path, "Hello")

        pipe = PipelineOrchestrator(path, OUTPUT / "edge_minimal_out")
        result = pipe.convert()
        md_path = OUTPUT / "edge_minimal_out" / "mini.md"
        assert md_path.exists()
        md = md_path.read_text(encoding="utf-8")
        assert "Hello" in md

    def test_special_characters(self):
        """PDF with special chars (unicode, symbols) should preserve them."""
        path = OUTPUT / "edge_special" / "special.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        _create_minimal_pdf(path, "Testing: \u00e9\u00e8\u00ea \u00fc\u00f6\u00e4 3.14 & 42%")

        pipe = PipelineOrchestrator(path, OUTPUT / "edge_special_out")
        result = pipe.convert()
        md_path = OUTPUT / "edge_special_out" / "special.md"
        md = md_path.read_text(encoding="utf-8")
        assert "3.14" in md
        assert "&" in md

    def test_multipage_fixture(self):
        """Multi-page doc should produce all page content."""
        pipe = PipelineOrchestrator(
            FIXTURES / "multipage.pdf", OUTPUT / "edge_multi"
        )
        result = pipe.convert()
        assert len(result.pages) == 3


# ─── Phase 8.4 — Logging & Diagnostics ───────────────────────

class TestLoggingDiagnostics:
    """Step 8.4 — Logging & diagnostics."""

    def test_timings_available(self):
        pipe = PipelineOrchestrator(FIXTURES / "simple_text.pdf", OUTPUT / "diag_timing")
        pipe.convert()

        timings = pipe.timings
        assert "extraction" in timings
        assert "assembly" in timings
        assert "layout" in timings
        assert "total" in timings
        assert all(v >= 0 for v in timings.values())

    def test_total_time_reasonable(self):
        pipe = PipelineOrchestrator(FIXTURES / "simple_text.pdf", OUTPUT / "diag_time")
        pipe.convert()

        total = pipe.timings.get("total", 999)
        assert total < 30, f"Conversion took {total:.1f}s — too slow for a test PDF"

    def test_progress_reaches_100(self):
        pipe = PipelineOrchestrator(FIXTURES / "simple_text.pdf", OUTPUT / "diag_prog")

        progress_values = []
        pipe.set_progress_callback(lambda p, s: progress_values.append(p))
        pipe.convert()

        assert 100 in progress_values
        assert progress_values == sorted(progress_values)  # Monotonically increasing

    def test_options_respected(self):
        """Custom options passed to orchestrator should take effect."""
        pipe = PipelineOrchestrator(
            FIXTURES / "simple_text.pdf",
            OUTPUT / "diag_opts",
            include_frontmatter=False,
        )
        pipe.convert()

        md_path = OUTPUT / "diag_opts" / "simple_text.md"
        md = md_path.read_text(encoding="utf-8")
        assert not md.startswith("---"), "Frontmatter should not be present"
