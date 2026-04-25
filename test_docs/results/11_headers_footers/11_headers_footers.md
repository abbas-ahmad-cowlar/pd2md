---
date: "D:20260413043823+05'00'"
source: "11_headers_footers.pdf"
pages: 3
---

## Document with Headers and Footers

#### Header/Footer Test

#### April 13, 2026

### 1 Page 1 Content

This document has running headers (“PD2MD Technical Manual” on the left, “Version 1.0”
on the right) and footers (page number centered, “Confidential” on the right). The converter
should detect these repeating elements across pages and exclude them from the body content
in the Markdown output.
The header and footer text should not appear as paragraphs in the converted Markdown.
Only the body content within each section should be preserved.


### 2 Page 2 Content

This is the second page of the document. The same headers and footers appear here, demon
strating the cross-page repetition pattern that the converter uses to identify running headers
and footers.
Content on this page should flow naturally after the content from page 1 in the Markdown
output, without any header or footer text interrupting the flow.


### 3 Page 3 Content

The third and fni al page continues with the same layout. By having three pages, we provide
enough data for the cross-page header/footer detection algorithm to work reliably. The
algorithm requires at least two pages to identify patterns.
All body content from all three pages should appear in the correct order in the final
Markdown output.
