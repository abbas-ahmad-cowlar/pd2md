---
date: "D:20260413043801+05'00'"
source: "05_two_column.pdf"
pages: 1
---

Two-Column Research Paper
Dr. Robert Chen
2026
Abstract
This paper presents a two-column layout com-
monly used in academic publications. The con-
verter should correctly identify column bound-
aries and reconstruct the reading order so that
text flows from the left column to the right col
umn on each page, not interleaving lines from
both columns.
1 Introduction
Academic papers frequently use two-column lay
outs to maximize information density on each
page. This presents a challenge for PDF extrac
tion because the converter must determine which
text blocks belong to which column.
The spatial analysis must consider the hori
zontal gap between columns as a separator. Text
blocks on the left side of the gap should be read
first, followed by text blocks on the right side.
2 Methodology
Our approach uses a vertical split-point detec
tor. We analyze the distribution of text block
x-coordinates and identify a gap region near the
horizontal center of the page. Blocks to the left
of this gap are assigned to column 1, and blocks
to the right are assigned to column 2.
Within each column, blocks are ordered top
to-bottom. The final reading order concatenates
column 1 followed by column 2 for each page.

#### Dr. Maria Lopez

3 Results
Testing on 500 academic papers showed that our
column detection achieves 97.3% accuracy in cor-
rectly ordering text blocks. The most common
failure case involves wide equations or figures
that span both columns.
4 Conclusion
Two-column layout handling is essential for aca
demic paper conversion. Our spatial analysis ap-
p
roach provides robust column detection without
requiring machine learning or training data.
