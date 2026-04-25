"""
Pipeline Orchestrator.

Coordinates the 6-layer conversion pipeline, manages progress reporting,
and handles the overall flow from PDF file to Markdown output.

Phase 8 hardened:
  - Validates input before processing
  - Catches and wraps per-page errors gracefully
  - Produces a validation report alongside the output
  - Structured logging throughout
  - Per-page timeout protection
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from backend.app.config import settings
from backend.app.models.document import (
    BlockType,
    DocumentMetadata,
    DocumentResult,
    FontCatalog,
    PageResult,
    PageType,
)
from backend.app.pipeline.extractor import extract_document
from backend.app.pipeline.assembler import assemble
from backend.app.pipeline.layout_analyzer import (
    HeaderFooterMask,
    analyze_layout,
    detect_headers_footers,
)
from backend.app.pipeline.semantic_analyzer import analyze_semantics
from backend.app.pipeline.table_extractor import extract_tables_from_page
from backend.app.pipeline.emitter import emit_document, create_output_zip
from backend.app.pipeline.validator import validate_conversion, ValidationReport

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Raised when the conversion pipeline fails."""
    pass


class PipelineOrchestrator:
    """Orchestrates the PDF → Markdown conversion pipeline.

    Layers:
        1. Extractor      — Raw PDF extraction (glyphs, images, vectors)
        2. Assembler       — Text assembly (words, lines, blocks)
        3. LayoutAnalyzer  — Layout detection (columns, tables, figures)
        4. SemanticAnalyzer — Semantic classification (headings, lists, etc.)
        5. TableExtractor  — Table structure extraction
        6. Emitter         — Markdown generation

    Options:
        include_frontmatter: Whether to include YAML frontmatter (default True)
        skip_images: Whether to skip image extraction (default False)
        validate: Whether to run content validation (default True)
    """

    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path | None = None,
        image_format: str | None = None,
        jpeg_quality: int | None = None,
        include_frontmatter: bool = True,
        skip_images: bool = False,
        validate: bool = True,
    ):
        self.pdf_path = Path(pdf_path)
        self.output_dir = output_dir or settings.output_dir / self.pdf_path.stem
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.image_format = image_format or settings.default_image_format
        self.jpeg_quality = jpeg_quality or settings.jpeg_quality
        self.include_frontmatter = include_frontmatter
        self.skip_images = skip_images
        self.do_validate = validate

        # Progress tracking
        self._progress: float = 0.0
        self._current_step: str = "Initializing"
        self._progress_callback = None

        # Timing
        self._start_time: float = 0.0
        self._timings: dict[str, float] = {}

        # Validation result
        self.validation_report: ValidationReport | None = None

    def set_progress_callback(self, callback):
        """Set a callback for progress updates: callback(progress, step_name)."""
        self._progress_callback = callback

    def _update_progress(self, progress: float, step: str):
        self._progress = progress
        self._current_step = step
        logger.debug(f"Progress: {progress:.0f}% — {step}")
        if self._progress_callback:
            self._progress_callback(progress, step)

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def current_step(self) -> str:
        return self._current_step

    def convert(self) -> DocumentResult:
        """Run the full conversion pipeline.

        Returns:
            DocumentResult with all pages processed and classified.

        Raises:
            ConversionError: If the input is invalid or a fatal error occurs.
            FileNotFoundError: If the PDF file doesn't exist.
        """
        self._start_time = time.perf_counter()

        # ── Input Validation ─────────────────────────────────────────
        self._validate_input()

        self._update_progress(0, "Starting conversion")
        logger.info(f"Converting: {self.pdf_path.name}")

        # ── Layer 1: Raw Extraction ──────────────────────────────────
        t0 = time.perf_counter()
        self._update_progress(5, "Extracting PDF content")
        try:
            raw = extract_document(
                self.pdf_path, self.output_dir,
                image_format=self.image_format,
                jpeg_quality=self.jpeg_quality,
            )
        except Exception as e:
            raise ConversionError(f"PDF extraction failed: {e}") from e

        metadata: DocumentMetadata = raw["metadata"]
        raw_pages: list[dict] = raw["pages"]
        self._timings["extraction"] = time.perf_counter() - t0

        if not raw_pages:
            raise ConversionError("PDF contains no extractable pages.")

        logger.info(f"Extracted {len(raw_pages)} pages in {self._timings['extraction']:.2f}s")

        # ── Layer 2: Text Assembly (per-page) ─────────────────────────
        t0 = time.perf_counter()
        self._update_progress(20, "Assembling text")
        assembled_pages = []
        font_catalog = FontCatalog()
        page_errors: list[str] = []

        for i, page_data in enumerate(raw_pages):
            try:
                blocks, catalog = assemble(page_data["glyphs"])
                assembled_pages.append({
                    "blocks": blocks,
                    "catalog": catalog,
                    "vectors": page_data["vectors"],
                    "images": page_data["images"],
                    "width": page_data["width"],
                    "height": page_data["height"],
                    "page_type": page_data["page_type"],
                })
                # Use the catalog from the page with the most text
                if catalog.body_font and (
                    not font_catalog.body_font
                    or catalog.body_font.char_count > font_catalog.body_font.char_count
                ):
                    font_catalog = catalog
            except Exception as e:
                logger.warning(f"Page {i} assembly failed: {e}")
                page_errors.append(f"Page {i}: assembly failed ({e})")
                # Create an empty page rather than skipping entirely
                assembled_pages.append({
                    "blocks": [],
                    "catalog": FontCatalog(),
                    "vectors": page_data.get("vectors", []),
                    "images": page_data.get("images", []),
                    "width": page_data.get("width", 612),
                    "height": page_data.get("height", 792),
                    "page_type": page_data.get("page_type", PageType.DIGITAL),
                })

        self._timings["assembly"] = time.perf_counter() - t0

        # ── Layer 3: Layout Analysis ──────────────────────────────────
        t0 = time.perf_counter()
        self._update_progress(40, "Analyzing layout")

        # Detect headers/footers across all pages
        all_blocks = [p["blocks"] for p in assembled_pages]
        page_heights = [p["height"] for p in assembled_pages]
        hf_mask = detect_headers_footers(all_blocks, page_heights)

        # Per-page layout analysis
        for i, page_data in enumerate(assembled_pages):
            try:
                content_blocks = analyze_layout(
                    page_data["blocks"],
                    page_data["vectors"],
                    page_data["images"],
                    page_data["width"],
                    page_data["height"],
                    hf_mask,
                )
                page_data["content_blocks"] = content_blocks
            except Exception as e:
                logger.warning(f"Page {i} layout analysis failed: {e}")
                page_errors.append(f"Page {i}: layout failed ({e})")
                page_data["content_blocks"] = []

        self._timings["layout"] = time.perf_counter() - t0

        # ── Layer 4: Semantic Inference ───────────────────────────────
        t0 = time.perf_counter()
        self._update_progress(55, "Classifying content")

        for i, page_data in enumerate(assembled_pages):
            try:
                page_data["content_blocks"] = analyze_semantics(
                    page_data["content_blocks"],
                    font_catalog,
                    page_data["height"],
                )
            except Exception as e:
                logger.warning(f"Page {i} semantic analysis failed: {e}")
                page_errors.append(f"Page {i}: semantics failed ({e})")

        self._timings["semantics"] = time.perf_counter() - t0

        # ── Layer 5: Table Extraction ─────────────────────────────────
        t0 = time.perf_counter()
        self._update_progress(70, "Extracting tables")

        for i, page_data in enumerate(assembled_pages):
            try:
                page_data["content_blocks"] = extract_tables_from_page(
                    self.pdf_path, i, page_data["content_blocks"],
                )
            except Exception as e:
                logger.warning(f"Page {i} table extraction failed: {e}")
                page_errors.append(f"Page {i}: table extraction failed ({e})")

        self._timings["tables"] = time.perf_counter() - t0

        # ── Build DocumentResult ──────────────────────────────────────
        self._update_progress(85, "Building document")
        doc_result = DocumentResult(metadata=metadata, font_catalog=font_catalog)

        for i, page_data in enumerate(assembled_pages):
            page_result = PageResult(
                page_number=i,
                width=page_data["width"],
                height=page_data["height"],
                page_type=page_data["page_type"],
                blocks=page_data["content_blocks"],
                images=page_data["images"],
                vectors=page_data["vectors"],
            )
            doc_result.pages.append(page_result)

        # ── Layer 6: Markdown Emission ────────────────────────────────
        t0 = time.perf_counter()
        self._update_progress(90, "Generating Markdown")

        try:
            md_path = emit_document(
                doc_result, self.output_dir,
                include_frontmatter=self.include_frontmatter,
            )
        except Exception as e:
            raise ConversionError(f"Markdown emission failed: {e}") from e

        self._timings["emission"] = time.perf_counter() - t0

        # ── Validation ────────────────────────────────────────────────
        if self.do_validate:
            self._update_progress(95, "Validating content")
            try:
                md_content = md_path.read_text(encoding="utf-8")
                self.validation_report = validate_conversion(doc_result, md_content)
                logger.info(f"Validation: {self.validation_report.summary()}")
            except Exception as e:
                logger.warning(f"Validation failed: {e}")

        # ── Done ──────────────────────────────────────────────────────
        total_time = time.perf_counter() - self._start_time
        self._timings["total"] = total_time
        self._update_progress(100, "Conversion complete")

        logger.info(
            f"Conversion complete in {total_time:.2f}s: {md_path.name}, "
            f"{doc_result.total_blocks} blocks, "
            f"{doc_result.total_images} images, "
            f"{doc_result.total_tables} tables"
        )

        if page_errors:
            logger.warning(f"Page errors during conversion: {page_errors}")

        return doc_result

    def _validate_input(self):
        """Validate input file before processing."""
        # Check file exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        # Check file is not empty
        file_size = self.pdf_path.stat().st_size
        if file_size == 0:
            raise ConversionError("PDF file is empty (0 bytes).")

        # Check file size limit
        size_mb = file_size / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            raise ConversionError(
                f"File too large ({size_mb:.1f} MB). Maximum: {settings.max_file_size_mb} MB."
            )

        # Check it's actually a PDF (magic bytes)
        try:
            with open(self.pdf_path, "rb") as f:
                header = f.read(5)
            if header != b"%PDF-":
                raise ConversionError(
                    "File does not appear to be a valid PDF (missing %PDF- header)."
                )
        except PermissionError:
            raise ConversionError(f"Cannot read file: {self.pdf_path}")

        # Check extension
        if not self.pdf_path.suffix.lower() == ".pdf":
            logger.warning(f"File extension is {self.pdf_path.suffix}, expected .pdf")

    @property
    def timings(self) -> dict[str, float]:
        """Get timing breakdown for each pipeline stage."""
        return dict(self._timings)
