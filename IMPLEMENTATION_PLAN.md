# PD2MD — Intelligent PDF → Markdown Converter

## Implementation Plan

---

## 1. Project Vision

Build a **web-based, intelligent PDF-to-Markdown converter** optimized for **content accuracy** — designed to produce clean, faithful Markdown suitable for **feeding to AI/LLM systems** (reports, papers, technical documents).

### Core Priorities (in order)
1. **Content accuracy** — every word, number, and symbol must be exactly correct
2. **Structural fidelity** — headings, paragraphs, lists, tables, emphasis preserved in the right order
3. **Image extraction** — embedded images extracted and linked in the output
4. **Formatting polish** — clean Markdown that renders well (secondary to content correctness)

> [!IMPORTANT]
> **Primary use case:** Converting reports, papers, and technical documents to Markdown for AI/LLM consumption. Content accuracy trumps visual formatting.

---

## 2. Technology Stack

| Layer | Choice | Why |
|---|---|---|
| **PDF Extraction** | **PyMuPDF (fitz)** | Fastest PDF library. Excellent text, image, and vector extraction. AGPL fine for open-source. |
| **Table Extraction** | **pdfplumber** | MIT license. Best-in-class rule-based table detection. No GPU needed. |
| **Backend API** | **FastAPI** | Async, modern, auto-generates OpenAPI docs. |
| **Frontend** | **Vanilla HTML/CSS/JS** | No framework overhead for a single-page tool. |
| **Image Processing** | **Pillow** | Standard Python imaging for extraction and format conversion. |
| **Testing** | **pytest** + sample PDFs | Unit + integration tests with curated PDF test suite. |

**System:** Windows, Python 3.14, Node.js 24.11, CPU-only (no GPU required).

> [!NOTE]
> **Why not Surya/Marker?** GPL-licensed, require PyTorch + heavy model downloads (~2-4 GB), 10-50x slower on CPU. Our rule-based pipeline is fast and deterministic. ML-enhanced path can be plugged in later via the enhancer architecture (Step 9.5).

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB UI (Browser)                         │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Drop Zone │  │ Progress Bar │  │  Side-by-Side Preview    │  │
│  └─────┬─────┘  └──────┬───────┘  └──────────┬───────────────┘  │
└────────┼───────────────┼──────────────────────┼──────────────────┘
    HTTP POST        Polling              HTTP GET
┌────────┼───────────────┼──────────────────────┼──────────────────┐
│  ┌─────▼───────────────▼──────────────────────▼──────────────┐   │
│  │                  FastAPI Server                            │   │
│  └─────────────────────┬─────────────────────────────────────┘   │
│  ┌─────────────────────▼─────────────────────────────────────┐   │
│  │              CONVERSION PIPELINE (6 Layers)                │   │
│  │  Extract → Assemble → Layout → Semantic → Tables → Emit   │   │
│  │  (PyMuPDF)  (Words/    (Cols,   (Headings, (pdfplumber)    │   │
│  │              Lines/     Tables,   Lists,     → Markdown     │   │
│  │              Blocks)    Figs)     Emphasis)                 │   │
│  └────────────────────────────────────────────────────────────┘   │
│                        BACKEND                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Core Design Principles
1. **Each layer is a separate Python module** — independently testable, swappable
2. **Intermediate representation (IR)** — Every layer produces well-defined dataclasses
3. **Page-by-page processing** — Streaming progress, constant memory
4. **Plugin architecture** — ML models/OCR/LLM post-processors can be plugged in later

---

## 4. Completed Phases (0–9) — ✅ DONE

> **147 tests passing** across all phases. All phases verified at checkpoints.

---

### PHASE 0 — Project Foundation ✅ DONE

**Delivered:** Project skeleton, virtual environment, core IR data models (`BBox`, `RawGlyph`, `TextSpan`, `TextLine`, `TextBlock`, `ContentBlock`, `PageResult`, `DocumentResult`), basic FastAPI health endpoint.

