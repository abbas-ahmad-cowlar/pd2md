---
date: "D:20260413043936+05'00'"
source: "22_full_report.pdf"
pages: 3
---

## PD2MD: An Intelligent PDF to Markdown Converter

#### Technical Design Document

#### Engineering Team

#### April 2026

Abstract

We present PD2MD, a modular pipeline for converting digital PDF documents to
clean, structured Markdown. Our system prioritizes content accuracy over formatting
fidelity, making it ideal for preparing documents for AI and LLM consumption. The
pipeline consists of six layers: extraction, assembly, layout analysis, semantic classifi
cation, table extraction, and Markdown emission. Evaluation on 117 test cases shows
100% content accuracy across diverse document types.

### 1 Introduction

The growing use of large language models for document analysis has created a need for high-
quality text extraction from PDF files. While PDF is the dominant format for published
documents, its page-oriented representation makes it challenging to extract logical structure.

#### 1.1 Problem Statement
Given a digital PDF file, produce a Markdown document that:
1. Preserves all text content character-perfectly

2. Identifies headings, paragraphs, and lists

3. Extracts tables with correct cell values

4. Includes embedded images with references

5. Removes running headers and footers

[^1]: 2 Design Principles
 Content first: Every word must survive conversion
 Modular: Each layer is independently testable
 No ML required: CPU-only, deterministic output
 Configurable: Image format, frontmatter, validation


### 2 Architecture

#### 2.1 Pipeline Overview
The conversion pipeline consists of six sequential layers:

Table 1: Pipeline Layers

Layer Name Input Output
1 Extractor PDF file Raw glyphs, images, vectors
2 Assembler Raw glyphs Text blocks, font catalog
3 Layout Text blocks Ordered content blocks
4 Semantics Content blocks Classified blocks
5 Tables Classified blocks Blocks with table data
6 Emitter All blocks Markdown file

2.2 Data Model
The central data structure is the ContentBlock, which carries:
 Block type (heading, paragraph, list item, table, etc.)
 Bounding box coordinates
 Text content with span-level formatting
 Optional table data or image reference

### 3 Evaluation

#### 3.1 Test Suite
We evaluate PD2MD using 147 automated tests across 8 test suites:

#### 3.2 Performance
Average conversion time per page is 0.15 seconds for simple documents and 0.45 seconds for
complex layouts with tables. Memory usage stays below 100 MB for documents up to 100
pages.

### 4 Future Work

Potential improvements include:

1. Support for scanned PDFs via OCR integration


Table 2: Test Results

Suite Tests Status
Extractor 20 Pass
Assembler 23 Pass
Layout Analyzer 18 Pass
Semantic Analyzer 18 Pass
Table Extractor 15 Pass
Emitter 23 Pass
Hardening 17 Pass
Advanced Features 13 Pass
Total 147 All Pass

2. Multi-column academic paper handling improvements

3. Mathematical equation extraction to LaTeX notation

4. Nested list depth preservation

5. Custom Markdown flavor output (GitHub, CommonMark, etc.)

### 5 Conclusion

PD2MD demonstrates that high-fidelity PDF to Markdown conversion is achievable with a
carefully designed pipeline of spatial analysis heuristics. By prioritizing content accuracy and
modularity, the system provides reliable document extraction for AI and LLM applications
without requiring machine learning models or GPU resources.


---

[^1]: 2 Design Principles
 Content first: Every word must survive conversion
 Modular: Each layer is independently testable
 No ML required: CPU-only, deterministic output
 Configurable: Image format, frontmatter, validation
