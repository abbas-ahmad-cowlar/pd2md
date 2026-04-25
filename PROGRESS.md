# PD2MD — Task Tracker

## Phase 0 — Project Foundation
- [x] Step 0.1 — Project Structure Creation
- [x] Step 0.2 — Virtual Environment & Dependencies
- [x] Step 0.3 — Core Data Models (IR)
- [x] Step 0.4 — Basic FastAPI Skeleton
- [x] 🏁 CHECKPOINT 0 — Foundation Verified ✅
  - All imports OK (PyMuPDF 1.27.2, pdfplumber 0.11.9, FastAPI 0.135.3)
  - All data models instantiate correctly (BBox, RawGlyph, DocumentResult)
  - FastAPI starts and serves /api/health → 200

## Phase 1 — Raw PDF Extraction
## Phase 1 — Raw PDF Extraction
- [x] Step 1.1 — Document Metadata Extraction
- [x] Step 1.2 — Per-Page Text Extraction (Glyph Level)
- [x] Step 1.3 — Image Extraction
- [x] Step 1.4 — Vector Path Extraction
- [x] Step 1.5 — Page Classification
- [x] 🏁 CHECKPOINT 1 — Raw Extraction Verified ✅ (20/20 tests passed in 0.49s)
  - Text extraction: all characters correct, positions valid, font info present
  - Bold/italic/monospace: detected correctly from font names
  - Images: extracted as PNG and JPEG, bounding boxes recorded
  - Vectors: table border lines detected (horizontal + vertical)
  - Page classification: digital pages identified correctly
  - Content accuracy: all required strings found in extraction

## Phase 2 — Text Assembly
- [x] Step 2.1 — Glyph → Word Assembly
- [x] Step 2.2 — Word → Line Assembly
- [x] Step 2.3 — Line → Block Assembly
- [x] Step 2.4 — Dehyphenation
- [x] Step 2.5 — Font Catalog Build
- [x] 🏁 CHECKPOINT 2 — Text Assembly Verified ✅ (23/23 tests, 43/43 total regression)
  - Words have correct spaces, no character soup
  - Lines grouped correctly by y-coordinate
  - Blocks separate at headings and paragraph gaps
  - Font catalog identifies body font and multiple sizes
  - Content accuracy: all required strings found after assembly

## Phase 3 — Layout Analysis
- [x] Step 3.1 — Header/Footer Detection & Removal
- [x] Step 3.2 — Column Detection
- [x] Step 3.3 — Table Region Detection
- [x] Step 3.4 — Image Region Detection
- [x] Step 3.5 — Code Block Detection
- [x] Step 3.6 — Reading Order Determination
- [x] 🏁 CHECKPOINT 3 — Layout Analysis Verified ✅ (18/18 tests, 61/61 total)
  - Headers/footers detected via cross-page repetition
  - Columns: single-column correctly identified, false-positive 2-col fixed
  - Table regions: bordered tables detected via line clustering
  - Image regions: images inserted in reading order
  - Code blocks: monospace text flagged, normal text clean
  - Reading order: top-to-bottom verified, content accuracy preserved

## Phase 4 — Semantic Inference
- [x] Step 4.1 — Heading Detection & Level Assignment
- [x] Step 4.2 — Paragraph Assembly
- [x] Step 4.3 — List Detection
- [x] Step 4.4 — Emphasis & Inline Formatting Recovery
- [x] Step 4.5 — Link Extraction
- [x] Step 4.6 — Footnote Handling
- [x] 🏁 CHECKPOINT 4 — Semantic Inference Verified ✅ (18/18 tests, 79/79 total)
  - Headings: title=H1, sections=H2/H3, body text excluded
  - Lists: bullet (including 0xB7 middle dot) + ordered both detected
  - List splitting: multi-item blocks correctly split into individual items
  - Paragraphs: all UNKNOWN blocks classified, no orphans
  - Emphasis: bold/italic spans preserved from extraction
  - Content accuracy: all required strings survive 4 layers of processing

