---
date: "D:20260413043805+05'00'"
source: "08_figures_captions.pdf"
pages: 2
---

## Document with Figures and Captions

#### Visual Content Team

#### April 13, 2026

### 1 Introduction

This document tests the handling of figure environments and captions. While we cannot
include actual images in this test LaTeX file without external assets, we test caption text
extraction and figure numbering.

### 2 Results

Figure 1: Architecture diagram of the PD2MD conversion pipeline showing the six processing
layers from extraction through emission.

The architecture shown in Figure 1 demonstrates the modular design of our system. Each
layer operates independently, communicating through a well-defined intermediate represen
tation.


Figure 2: Performance comparison across different PDF complexity levels. Simple documents
convert in under 0.5 seconds, while complex multi-column layouts require up to 3.2 seconds.

As shown in Figure 2, performance scales linearly with document complexity for most
cases.

Figure 3: Error rate by document category. Academic papers (2.1%), business reports
(1.4%), and technical manuals (3.7%).

### 3 Discussion

The figure captions above should appear in the Markdown output. The converter should
identify caption text and include it near the figure references.