**Key files:** `backend/app/models/document.py`, `backend/app/models/elements.py`, `backend/app/main.py`, `backend/app/config.py`

---

### PHASE 1 — Raw PDF Extraction (Layer 1) ✅ DONE

**Delivered:** Glyph-level text extraction via `page.get_text("rawdict")`, image extraction (PNG/JPEG with CMYK→RGB), vector path extraction for table borders, page classification (DIGITAL/SCANNED/MIXED), document metadata from `/Info` dict.

**Key file:** `backend/app/pipeline/extractor.py` (18KB)
**Tests:** 20/20 passed — text positions, font flags, images as PNG/JPEG, vector lines, page classification.

---

### PHASE 2 — Text Assembly (Layer 2) ✅ DONE

**Delivered:** Glyph→Word assembly (gap analysis with `1.3×` avg char width threshold), Word→Line grouping (y-coordinate tolerance ±font_size/3), Line→Block grouping (gap > `1.8×` line spacing = new block), dehyphenation, font catalog (body font detection, heading/code font classification).

**Key file:** `backend/app/pipeline/assembler.py` (18KB)
**Tests:** 23/23 passed — correct words, lines, blocks, font catalog, content accuracy.

---

### PHASE 3 — Layout Analysis (Layer 3) ✅ DONE

**Delivered:** Header/footer detection via cross-page repetition (≥60% threshold, top/bottom 8%), column detection (vertical whitespace gap analysis), bordered table region detection (line clustering), image region detection with caption association, code block detection (monospace font), reading order (top→bottom, left→right within columns).

**Key file:** `backend/app/pipeline/layout_analyzer.py` (29KB)
**Tests:** 18/18 passed — headers/footers stripped, single-column correct, table regions detected, images positioned, code blocks flagged.

---

### PHASE 4 — Semantic Inference (Layer 4) ✅ DONE

