---
date: "D:20260413043828+05'00'"
source: "15_mixed_stress.pdf"
pages: 2
---

## Mixed Formatting Stress Test

#### QA Team

#### April 13, 2026

### 1 Paragraph with Everything

This paragraph has bold text, italic text, inline code, a reference to Section 2, and some
numbers like 3.14159 and 2.71828. It also includes special characters: ampersand (&),
percent (5%), dollar sign ($100), and various punctuation marks: semicolons; colons: dashes

- and ellipses. . .

### 2 Lists Followed by Paragraphs

Here is a list:

 Bold list item with explanation text

 Italic list item with different formatting

 Code list item showing a command

And now we continue with a regular paragraph that follows the list. The converter should
correctly separate the list from this paragraph.

### 3 Table Followed by Text

Metric Value
Precision 94.2%
Recall 91.7%
F1 Score 92.9%

The table above shows our evaluation metrics. As you can see, the system achieves high
precision and recall across all test cases.


### 4 Multiple Paragraphs

First paragraph of this section. It contains multiple sentences that should be joined into a
single paragraph in the Markdown output.
Second paragraph of this section. This tests that paragraph breaks are correctly detected
based on vertical spacing between text blocks.
Third paragraph. Short but distinct from the previous paragraphs.
