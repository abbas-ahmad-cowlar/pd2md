"""
Tests for Phase 9: Advanced Features.

Verifies:
  - CLI single file conversion
  - CLI batch processing
  - Quality report generation
  - Custom output options (frontmatter, image format)
"""

import sys
import subprocess
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.pipeline.orchestrator import PipelineOrchestrator

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent / "test_output"
PYTHON = sys.executable


# ─── Phase 9.1 — CLI Mode ────────────────────────────────────

class TestCLI:
    """Step 9.1 — CLI mode."""

    def test_cli_help(self):
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "--help"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "PD2MD" in result.stdout

    def test_cli_convert_help(self):
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "convert", "--help"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "--image-format" in result.stdout

    def test_cli_convert(self):
        out_dir = OUTPUT / "cli_convert"
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "convert",
             str(FIXTURES / "simple_text.pdf"),
             "-o", str(out_dir)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "complete" in result.stdout.lower() or "[ok]" in result.stdout.lower()

        # Check output exists
        md_path = out_dir / "simple_text.md"
        assert md_path.exists()

    def test_cli_convert_no_frontmatter(self):
        out_dir = OUTPUT / "cli_nofm"
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "convert",
             str(FIXTURES / "simple_text.pdf"),
             "-o", str(out_dir), "--no-frontmatter"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        md = (out_dir / "simple_text.md").read_text(encoding="utf-8")
        assert not md.startswith("---")

    def test_cli_missing_file(self):
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "convert", "nonexistent.pdf"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode != 0

    def test_cli_report(self):
        out_dir = OUTPUT / "cli_report"
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "convert",
             str(FIXTURES / "simple_text.pdf"),
             "-o", str(out_dir), "--report"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "Quality Report" in result.stdout


# ─── Phase 9.2 — Batch Processing ────────────────────────────

class TestBatch:
    """Step 9.2 — Batch processing."""

    def test_batch_convert(self):
        out_dir = OUTPUT / "batch_out"
        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "batch",
             str(FIXTURES), "-o", str(out_dir)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "succeeded" in result.stdout.lower() or "complete" in result.stdout.lower() or "batch" in result.stdout.lower()

        # Check batch report was created
        report_path = out_dir / "batch_report.json"
        assert report_path.exists()

        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert len(report) >= 2  # At least 2 PDFs in fixtures

    def test_batch_empty_dir(self):
        empty_dir = OUTPUT / "batch_empty"
        empty_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [PYTHON, "-m", "backend.app.cli", "batch", str(empty_dir)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode != 0


# ─── Phase 9.3 — Quality Report ──────────────────────────────

class TestQualityReport:
    """Step 9.3 — Quality report."""

    def test_validation_report_format(self):
        pipe = PipelineOrchestrator(
            FIXTURES / "simple_text.pdf", OUTPUT / "qr_format"
        )
        pipe.convert()

        report = pipe.validation_report
        assert report is not None

        summary = report.summary()
        assert "Score:" in summary
        assert "%" in summary
        assert "Blocks:" in summary


# ─── Phase 9.4 — Custom Output Options ───────────────────────

class TestCustomOptions:
    """Step 9.4 — Custom output options."""

    def test_jpeg_image_format(self):
        out_dir = OUTPUT / "opt_jpeg"
        pipe = PipelineOrchestrator(
            FIXTURES / "with_images.pdf",
            out_dir,
            image_format="jpeg",
            jpeg_quality=90,
        )
        pipe.convert()

        # Images should exist in output
        md_path = out_dir / "with_images.md"
        assert md_path.exists()

    def test_no_frontmatter_option(self):
        out_dir = OUTPUT / "opt_nofm"
        pipe = PipelineOrchestrator(
            FIXTURES / "simple_text.pdf",
            out_dir,
            include_frontmatter=False,
        )
        pipe.convert()

        md = (out_dir / "simple_text.md").read_text(encoding="utf-8")
        assert not md.startswith("---")

    def test_with_frontmatter_option(self):
        out_dir = OUTPUT / "opt_fm"
        pipe = PipelineOrchestrator(
            FIXTURES / "simple_text.pdf",
            out_dir,
            include_frontmatter=True,
        )
        pipe.convert()

        md = (out_dir / "simple_text.md").read_text(encoding="utf-8")
        assert md.startswith("---")

    def test_skip_validation_option(self):
        out_dir = OUTPUT / "opt_noval"
        pipe = PipelineOrchestrator(
            FIXTURES / "simple_text.pdf",
            out_dir,
            validate=False,
        )
        pipe.convert()
        assert pipe.validation_report is None
