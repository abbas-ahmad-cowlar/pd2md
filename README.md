<!-- ┌──────────────────────────────────────────────────────────────────┐ -->
<!-- │  HERO IMAGE PLACEHOLDER                                           │ -->
<!-- │  Drop a banner / UI screenshot at docs/hero.png and it will       │ -->
<!-- │  render below. Recommended: a shot of the drag-and-drop web UI    │ -->
<!-- │  mid-conversion, or a side-by-side PDF → Markdown frame.          │ -->
<!-- └──────────────────────────────────────────────────────────────────┘ -->

<p align="center">
  <img src="docs/hero.png" alt="PD2MD — PDF to Markdown" width="820"
       onerror="this.style.display='none'">
</p>

<h1 align="center">PD2MD</h1>

<p align="center">
  <strong>Turn digital PDFs into clean, structured Markdown — headings, lists, tables, and images intact.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12+-blue.svg">
  <img alt="Tests" src="https://img.shields.io/badge/tests-149%20passing-brightgreen.svg">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg">
  <img alt="Built with" src="https://img.shields.io/badge/built%20with-PyMuPDF%20%7C%20pdfplumber%20%7C%20FastAPI-orange.svg">
</p>

---

## What it does

PD2MD is a PDF → Markdown conversion engine built for **content fidelity**. Instead of
dumping a flat stream of text, it rebuilds the *structure* of a document: it infers heading
levels from typography, reconstructs reading order across multi-column layouts, strips
running headers/footers, detects ordered and nested lists, extracts real tables into
GitHub-flavored Markdown, and pulls out embedded images with references.

It ships three ways to use it:

- a **CLI** for single files and batches,
- a **FastAPI web app** with a drag-and-drop UI, live progress, preview, and ZIP download, and
- an importable **Python pipeline** you can call directly.

