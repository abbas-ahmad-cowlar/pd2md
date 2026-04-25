---
date: "D:20260413043824+05'00'"
source: "12_footnotes.pdf"
pages: 1
---

## Document with Footnotes

#### Footnote Tester

#### April 13, 2026

### 1 Introduction

Footnotes are commonly used in academic writing`1` to provide supplementary information
without cluttering the main text.

### 2 Technical Details

The PDF format stores footnotes as regular text positioned at the bottom of the page`2`. This
means the converter must use spatial analysis to identify them.
Our approach detects footnotes by looking for small-font text blocks near the bottom
margin`3`. These blocks are then tagged as footnotes in the intermediate representation.

### 3 Limitations

Multi-page footnotes`4` present additional challenges.

### 4 Conclusion

Footnote handling is important for academic document conversion. The key signals are:
small font size, bottom-of-page positioning, and superscript reference markers in the body
text.

[^1]: This is a simple footnote that provides additional context.

[^2]: PDF does not have a semantic concept of “footnotes” — they are simply text blocks positioned near the page bottom.

[^3]: Specifically, we check for text blocks where the font size is less than 80% of the body font size and the vertical position is in the bottom 15% of the page.

[^4]: Footnotes that are too long to fit on a single page will overflow to the next page. This is a known edge case that our current implementation does not handle perfectly.


---

[^1]: This is a simple footnote that provides additional context.
[^2]: PDF does not have a semantic concept of “footnotes” — they are simply text blocks positioned near the page bottom.
[^3]: Specifically, we check for text blocks where the font size is less than 80% of the body font size and the vertical position is in the bottom 15% of the page.
[^4]: Footnotes that are too long to fit on a single page will overflow to the next page. This is a known edge case that our current implementation does not handle perfectly.