**Delivered:** Heading detection via font size ratio against body font (H1: >1.5×+bold, H2: >1.3×+bold, H3: ≈body+bold), paragraph assembly with cross-page stitching, list detection (bullet chars + ordered patterns + indentation), emphasis recovery (bold→`**`, italic→`*`, monospace→`` ` ``), link extraction (annotations + URL regex), footnote handling (superscript markers → `[^N]`).

**Key file:** `backend/app/pipeline/semantic_analyzer.py` (20KB)
**Tests:** 18/18 passed — headings at correct levels, lists detected, emphasis preserved.

---

### PHASE 5 — Table Extraction (Layer 5) ✅ DONE

**Delivered:** Bordered table extraction via pdfplumber `crop().extract_table()`, header row detection, alignment detection, merged cell handling, Markdown pipe table generation with escaped content.

**Key file:** `backend/app/pipeline/table_extractor.py` (13KB)
**Tests:** 15/15 passed — exact cell values, headers, alignment, merged cells, pipe escaping.

**Known limitation:** Borderless/booktabs tables fall through to raw text (pdfplumber needs visible lines).

---

### PHASE 6 — Markdown Emission (Layer 6) ✅ DONE

**Delivered:** YAML frontmatter, block-by-block emission (headings, paragraphs, lists, tables, images, code), whitespace polishing (blank lines, trim trailing spaces, max 2 consecutive blanks), output package assembly (`.md` + `images/` + `metadata.json` + `.zip`).

**Key file:** `backend/app/pipeline/emitter.py` (14KB)
**Tests:** 23/23 passed — 7 end-to-end PDF→Markdown tests all passing.

---

### PHASE 7 — Web UI ✅ DONE

**Delivered:** FastAPI endpoints (upload, status polling, download MD/ZIP, preview), drag-and-drop frontend with progress tracking, dark glassmorphism design (navy `#0a0e1a`, electric blue `#3b82f6`, Inter + JetBrains Mono fonts), animated drop zone, result page with stats + preview + download.

**Key files:** `frontend/index.html`, `frontend/css/style.css`, `frontend/js/app.js`

---

### PHASE 8 — Hardening ✅ DONE

**Delivered:** Content accuracy validator with confidence scoring, input validation (magic bytes, size limit, file existence), per-page error resilience (failed pages → empty content, not crash), structured logging with timing breakdown, edge case handling (empty PDF, single word, unicode, invalid files).

**Key file:** `backend/app/pipeline/validator.py` (7KB)
**Tests:** 17/17 passed.

---

### PHASE 9 — Advanced Features ✅ DONE

**Delivered:** CLI (`pd2md convert` + `pd2md batch` via argparse), batch processing with JSON report, quality report (block stats, timing, issue list), custom options (`--no-frontmatter`, `--image-format jpeg`, `--no-validate`, `--report`), ML enhancer hooks in orchestrator (future plugin interface).

**Key file:** `backend/app/cli.py`
**Tests:** 13/13 passed. Entry point: `pyproject.toml [project.scripts] pd2md = backend.app.cli:main`

---

## 5. Batch Quality Baseline (21 Test PDFs)

Batch run across all test PDFs reveals current quality distribution:

| Score | PDFs | Categories |
|---|---|---|
| **1.0** | 6 | Simple articles, lists, images, hyperlinks, code listings, mixed stress |
| **0.8–0.9** | 7 | Multi-section reports, formatting, title pages, tables, math, long paragraphs, full report |
| **0.7** | 3 | Bibliographies, enumerations, nested tables |
| **0.4–0.5** | 4 | ❌ Two-column (0.4), Footnotes (0.4), Headings (0.5), Definitions (0.5) |

**Average: ~0.79** — Good for simple/structured PDFs, but 4 test cases are critically broken.

---

## 6. Resolved Design Decisions

| # | Decision |
|---|---|
| Q1 | Python 3.14 (downgrade to 3.12 only if compatibility issues) |
| Q2 | **Content accuracy is #1.** Scanned PDF/OCR is out of scope. Use case: feeding reports to AI/LLMs. |
| Q3 | Image format is user-configurable (PNG vs JPEG) |
| Q4 | AGPL (PyMuPDF) is fine — personal/open-source project |

---

## 7. Phase 10 — Quality Hardening (PLANNED)

> **Goal:** Fix the 4 critically broken test cases (score ≤0.5) and address known output quality gaps. Target: **all test PDFs ≥ 0.8 confidence score.**

---

### Step 10.1 — Two-Column Reading Order Fix (P0 — score: 0.4)

**Problem:** Lines from left and right columns are interleaved instead of reading left-column-first, then right-column.

**Root cause:** The assembler (Phase 2) groups glyphs into lines by y-coordinate. In a two-column PDF, left-column line 1 and right-column line 1 share the same y — so they merge into one `TextBlock`. The existing `_merge_column_blocks()` (layout_analyzer.py L496–589) attempts to split these, but the splitting logic skips non-UNKNOWN blocks and the merging loop has an off-by-one (`split_result.pop(j)` while iterating).

**Sub-steps:**
1. **10.1a — Fix assembler line grouping** (`assembler.py`): Add a `max_line_width` guard — if a "line" is wider than 60% of page width AND has a gap > 3× avg char width in the middle, split it into two lines at the gap point. This prevents cross-column line merging at the source.
2. **10.1b — Fix `_merge_column_blocks` iteration bug** (`layout_analyzer.py` L547–589): Replace the `split_result.pop(j)` pattern with a clean two-pass approach — first tag each block with its column assignment, then stable-sort by (column, y0).
3. **10.1c — Relax the UNKNOWN-only filter** (`layout_analyzer.py` L517): Allow splitting for PARAGRAPH and CODE_BLOCK types too, not just UNKNOWN — blocks may already be classified by the time this runs.
4. **10.1d — Add two-column regression test**: Parse `05_two_column.pdf`, verify that "Abstract" content appears before "1 Introduction" and "1 Introduction" before "3 Results" in the output markdown.

**Affected files:** `assembler.py`, `layout_analyzer.py`
**Verification:** `05_two_column.pdf` score ≥ 0.9

---

### Step 10.2 — Footnote Detection Fix (P0 — score: 0.4)

**Problem:** Closing braces `}` and code line numbers are misidentified as footnotes. The `_FOOTNOTE_PATTERN` regex (semantic_analyzer.py L398–401) matches too broadly — `[\[\(]?(\d{1,2}|...[a-z])[\]\)]?[\s:]` captures single digits or letters followed by whitespace, which fires on code like `10 }`.

**Sub-steps:**
1. **10.2a — Tighten `_FOOTNOTE_PATTERN`**: Require the marker to be enclosed in brackets `[1]` or `(1)` OR be a bare digit followed by `)` or `.` — not just whitespace. Change regex to: `^\s*(?:\[(\d{1,2})\]|\((\d{1,2})\)|(\d{1,2})[).]|([*†‡§¶]))\s+(.*)`.
2. **10.2b — Skip CODE_BLOCK blocks**: In `detect_footnotes()` (L422), add `BlockType.CODE_BLOCK` to the skip list so code blocks are never scanned for footnotes.
3. **10.2c — Cross-reference validation**: After collecting all footnote-candidate blocks on a page, verify that each marker ID has a corresponding superscript reference in the body text above `footnote_zone_y`. Discard orphan footnotes that have no matching body reference.
4. **10.2d — Font size check**: Add requirement that footnote block's dominant font size is ≤ body font size (footnotes are typically smaller text). Access via `block.text_block.lines[0].dominant_font_size`.
5. **10.2e — Add regression tests**: Verify `12_footnotes.pdf` correctly identifies real footnotes, `14_code_listings.pdf` has zero footnote blocks.

**Affected files:** `semantic_analyzer.py`
**Verification:** `12_footnotes.pdf` ≥ 0.8, `14_code_listings.pdf` no false footnotes

---

### Step 10.3 — Code Block Fencing (P1)

**Problem:** `_emit_code_block()` (emitter.py L169–173) already wraps in triple backticks and uses `block.code_language`, but the output shows no fences. The issue is that code blocks aren't being classified as `CODE_BLOCK` in the first place — `detect_code_blocks()` (layout_analyzer.py L436–490) requires ≥80% monospace spans, but LaTeX listings use a mix of monospace + keyword styling fonts.

**Sub-steps:**
1. **10.3a — Lower monospace threshold**: In `detect_code_blocks()` (L476), lower the `mono_ratio` threshold from 0.8 to 0.6, and add a secondary signal: if a block has ≥4 lines with consistent left-indent AND contains programming keywords (`def `, `{`, `}`, `//`, `#include`, `import `), classify as code regardless of mono_ratio.
2. **10.3b — Strip PDF line numbers**: In `_emit_code_block()` (emitter.py L169), before emitting, strip leading line numbers from each line: `re.sub(r'^\s*\d{1,3}\s+', '', line)` — but only if ALL lines in the block start with a sequential number pattern.
3. **10.3c — Improve language detection**: Expand `_guess_code_language()` (layout_analyzer.py L764–777) to also detect: `#!/bin/bash` or `$ ` prefix → `bash`, `SELECT`/`FROM` → `sql`, `<html>`/`<div>` → `html`.
4. **10.3d — Fix inline code in paragraphs**: In `_emit_inline_text()` (emitter.py L251–259), the backtick wrapping already exists but verify it's not being swallowed by emphasis wrapping. Add test: paragraph containing `pip install pd2md` should have backticks in output.

**Affected files:** `layout_analyzer.py`, `emitter.py`
**Verification:** `14_code_listings.pdf` — Python/JS/Shell blocks fenced with correct language tags

---

### Step 10.4 — Borderless Table Detection (P1)

**Problem:** Tables using booktabs style (horizontal rules only, no vertical lines) or pure whitespace alignment are emitted as raw text. `_detect_borderless_tables()` (layout_analyzer.py L360–367) is a placeholder that returns `[]`. The pdfplumber fallback strategies (table_extractor.py L83–105) try `"text"` strategy but only if blocks were already classified as TABLE — which they aren't, because the detector is empty.

**Sub-steps:**
1. **10.4a — Implement `_detect_borderless_tables()`** (`layout_analyzer.py` L360): Analyze each multi-line block — for each line, compute the x-positions of all inter-word gaps > 2× avg char width. If ≥3 consecutive lines share ≥2 gap positions (within ±5pt tolerance), flag the block as a `TableRegion(is_bordered=False)`.
2. **10.4b — Detect booktabs via horizontal-only rules**: In `detect_table_regions()` (L297), add a new branch: if `len(h_lines) >= 2` but `len(v_lines) == 0`, check if the horizontal lines bracket text content. If yes, create a `TableRegion` with the h_lines' y-range.
3. **10.4c — Add text-based cell extraction**: In `table_extractor.py`, add a new function `_extract_borderless_table(block: ContentBlock) -> TableData` that uses the block's span x-positions to determine column boundaries and parses cells by (row_y, col_x) assignment.
4. **10.4d — Wire fallback in `extract_tables_from_page()`**: After the pdfplumber extraction loop (L126), for any TABLE block that still has no `table_data`, attempt `_extract_borderless_table()` before falling back to paragraph.
5. **10.4e — Test**: Verify `04_complex_tables.pdf` — "Employee Directory" and "Benchmark Results" tables render as pipe tables.

**Affected files:** `layout_analyzer.py`, `table_extractor.py`
**Verification:** `04_complex_tables.pdf` booktabs tables → Markdown pipe tables

---

### Step 10.5 — Heading Hierarchy Improvement (P1 — score: 0.5)

**Problem:** `detect_headings()` (semantic_analyzer.py L50–124) uses fixed `_HEADING_RATIOS` (L42–47): 2×→H1, 1.5×→H2, 1.2×→H3, 1.05×→H4. This fails when a document uses subtle size differences (e.g., 14pt/13pt/12pt/11pt for H1/H2/H3/body). The numbering regex (L112) only fires if `is_bold or size_ratio >= 1.0`, missing non-bold numbered headings.

**Sub-steps:**
1. **10.5a — Rank-based heading levels**: Before the per-block loop, collect all unique font sizes across UNKNOWN blocks. Sort descending. Map each size to a heading level by rank position (largest=H1, 2nd=H2, etc.), capped at H4. Use this rank map instead of fixed ratios when size differences are subtle (all within 1.5× of body).
2. **10.5b — Improve numbered heading detection** (L110–117): Remove the `is_bold or size_ratio >= 1.0` guard for numbered patterns. If text matches `^\d+(\.\d+)*\s+\S`, derive level from dot count: 0 dots=H2, 1 dot=H3, 2 dots=H4. This covers `1 Introduction`→H2, `1.1 Methods`→H3, `1.1.1 Details`→H4.
3. **10.5c — Title detection**: Add a first-pass that finds the single largest-font block on page 0 that is ≤2 lines and marks it as H1 unconditionally (the document title). All other headings start at H2.
4. **10.5d — Monotonic enforcement post-pass**: After all headings are assigned, walk the heading sequence. If there's a jump > 1 level (e.g., H1→H3 with no H2), demote the lower heading by the gap (H3→H2).
5. **10.5e — Test**: `19_headings.pdf` — verify H1 is the title, section numbers map to correct levels, no level jumps > 1.

**Affected files:** `semantic_analyzer.py`
**Verification:** `19_headings.pdf` score ≥ 0.8

---

### Step 10.6 — Definition/Glossary Layout (P1 — score: 0.5)

**Problem:** `detect_definition_lists()` (semantic_analyzer.py L459–504) exists but converts definitions to `LIST_ITEM` with `-` marker, losing the term/definition structure. The detection requires `len(first_line.spans) >= 2` (L480), which misses definitions where the term is a standalone bold block followed by a separate description block.

**Sub-steps:**
1. **10.6a — Cross-block definition detection**: Instead of checking within a single block, scan pairs of consecutive blocks: if block N is a short bold-only paragraph (≤50 chars, `is_all_bold`) and block N+1 is a regular paragraph, merge them into a single definition block.
2. **10.6b — Add `DEFINITION` block type**: Add `DEFINITION = "definition"` to `BlockType` enum in `document.py`. Store the term in a new `definition_term` field on `ContentBlock`.
3. **10.6c — Definition emitter**: Add `_emit_definition()` in `emitter.py` that outputs:
   ```
   **Term**
   : Description text here
   ```
4. **10.6d — Preserve existing single-block detection**: Keep the current `detect_definition_lists()` logic but change output from `LIST_ITEM` to `DEFINITION` type.
5. **10.6e — Test**: `20_definitions.pdf` — verify terms are bold, descriptions follow with `: ` prefix.

**Affected files:** `document.py`, `semantic_analyzer.py`, `emitter.py`
**Verification:** `20_definitions.pdf` score ≥ 0.8

---

### 🏁 CHECKPOINT 10 — Quality Hardening Verified

| Criteria | Target |
|---|---|
| Two-column reading order | `05_two_column.pdf` ≥ 0.9 |
| Footnotes correct | `12_footnotes.pdf` ≥ 0.8, no false positives in code |
| Code blocks fenced | `14_code_listings.pdf` has ` ```python ``` ` fences |
| Borderless tables | `04_complex_tables.pdf` booktabs → pipe tables |
| Heading hierarchy | `19_headings.pdf` ≥ 0.8 |
| Definition lists | `20_definitions.pdf` ≥ 0.8 |
| **Batch average** | **≥ 0.85** (up from 0.79) |
| **No regressions** | All previously 1.0-score PDFs stay at 1.0 |

---

## 8. Phase 11 — Real-World PDF Stress Testing (PLANNED)

> **Goal:** Validate the converter against 20+ wild PDFs from diverse sources. Fix regressions discovered. Target: **≥0.8 on 80% of real-world PDFs.**

**Sub-steps:**
1. **11.1 — Curate test corpus**: Collect 20+ PDFs from: arxiv papers (2-column, math-heavy), government reports (tables, headers), textbook chapters (figures, footnotes, indices), corporate whitepapers (branded headers, watermarks), resumes/CVs (multi-column, icons).
2. **11.2 — Batch benchmark run**: Run `pd2md batch` on the corpus, collect scores and timing. Produce a comparison table: filename, pages, score, time, top issue.
3. **11.3 — Triage failures**: Categorize failures into: (a) already-known gaps from Phase 10, (b) new layout issues, (c) encoding/font issues, (d) edge cases. Prioritize by frequency.
4. **11.4 — Targeted fixes**: For the top 5 failure categories, implement fixes in the relevant pipeline layer. Each fix gets a dedicated regression test PDF.
5. **11.5 — Regression gate**: Re-run the full batch (21 synthetic + 20 real-world). No previously-passing PDF may drop below its prior score.

---

## 9. Phase 12 — Math Equation Handling (PLANNED)

> **Goal:** Detect math equations and emit them in a useful format (LaTeX where possible, image fallback otherwise).

**Sub-steps:**
1. **12.1 — Equation region detection**: In `layout_analyzer.py`, detect equation blocks by: (a) lines containing Symbol/Math fonts (CMR, CMMI, CMSY, etc.), (b) centered short blocks with unusual character distributions (many Greek letters, operators, subscripts).
2. **12.2 — Simple inline math recovery**: For inline math (single symbols like α, β, ∑, ∫ within paragraphs), map Unicode math characters to LaTeX equivalents and wrap in `$...$`.
3. **12.3 — Display equation extraction**: For display equations (centered, standalone blocks), attempt to reconstruct LaTeX from the glyph sequence using a character-to-LaTeX mapping table. Wrap in `$$...$$`.
4. **12.4 — Image fallback**: When reconstruction fails (complex equations with matrices, fractions, etc.), render the equation region as a cropped PNG image using `page.get_pixmap(clip=eq_bbox)` and embed as `![equation](images/eq_N.png)`.
5. **12.5 — Test**: `13_math_equations.pdf` — simple equations appear as LaTeX, complex ones as images.

---

## 10. Phase 13 — ML Enhancer Plugins (PLANNED)

> **Goal:** Plug in GPU-accelerated ML models for users who have them, keeping the CPU pipeline as default.

**Sub-steps:**
1. **13.1 — Enhancer interface**: Define `backend/app/enhancers/base.py` with the `Enhancer` protocol: `can_run() -> bool` (checks GPU/model availability), `enhance(page: PageResult) -> PageResult`.
2. **13.2 — Auto-discovery**: On startup, scan `enhancers/` directory, import all modules, call `can_run()`. Log which enhancers are active. Store in `config.active_enhancers`.
3. **13.3 — Table enhancer** (`enhancers/table_transformer.py`): Use Microsoft's TableTransformer (DETR-based) for table detection. Replaces `detect_table_regions()` when available. Dependency: `transformers`, `torch`.
4. **13.4 — Layout enhancer** (`enhancers/surya_layout.py`): Use Surya for layout segmentation (columns, figures, headers). Replaces `detect_columns()` + `detect_code_blocks()`. Dependency: `surya-ocr`.
5. **13.5 — Math enhancer** (`enhancers/nougat_math.py`): Use Meta's Nougat for equation-to-LaTeX conversion. Replaces the heuristic math recovery from Phase 12.
6. **13.6 — Orchestrator integration**: In `orchestrator.py`, after each rule-based layer, check if an enhancer exists for that layer and call `enhance()` to override/augment results.

---

## 11. Phase 14 — Packaging & Distribution (PLANNED)

> **Goal:** Make PD2MD installable and deployable by anyone.

**Sub-steps:**
1. **14.1 — PyPI packaging**: Finalize `pyproject.toml` metadata (description, classifiers, URLs), add `README.md` with badges (version, license, Python version), publish to PyPI via `python -m build` + `twine upload`.
2. **14.2 — Docker image**: Create `Dockerfile` (Python 3.12-slim base, pip install, expose port 8000). Add `docker-compose.yml` for one-command startup. Publish to Docker Hub / GitHub Container Registry.
3. **14.3 — GitHub releases**: Set up GitHub Actions CI: run tests on push, build wheel on tag, create GitHub Release with changelog and wheel artifact.
4. **14.4 — Documentation site**: Generate docs from docstrings using mkdocs-material. Sections: Quick Start, CLI Reference, API Reference, Architecture, Contributing.
5. **14.5 — README polish**: Add demo GIF/video, feature comparison table vs. marker/pymupdf4llm, installation instructions for all platforms.

---

## 12. Phase 15 — Productization (PLANNED)

> **Goal:** Turn PD2MD into a monetizable product (Fiverr gig, hosted API, or SaaS).

**Sub-steps:**
1. **15.1 — Landing page**: Build a single-page marketing site with: hero section (before/after PDF→MD demo), feature grid, pricing tiers, CTA buttons. Deploy on Vercel/Netlify.
2. **15.2 — Demo video**: Record a 60-second screen recording showing: drag PDF → see progress → download clean Markdown. Use for Fiverr gig thumbnail and landing page.
3. **15.3 — Hosted API**: Deploy the FastAPI backend on a VPS (DigitalOcean/Railway). Add API key authentication, rate limiting (10 req/min free tier), and usage tracking.
4. **15.4 — Fiverr gig setup**: Create gig: "I will convert your PDF to clean Markdown for AI/LLM use". Tiers: Basic (1 PDF, $5), Standard (5 PDFs + quality report, $15), Premium (batch + custom formatting, $30).
5. **15.5 — Feedback loop**: Collect converted PDFs from customers (with permission) to expand the real-world test corpus (Phase 11) and continuously improve quality.