## Phase 5 — Table Extraction
- [x] Step 5.1 — Bordered Table Extraction
- [x] Step 5.2 — Borderless Table Detection (placeholder, handled in pdfplumber fallback)
- [x] Step 5.3 — Merged Cell Detection
- [x] Step 5.4 — Table → Markdown Conversion
- [x] 🏁 CHECKPOINT 5 — Table Extraction Verified ✅ (15/15 tests, 94/94 total)
  - pdfplumber extracts bordered tables with exact cell values
  - Header row detected, alignment detection, merged cells handled
  - Markdown tables: pipes, separators, escaped content
  - Edge cases: empty cells, pipe escaping, synthetic tables
  - No false tables on text-only PDFs

## Phase 6 — Markdown Emission
- [x] Step 6.1 — Document-Level Structure (frontmatter)
- [x] Step 6.2 — Block-by-Block Emission
- [x] Step 6.3 — Whitespace & Formatting Polish
- [x] Step 6.4 — Output Package Assembly
- [x] 🏁 CHECKPOINT 6 — End-to-End Verified ✅ (23/23 tests, 117/117 total)
  - YAML frontmatter with metadata
  - Headings: correct # levels, titles as H1
  - Paragraphs: inline bold/italic/code formatting
  - Lists: bullet + ordered, marker stripping
  - Tables: full markdown pipe tables with headers
  - Images: referenced with ![caption](path)
  - Headers/footers: correctly excluded from output
  - 7 end-to-end PDF → Markdown tests all passing
  - Content accuracy: every test string found in final Markdown

## Phase 7 — Web UI
- [x] Step 7.1 — FastAPI Backend Endpoints (upload, status polling, download MD/ZIP, preview)
- [x] Step 7.2 — Frontend HTML Structure (drag-and-drop, progress, result, preview)
- [x] Step 7.3 — CSS Design System (dark glassmorphism, gradient accents, animations)
- [x] Step 7.4 — JavaScript Logic (file handling, progress polling, download)
- [x] 🏁 CHECKPOINT 7 — Web UI Verified ✅
  - FastAPI serves frontend + API on port 8000
  - Drag-and-drop upload works
  - Background pipeline runs with progress tracking
  - Result page shows stats + markdown preview
  - Download MD and ZIP endpoints functional
  - Modern dark UI with premium design

## Phase 8 — Hardening
- [x] Step 8.1 — Content Accuracy Validation (validator module with confidence scoring)
- [x] Step 8.2 — Error Handling & Resilience (ConversionError, per-page try/except)
- [x] Step 8.3 — Edge Case Handling (empty PDF, minimal text, unicode, invalid files)
- [x] Step 8.4 — Logging & Diagnostics (structured logging, timing breakdown, progress)
- [x] 🏁 CHECKPOINT 8 — Hardened ✅ (17/17 tests, 147/147 total)
  - Input validation: magic bytes check, size limit, file existence
  - Error handling: FileNotFoundError, ConversionError for invalid inputs
  - Per-page resilience: failed pages produce empty content, not crash
  - Validation report: block classification, text coverage, confidence score
  - Timing breakdown: per-stage performance metrics
  - Edge cases: blank PDF, single word, unicode chars all handled

## Phase 9 — Advanced Features
- [x] Step 9.1 — CLI Mode (convert + batch subcommands, argparse)
- [x] Step 9.2 — Batch Processing (directory scan, JSON report, per-file error handling)
- [x] Step 9.3 — Quality Report (table format, timing breakdown, issue list)
- [x] Step 9.4 — Custom Output Options (frontmatter toggle, image format, JPEG quality, validation skip)
- [x] Step 9.5 — ML Enhancement Path (hooks in orchestrator for future plugin layers)
- [x] 🏁 CHECKPOINT 9 — Complete ✅ (13/13 tests, 147/147 total)
  - CLI: pd2md convert + pd2md batch, progress bar, --report flag
  - Batch: processes all PDFs in directory, produces batch_report.json
  - Quality report: block stats, timing breakdown, issue list
  - Custom options: --no-frontmatter, --image-format jpeg, --no-validate
  - Entry point: pyproject.toml [project.scripts] pd2md = backend.app.cli:main
  - Windows-safe: ASCII output, UTF-8 forced on stdout/stderr
