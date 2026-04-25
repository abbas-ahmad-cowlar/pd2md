---
date: "D:20260413043755+05'00'"
source: "01_simple_article.pdf"
pages: 1
---

## A Simple Article

#### Jane Smith

#### April 2026

### 1 Introduction

This is a simple article to test basic text extraction. The converter should correctly identify
the title, author, date, section headings, and body paragraphs.
Each paragraph should be separated by a blank line in the Markdown output, and the
text content should be character-perfect with no missing words or garbled output.

### 2 Background

PDF documents store text as positioned glyphs rather than flowing paragraphs. This means
a converter must reconstruct the logical reading order from spatial coordinates. Our pipeline
uses adaptive gap analysis to group glyphs into words, lines, and blocks.

### 3 Conclusion

If this document converts correctly, the basic extraction and assembly pipeline is working
as expected. The key metrics are: no missing text, correct paragraph breaks, and proper
section heading identification.
