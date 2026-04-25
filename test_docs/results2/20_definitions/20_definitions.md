---
date: "D:20260413043933+05'00'"
source: "20_definitions.pdf"
pages: 2
---

## Technical Glossary

#### Documentation Team

#### April 13, 2026

### 1 Core Concepts

Glyph The smallest unit of text in a PDF. Represents a single character with position, font,

and size metadata.

Content Block A group of related text lines that form a logical unit such as a paragraph,

heading, or list item.

Font Catalog A registry of all fonts used in a document, including the identified body font

and heading fonts.

Reading Order The sequence in which content blocks should be read to reconstruct the

logical flow of the document.

Intermediate Representation The structured data model that connects all pipeline lay-

ers, containing blocks, their types, and metadata.

### 2 Pipeline Stages

Extraction Layer 1. Raw PDF data retrieval using PyMuPDF.

Assembly Layer 2. Character-to-block construction.

Layout Analysis Layer 3. Spatial structure detection.

Semantic Analysis Layer 4. Content type classification.

Table Extraction Layer 5. Structured table recovery.

Emission Layer 6. Markdown text generation.


### 3 File Formats

PDF Portable Document Format. Page-oriented, position-based rendering.

Markdown Lightweight semantic markup. Line-oriented, structure-based.

YAML YAML Ain’t Markup Language. Used for frontmatter metadata.

ZIP Archive format for bundling Markdown output with extracted images.