> **Scope:** PD2MD targets *digital* (text-based) PDFs. Scanned / image-only pages are detected
> but not OCR'd — that's out of scope for now (see [Roadmap](#roadmap)).

---

## The 6-stage pipeline

Every conversion flows through six deterministic, independently-testable layers
(`backend/app/pipeline/`). Each stage hardens against per-page failures so one bad
page never sinks the whole document.

```
  PDF
   │
   ▼
 ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
 │ extract  │──▶│ assemble │──▶│  layout  │──▶│ semantic │──▶│  tables  │──▶│   emit   │──▶ Markdown
 └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

| # | Stage | Module | Responsibility |
|---|-------|--------|----------------|
| 1 | **extract**  | `extractor.py`         | Pull raw glyphs, images, vector paths, and document metadata via **PyMuPDF**. |
| 2 | **assemble** | `assembler.py`         | Group glyphs → words → lines → blocks; build a font catalog (body vs. heading fonts). |
| 3 | **layout**   | `layout_analyzer.py`   | Detect columns & reading order, find figure/table regions, mask running headers/footers. |
| 4 | **semantic** | `semantic_analyzer.py` | Classify each block: heading level, paragraph, list item, code, blockquote, footnote. |
| 5 | **tables**   | `table_extractor.py`   | Recover table grid structure with **pdfplumber** and render Markdown tables. |
| 6 | **emit**     | `emitter.py`           | Write Markdown + YAML frontmatter + image refs, and package an output ZIP. |

A final **validation** pass (`validator.py`) scores the conversion and reports issues
(empty blocks, unclassified content, dropped text) so quality is measurable, not assumed.

---

## Before / after

Below is a real table lifted from a 34-page scientific PDF (a photoelectrochemistry
literature review). In the source it's a borderless, six-column comparison grid embedded
in running prose — exactly the kind of structure a naive text dump flattens into noise.

**Before** — typical flat extraction collapses cells into a run-on line:

```text
GaInP₂/GaAs (III-V) ~1.8 / ~1.4 ≈12.4–19 17%; 20 h High cost, photo-corrosion (Moss et al., 2021)
α-Fe₂O₃ (Hematite) 1.9–2.32 ≤1–2* 0%; 1000 h ... Short carrier diffusion length (Ameen et al., 2025) ...
```

**After** — PD2MD reconstructs the grid (subscripts like `Fe₂O₃`, superscript units, and
column boundaries preserved), straight from `output/`:

| Material                | Bandgap (eV) | Best STH (%)    | Stability               | Key Challenge                  | Reference                                  |
| ----------------------- | ------------ | --------------- | ----------------------- | ------------------------------ | ------------------------------------------ |
| GaInP₂/GaAs (III-V)     | ~1.8 / ~1.4  | ≈12.4–19        | 17%; 20 h               | High cost, photo-corrosion     | (Moss et al., 2021)                        |
| α-Fe₂O₃ (Hematite)      | 1.9–2.32     | ≤1–2*           | 0%; 1000 h (Si- backed) | Short carrier diffusion length | (Ameen et al., 2025) (Moss et al., 2021)   |
| BiVO₄                   | ~2.4         | ≈3–5*           | Hours to days           | Poor carrier transport         | (Moss et al., 2021) (Ahmed & Dincer, 2019) |
| TiO₂ (Anatase: Rutile)  | ~2.6–3.2     | < 1*            | Stable (hours)          | Wide bandgap, UV-only          | (Moss et al., 2021)                        |
| Cu₂O                    | ~2.0         | ≈3 (with BiVO₄) | Limited                 | Photo-corrosion                | (Moss et al., 2021)                        |
| a-Si tandem (multi-jn.) | Variable     | ≈9.5–12         | 10%; short-term         | Stability, degradation         | (Moss et al., 2021) (Ahmed & Dincer, 2019) |

Every document also gets YAML frontmatter inferred from its metadata:

```yaml
---
author: "Un-named"
date: "D:20260313094854+05'00'"
source: "literature_review_revised.pdf"
pages: 34
---
```

---

## Features

- 📄 **Digital PDF → clean Markdown** with structure, not just text
- 🔤 **Typography-aware heading hierarchy** (H1–H6 inferred from font size/weight)
- 🧱 **Multi-column reading-order reconstruction**
- 🧹 **Running header/footer detection & removal**
- 🔢 **Ordered, unordered & nested list detection**
- 📊 **Table extraction** to GitHub-flavored Markdown (via pdfplumber)
- 🖼️ **Image extraction** (PNG or JPEG) with inline Markdown references
- 💬 **Code blocks, blockquotes & footnotes** detection
- 🧾 **YAML frontmatter** (title, author, date, source, page count)
- ✅ **Conversion quality report** with per-issue scoring
- 🖥️ **Web UI**: drag-and-drop, multi-file batch (up to 20), live progress, preview & ZIP download
- ⌨️ **CLI**: single + batch conversion, progress bar, JSON batch report
- 🛡️ **Hardened**: input validation, per-page error isolation, size & timeout limits

---

## Install

Requires **Python 3.12+**.

```bash
git clone https://github.com/abbas-ahmad-cowlar/pd2md.git
cd pd2md

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev]"            # installs the `pd2md` command + dev/test deps
```

---

## Run it

### CLI

```bash
# Convert a single PDF (output lands in ./output/<name>/)
pd2md convert report.pdf

# Choose an output dir and image format
pd2md convert report.pdf -o ./out/ --image-format jpeg

# Batch-convert a folder of PDFs, with a JSON summary report
pd2md batch ./pdfs/ -o ./results/

# Print a detailed quality report after conversion
pd2md convert report.pdf --report
```

> No install? Run the module directly: `python -m backend.app.cli convert report.pdf`

### Web UI (FastAPI, port 8000)

```bash
uvicorn backend.app.main:app --port 8000
# then open http://127.0.0.1:8000
```

Drag PDFs onto the dropzone, watch live progress, preview the Markdown, and download the
`.md` file or the full `.zip` package (Markdown + extracted images).

---

## Tests

```bash
pytest -q
```

```
149 passed
```

The suite covers every pipeline layer end-to-end — extraction, assembly, layout, semantics,
tables, emission, plus hardening/edge-case tests — against a corpus of synthetic LaTeX-built
PDFs in `test_docs/`.

---

## Tech stack

| Area | Tools |
|------|-------|
| PDF extraction | [PyMuPDF](https://pymupdf.readthedocs.io/) (glyphs, images, vectors, metadata) |
| Table recovery | [pdfplumber](https://github.com/jsvine/pdfplumber) |
| API / server | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Models / config | [Pydantic](https://docs.pydantic.dev/) + pydantic-settings |
| Images | [Pillow](https://python-pillow.org/) |
| Frontend | Vanilla HTML / CSS / JavaScript (no framework) |
| Testing | [pytest](https://docs.pytest.org/) — 149 tests |

---

## Project structure

```
pd2md/
├── backend/
│   ├── app/
│   │   ├── pipeline/        # 6-stage engine: extract → assemble → layout → semantic → tables → emit
│   │   ├── models/          # Pydantic document model (blocks, pages, font catalog)
│   │   ├── cli.py           # `pd2md` command-line interface
│   │   ├── main.py          # FastAPI app + REST API
│   │   └── config.py        # settings (PD2MD_* env vars)
│   └── tests/               # 149 pytest tests
├── frontend/                # drag-and-drop web UI (HTML/CSS/JS)
└── test_docs/               # synthetic LaTeX-built PDF corpus for testing
```

---

## Roadmap

These are **not implemented today** and are listed honestly as future work:

- **OCR for scanned PDFs** — image-only pages are currently detected but skipped.
- **Math / equation recovery** to LaTeX.
- **Optional ML post-processing layer** — the pipeline is fully deterministic and heuristic
  today; there are no model/LLM hooks in the orchestrator.

---

## License

[MIT](LICENSE) © 2026 Syed Abbas Ahmad
