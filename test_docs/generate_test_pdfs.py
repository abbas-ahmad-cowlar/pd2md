"""
Generate 22 diverse LaTeX test documents and compile to PDF.

Each document tests a different aspect of PDF → Markdown conversion:
  1. Simple article           12. Footnotes & endnotes
  2. Multi-section report     13. Mathematical equations
  3. Nested lists             14. Code listings
  4. Complex tables           15. Mixed formatting stress
  5. Two-column layout        16. Long paragraphs
  6. Bibliography/references  17. Blockquotes / epigraphs
  7. Title page + abstract    18. Nested tables
  8. Figures with captions    19. Multi-level headings
  9. Enumerated & itemized    20. Definition lists
  10. Bold/italic/underline   21. Hyperlinks & URLs
  11. Headers & footers       22. Full technical report
"""

import os
import subprocess
import sys
from pathlib import Path

LATEX_DIR = Path(__file__).parent / "latex"
PDF_DIR = Path(__file__).parent / "pdfs"

DOCUMENTS = {}

# ──────────────────────────────────────────────────────────────
# 1. Simple Article
# ──────────────────────────────────────────────────────────────
DOCUMENTS["01_simple_article"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{A Simple Article}
\author{Jane Smith}
\date{April 2026}
\begin{document}
\maketitle

\section{Introduction}
This is a simple article to test basic text extraction. The converter should
correctly identify the title, author, date, section headings, and body paragraphs.

Each paragraph should be separated by a blank line in the Markdown output, and
the text content should be character-perfect with no missing words or garbled output.

\section{Background}
PDF documents store text as positioned glyphs rather than flowing paragraphs.
This means a converter must reconstruct the logical reading order from spatial
coordinates. Our pipeline uses adaptive gap analysis to group glyphs into words,
lines, and blocks.

\section{Conclusion}
If this document converts correctly, the basic extraction and assembly pipeline
is working as expected. The key metrics are: no missing text, correct paragraph
breaks, and proper section heading identification.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 2. Multi-Section Report
# ──────────────────────────────────────────────────────────────
DOCUMENTS["02_multisection_report"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Quarterly Performance Report}
\author{Analytics Department}
\date{Q1 2026}
\begin{document}
\maketitle
\tableofcontents
\newpage

\section{Executive Summary}
This report summarizes the key performance indicators for Q1 2026. Revenue
increased by 15\% year-over-year, while operating costs decreased by 3\%.

\section{Financial Overview}
\subsection{Revenue Analysis}
Total revenue reached \$4.2 million, driven primarily by enterprise subscriptions.
The SaaS segment contributed 68\% of total revenue, up from 61\% in Q4 2025.

\subsection{Cost Structure}
Operating expenses totaled \$2.8 million. The largest categories were:
personnel (52\%), infrastructure (23\%), and marketing (15\%).

\subsection{Profitability}
Net income was \$1.1 million, representing a 26\% margin. This is a significant
improvement from the 19\% margin achieved in Q1 2025.

\section{Product Metrics}
\subsection{User Growth}
Monthly active users grew to 142,000, a 28\% increase from the previous quarter.
Daily active users averaged 67,000.

\subsection{Engagement}
Average session duration increased from 8.2 minutes to 11.4 minutes. Feature
adoption rates for the new dashboard exceeded 73\%.

\section{Outlook}
Based on current trends, we project Q2 revenue of \$4.8 million and continued
margin expansion. Key risks include rising infrastructure costs and competitive
pressure in the mid-market segment.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 3. Nested Lists
# ──────────────────────────────────────────────────────────────
DOCUMENTS["03_nested_lists"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Nested List Structures}
\author{Test Suite}
\begin{document}
\maketitle

\section{Bullet Lists}
\begin{itemize}
    \item First level item A
    \item First level item B
    \begin{itemize}
        \item Second level item B.1
        \item Second level item B.2
        \begin{itemize}
            \item Third level item B.2.a
            \item Third level item B.2.b
        \end{itemize}
        \item Second level item B.3
    \end{itemize}
    \item First level item C
\end{itemize}

\section{Numbered Lists}
\begin{enumerate}
    \item Install Python 3.12 or later
    \item Create a virtual environment
    \begin{enumerate}
        \item Run: python -m venv .venv
        \item Activate: source .venv/bin/activate
    \end{enumerate}
    \item Install dependencies
    \begin{enumerate}
        \item Core: pip install pymupdf pdfplumber
        \item Dev: pip install pytest ruff
    \end{enumerate}
    \item Run the test suite
    \item Deploy to production
\end{enumerate}

\section{Mixed Lists}
\begin{itemize}
    \item Unordered parent item
    \begin{enumerate}
        \item Ordered child 1
        \item Ordered child 2
    \end{enumerate}
    \item Another unordered item
    \begin{itemize}
        \item Nested bullet A
        \item Nested bullet B
    \end{itemize}
\end{itemize}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 4. Complex Tables
# ──────────────────────────────────────────────────────────────
DOCUMENTS["04_complex_tables"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{multirow}
\title{Complex Table Structures}
\author{Test Suite}
\begin{document}
\maketitle

\section{Basic Table}
\begin{table}[h]
\centering
\caption{Employee Directory}
\begin{tabular}{|l|l|c|r|}
\hline
\textbf{Name} & \textbf{Department} & \textbf{Years} & \textbf{Salary} \\
\hline
Alice Johnson & Engineering & 5 & \$95,000 \\
Bob Williams & Marketing & 3 & \$72,000 \\
Carol Davis & Engineering & 8 & \$115,000 \\
David Brown & Finance & 2 & \$68,000 \\
Eve Wilson & Engineering & 6 & \$105,000 \\
\hline
\end{tabular}
\end{table}

\section{Booktabs Table}
\begin{table}[h]
\centering
\caption{Benchmark Results}
\begin{tabular}{lrrr}
\toprule
\textbf{Algorithm} & \textbf{Time (ms)} & \textbf{Memory (MB)} & \textbf{Accuracy} \\
\midrule
Linear Search & 1,245 & 12.3 & 100.0\% \\
Binary Search & 8 & 12.3 & 100.0\% \\
Hash Table & 3 & 45.7 & 100.0\% \\
Neural Net & 156 & 234.5 & 98.7\% \\
\bottomrule
\end{tabular}
\end{table}

\section{Multi-row Table}
\begin{table}[h]
\centering
\caption{Course Schedule}
\begin{tabular}{|l|l|l|l|}
\hline
\textbf{Day} & \textbf{Time} & \textbf{Course} & \textbf{Room} \\
\hline
\multirow{2}{*}{Monday} & 9:00 AM & Mathematics & A101 \\
 & 2:00 PM & Physics & B205 \\
\hline
\multirow{3}{*}{Wednesday} & 9:00 AM & Chemistry & C310 \\
 & 11:00 AM & Biology & D102 \\
 & 3:00 PM & Computer Science & E401 \\
\hline
\end{tabular}
\end{table}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 5. Two-Column Layout
# ──────────────────────────────────────────────────────────────
DOCUMENTS["05_two_column"] = r"""
\documentclass[12pt,twocolumn]{article}
\usepackage[margin=0.75in]{geometry}
\title{Two-Column Research Paper}
\author{Dr.\ Robert Chen \and Dr.\ Maria Lopez}
\date{2026}
\begin{document}
\maketitle

\begin{abstract}
This paper presents a two-column layout commonly used in academic publications.
The converter should correctly identify column boundaries and reconstruct the
reading order so that text flows from the left column to the right column on
each page, not interleaving lines from both columns.
\end{abstract}

\section{Introduction}
Academic papers frequently use two-column layouts to maximize information density
on each page. This presents a challenge for PDF extraction because the converter
must determine which text blocks belong to which column.

The spatial analysis must consider the horizontal gap between columns as a
separator. Text blocks on the left side of the gap should be read first, followed
by text blocks on the right side.

\section{Methodology}
Our approach uses a vertical split-point detector. We analyze the distribution
of text block x-coordinates and identify a gap region near the horizontal center
of the page. Blocks to the left of this gap are assigned to column 1, and blocks
to the right are assigned to column 2.

Within each column, blocks are ordered top-to-bottom. The final reading order
concatenates column 1 followed by column 2 for each page.

\section{Results}
Testing on 500 academic papers showed that our column detection achieves 97.3\%
accuracy in correctly ordering text blocks. The most common failure case involves
wide equations or figures that span both columns.

\section{Conclusion}
Two-column layout handling is essential for academic paper conversion. Our
spatial analysis approach provides robust column detection without requiring
machine learning or training data.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 6. Bibliography
# ──────────────────────────────────────────────────────────────
DOCUMENTS["06_bibliography"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Research with References}
\author{Academic Author}
\begin{document}
\maketitle

\section{Introduction}
Machine learning has transformed many fields. Convolutional neural networks
achieved breakthrough results in image recognition [1]. Transformer architectures
revolutionized natural language processing [2], leading to large language models
that can perform complex reasoning tasks [3].

\section{Related Work}
The challenge of PDF parsing has been studied extensively. Early work focused on
rule-based approaches [4], while more recent methods employ deep learning for
document layout analysis [5]. Our approach combines traditional heuristics with
adaptive thresholds, avoiding the need for training data.

\section{Discussion}
Despite significant progress, PDF-to-text conversion remains challenging due to
the format's low-level representation. As noted by Smith et al. [6], the gap
between visual presentation and logical structure is the fundamental obstacle.

\begin{thebibliography}{9}
\bibitem{lecun} LeCun, Y., Bengio, Y., \& Hinton, G. (2015). Deep learning. \textit{Nature}, 521(7553), 436--444.
\bibitem{vaswani} Vaswani, A., et al. (2017). Attention is all you need. \textit{NeurIPS}, 5998--6008.
\bibitem{brown} Brown, T., et al. (2020). Language models are few-shot learners. \textit{NeurIPS}, 1877--1901.
\bibitem{mao} Mao, S., Rosenfeld, A., \& Kanungo, T. (2003). Document structure analysis algorithms. \textit{Pattern Recognition}, 36(11), 2225--2243.
\bibitem{zhong} Zhong, X., Tang, J., \& Yepes, A. J. (2019). PubLayNet: largest dataset for document layout analysis. \textit{ICDAR}, 1015--1022.
\bibitem{smith} Smith, R. (2007). An overview of the Tesseract OCR engine. \textit{ICDAR}, 629--633.
\end{thebibliography}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 7. Title Page + Abstract
# ──────────────────────────────────────────────────────────────
DOCUMENTS["07_titlepage_abstract"] = r"""
\documentclass[12pt]{report}
\usepackage[margin=1in]{geometry}
\begin{document}

\begin{titlepage}
\centering
\vspace*{2cm}
{\Huge\bfseries Advances in Document Processing\\[0.5cm]}
{\Large A Comprehensive Survey\\[2cm]}
{\large Dr.\ Katherine Park\\[0.3cm]}
{\normalsize Department of Computer Science\\
University of Technology\\
kpark@university.edu\\[2cm]}
{\large April 2026\\[3cm]}
{\small Technical Report TR-2026-042}
\end{titlepage}

\begin{abstract}
This report provides a comprehensive survey of document processing techniques,
covering optical character recognition, layout analysis, semantic classification,
and content extraction. We examine the evolution from rule-based systems to modern
deep learning approaches, identifying key challenges in handling diverse document
formats. Our analysis covers 150 papers published between 2015 and 2025, revealing
trends toward end-to-end learning systems and multimodal architectures.
\end{abstract}

\chapter{Introduction}
Document processing is the task of extracting structured information from
unstructured document images or digital files. This field encompasses several
sub-tasks including text recognition, layout analysis, and semantic understanding.

\section{Motivation}
The volume of digital documents continues to grow exponentially. Organizations
need automated tools to extract, classify, and index information from PDF files,
scanned documents, and other formats.

\section{Scope}
This survey focuses on digital PDF processing, excluding scanned document OCR.
We examine techniques for preserving content fidelity during conversion to
structured formats such as Markdown, HTML, and XML.

\chapter{Background}
\section{PDF Format}
The Portable Document Format stores content as positioned drawing commands rather
than logical text flow. This design prioritizes pixel-perfect rendering over
content accessibility.

\section{Markdown Format}
Markdown is a lightweight markup language designed for readability. It supports
headings, lists, tables, images, and inline formatting through simple syntax.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 8. Figures with Captions
# ──────────────────────────────────────────────────────────────
DOCUMENTS["08_figures_captions"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{float}
\title{Document with Figures and Captions}
\author{Visual Content Team}
\begin{document}
\maketitle

\section{Introduction}
This document tests the handling of figure environments and captions. While we
cannot include actual images in this test LaTeX file without external assets,
we test caption text extraction and figure numbering.

\section{Results}

\begin{figure}[H]
\centering
\rule{8cm}{5cm} % Placeholder rectangle
\caption{Architecture diagram of the PD2MD conversion pipeline showing the six
processing layers from extraction through emission.}
\label{fig:architecture}
\end{figure}

The architecture shown in Figure~\ref{fig:architecture} demonstrates the modular
design of our system. Each layer operates independently, communicating through
a well-defined intermediate representation.

\begin{figure}[H]
\centering
\rule{8cm}{4cm}
\caption{Performance comparison across different PDF complexity levels. Simple
documents convert in under 0.5 seconds, while complex multi-column layouts
require up to 3.2 seconds.}
\label{fig:performance}
\end{figure}

As shown in Figure~\ref{fig:performance}, performance scales linearly with
document complexity for most cases.

\begin{figure}[H]
\centering
\rule{6cm}{4cm}
\caption{Error rate by document category. Academic papers (2.1\%), business
reports (1.4\%), and technical manuals (3.7\%).}
\label{fig:errors}
\end{figure}

\section{Discussion}
The figure captions above should appear in the Markdown output. The converter
should identify caption text and include it near the figure references.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 9. Enumerated & Itemized Lists
# ──────────────────────────────────────────────────────────────
DOCUMENTS["09_enum_itemize"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{enumitem}
\title{Various List Styles}
\author{List Tester}
\begin{document}
\maketitle

\section{Standard Bullet List}
\begin{itemize}
    \item Python is a versatile programming language
    \item JavaScript dominates web development
    \item Rust provides memory safety without garbage collection
    \item Go excels at concurrent programming
    \item TypeScript adds static typing to JavaScript
\end{itemize}

\section{Standard Numbered List}
\begin{enumerate}
    \item Gather requirements from stakeholders
    \item Design the system architecture
    \item Implement core functionality
    \item Write comprehensive tests
    \item Deploy to staging environment
    \item Conduct user acceptance testing
    \item Deploy to production
\end{enumerate}

\section{Description List}
\begin{description}
    \item[Extraction] Raw content pulled from PDF using PyMuPDF
    \item[Assembly] Glyphs grouped into words, lines, and blocks
    \item[Layout] Column detection, header/footer removal, reading order
    \item[Semantics] Heading, list, and paragraph classification
    \item[Tables] Structured cell extraction via pdfplumber
    \item[Emission] Final Markdown text generation
\end{description}

\section{Custom Markers}
\begin{itemize}[label=$\diamond$]
    \item Diamond marker item one
    \item Diamond marker item two
    \item Diamond marker item three
\end{itemize}

\begin{enumerate}[label=\alph*)]
    \item Alpha-labeled item
    \item Beta-labeled item
    \item Gamma-labeled item
\end{enumerate}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 10. Bold / Italic / Underline formatting
# ──────────────────────────────────────────────────────────────
DOCUMENTS["10_formatting"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{ulem}
\title{Text Formatting Showcase}
\author{Format Tester}
\begin{document}
\maketitle

\section{Basic Formatting}
This paragraph contains \textbf{bold text}, \textit{italic text}, and
\underline{underlined text}. We can also combine them: \textbf{\textit{bold
italic text}} is used for strong emphasis.

\section{Monospace and Code}
Inline code like \texttt{print("hello world")} should be wrapped in backticks.
Variable names like \texttt{max\_value} and \texttt{user\_input} should preserve
underscores correctly.

\section{Font Sizes}
{\tiny This is tiny text.}
{\small This is small text.}
{\normalsize This is normal text.}
{\large This is large text.}
{\Large This is Large text.}
{\LARGE This is LARGE text.}

\section{Text Styles}
Here is \textsc{Small Caps Text} and here is \textsf{sans-serif text}.
We also have \textsl{slanted text} which is similar to italic.

\section{Mixed Formatting Paragraph}
In this paragraph, we mix \textbf{bold words} with \textit{italic phrases} and
some \texttt{code snippets} all in the same sentence. This tests whether the
converter can correctly identify formatting spans within a single line of text
and apply the appropriate Markdown markers without overlapping or nesting errors.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 11. Headers and Footers
# ──────────────────────────────────────────────────────────────
DOCUMENTS["11_headers_footers"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{PD2MD Technical Manual}
\fancyhead[R]{Version 1.0}
\fancyfoot[C]{Page \thepage\ of 3}
\fancyfoot[R]{Confidential}
\title{Document with Headers and Footers}
\author{Header/Footer Test}
\begin{document}
\maketitle
\thispagestyle{fancy}

\section{Page 1 Content}
This document has running headers (``PD2MD Technical Manual'' on the left,
``Version 1.0'' on the right) and footers (page number centered, ``Confidential''
on the right). The converter should detect these repeating elements across pages
and exclude them from the body content in the Markdown output.

The header and footer text should not appear as paragraphs in the converted
Markdown. Only the body content within each section should be preserved.

\newpage
\section{Page 2 Content}
This is the second page of the document. The same headers and footers appear
here, demonstrating the cross-page repetition pattern that the converter uses
to identify running headers and footers.

Content on this page should flow naturally after the content from page 1 in the
Markdown output, without any header or footer text interrupting the flow.

\newpage
\section{Page 3 Content}
The third and final page continues with the same layout. By having three pages,
we provide enough data for the cross-page header/footer detection algorithm to
work reliably. The algorithm requires at least two pages to identify patterns.

All body content from all three pages should appear in the correct order in the
final Markdown output.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 12. Footnotes
# ──────────────────────────────────────────────────────────────
DOCUMENTS["12_footnotes"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Document with Footnotes}
\author{Footnote Tester}
\begin{document}
\maketitle

\section{Introduction}
Footnotes are commonly used in academic writing\footnote{This is a simple
footnote that provides additional context.} to provide supplementary information
without cluttering the main text.

\section{Technical Details}
The PDF format stores footnotes as regular text positioned at the bottom of the
page\footnote{PDF does not have a semantic concept of ``footnotes'' --- they are
simply text blocks positioned near the page bottom.}. This means the converter
must use spatial analysis to identify them.

Our approach detects footnotes by looking for small-font text blocks near the
bottom margin\footnote{Specifically, we check for text blocks where the font
size is less than 80\% of the body font size and the vertical position is in
the bottom 15\% of the page.}. These blocks are then tagged as footnotes in the
intermediate representation.

\section{Limitations}
Multi-page footnotes\footnote{Footnotes that are too long to fit on a single
page will overflow to the next page. This is a known edge case that our current
implementation does not handle perfectly.} present additional challenges.

\section{Conclusion}
Footnote handling is important for academic document conversion. The key signals
are: small font size, bottom-of-page positioning, and superscript reference markers
in the body text.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 13. Mathematical Equations
# ──────────────────────────────────────────────────────────────
DOCUMENTS["13_math_equations"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath}
\usepackage{amssymb}
\title{Mathematical Content}
\author{Math Department}
\begin{document}
\maketitle

\section{Inline Mathematics}
The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$. Einstein's
famous equation $E = mc^2$ relates energy and mass. The area of a circle with
radius $r$ is $A = \pi r^2$.

\section{Display Equations}
The Gaussian integral:
\begin{equation}
\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}
\end{equation}

Maxwell's equations in differential form:
\begin{align}
\nabla \cdot \mathbf{E} &= \frac{\rho}{\epsilon_0} \\
\nabla \cdot \mathbf{B} &= 0 \\
\nabla \times \mathbf{E} &= -\frac{\partial \mathbf{B}}{\partial t} \\
\nabla \times \mathbf{B} &= \mu_0 \mathbf{J} + \mu_0 \epsilon_0 \frac{\partial \mathbf{E}}{\partial t}
\end{align}

\section{Matrix Notation}
A 3x3 identity matrix:
\begin{equation}
I = \begin{pmatrix}
1 & 0 & 0 \\
0 & 1 & 0 \\
0 & 0 & 1
\end{pmatrix}
\end{equation}

\section{Summation and Limits}
The Taylor series expansion:
\begin{equation}
e^x = \sum_{n=0}^{\infty} \frac{x^n}{n!} = 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \cdots
\end{equation}

The definition of a limit:
\begin{equation}
\lim_{x \to a} f(x) = L
\end{equation}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 14. Code Listings
# ──────────────────────────────────────────────────────────────
DOCUMENTS["14_code_listings"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{listings}
\usepackage{xcolor}
\lstset{
    basicstyle=\ttfamily\small,
    numbers=left,
    numberstyle=\tiny\color{gray},
    frame=single,
    breaklines=true,
    keywordstyle=\color{blue},
    commentstyle=\color{green!60!black},
    stringstyle=\color{red},
}
\title{Code Listings Test}
\author{Developer}
\begin{document}
\maketitle

\section{Python Example}
\begin{lstlisting}[language=Python]
def fibonacci(n):
    '''Calculate the nth Fibonacci number.'''
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# Print first 10 Fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
\end{lstlisting}

\section{JavaScript Example}
\begin{lstlisting}[language=JavaScript]
async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch failed:', error);
        throw error;
    }
}
\end{lstlisting}

\section{Inline Code}
Use the \texttt{pip install pd2md} command to install the package. Then run
\texttt{pd2md convert input.pdf} to convert a file. The output will be saved
to the \texttt{output/} directory by default.

\section{Shell Commands}
\begin{lstlisting}[language=bash]
# Clone the repository
git clone https://github.com/user/pd2md.git
cd pd2md

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest backend/tests/ -v
\end{lstlisting}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 15. Mixed Formatting Stress Test
# ──────────────────────────────────────────────────────────────
DOCUMENTS["15_mixed_stress"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Mixed Formatting Stress Test}
\author{QA Team}
\begin{document}
\maketitle

\section{Paragraph with Everything}
This paragraph has \textbf{bold text}, \textit{italic text}, \texttt{inline code},
a reference to Section 2, and some numbers like 3.14159 and 2.71828. It also
includes special characters: ampersand (\&), percent (5\%), dollar sign (\$100),
and various punctuation marks: semicolons; colons: dashes --- and ellipses\ldots

\section{Lists Followed by Paragraphs}
Here is a list:
\begin{itemize}
    \item \textbf{Bold list item} with explanation text
    \item \textit{Italic list item} with different formatting
    \item \texttt{Code list item} showing a command
\end{itemize}
And now we continue with a regular paragraph that follows the list. The converter
should correctly separate the list from this paragraph.

\section{Table Followed by Text}
\begin{table}[h]
\centering
\begin{tabular}{|l|r|}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
Precision & 94.2\% \\
Recall & 91.7\% \\
F1 Score & 92.9\% \\
\hline
\end{tabular}
\end{table}
The table above shows our evaluation metrics. As you can see, the system achieves
high precision and recall across all test cases.

\section{Multiple Paragraphs}
First paragraph of this section. It contains multiple sentences that should be
joined into a single paragraph in the Markdown output.

Second paragraph of this section. This tests that paragraph breaks are correctly
detected based on vertical spacing between text blocks.

Third paragraph. Short but distinct from the previous paragraphs.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 16. Long Paragraphs (Prose)
# ──────────────────────────────────────────────────────────────
DOCUMENTS["16_long_paragraphs"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Long-Form Prose}
\author{Technical Writer}
\begin{document}
\maketitle

\section{The Challenge of PDF Conversion}
Converting PDF documents to Markdown is fundamentally challenging because the two
formats represent content in fundamentally different ways. PDF is a page description
language that specifies the exact position, font, and size of each character on a
page. It is designed for precise visual reproduction across different devices and
platforms, prioritizing appearance over structure. Markdown, on the other hand, is
a semantic markup language that describes the logical structure of content through
simple syntax conventions like hash marks for headings, asterisks for emphasis,
and pipe characters for tables.

The gap between these two paradigms means that any converter must bridge the
divide between visual presentation and logical structure. This requires the
converter to reverse-engineer the author's intent from the visual layout, inferring
paragraph boundaries from spacing, heading levels from font sizes, and list items
from indentation and marker characters. This process is inherently heuristic and
imperfect, because the same visual appearance can result from different logical
structures, and different tools may produce subtly different PDF output for the
same source document.

\section{Our Approach}
Our six-layer pipeline approaches this challenge by separating concerns into
distinct processing stages. The first layer extracts raw character data from the
PDF, including precise position coordinates, font information, and text content.
The second layer assembles these characters into words, lines, and blocks using
adaptive gap analysis that adjusts thresholds based on the local font size. The
third layer performs layout analysis to detect headers, footers, columns, and
reading order. The fourth layer applies semantic classification to identify
headings, paragraphs, lists, and other structural elements. The fifth layer
handles table extraction using specialized algorithms. The sixth and final layer
generates the Markdown output.

\section{Content Accuracy as the Primary Goal}
Throughout the entire pipeline, our primary goal is content accuracy rather than
formatting fidelity. We prioritize ensuring that every word, number, and symbol
from the source PDF appears in the output Markdown, even if the formatting is
not perfectly replicated. This design decision reflects the intended use case:
converting documents for consumption by AI and language models, where content
completeness matters more than visual appearance.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 17. Blockquotes / Epigraphs
# ──────────────────────────────────────────────────────────────
DOCUMENTS["17_blockquotes"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{csquotes}
\title{Quotations and Epigraphs}
\author{Editorial Team}
\begin{document}
\maketitle

\section{Famous Quotes}
As Albert Einstein once said:

\begin{quote}
Imagination is more important than knowledge. Knowledge is limited. Imagination
encircles the world.
\end{quote}

This perspective highlights the importance of creative thinking in scientific
discovery.

\section{Extended Quotation}
From Donald Knuth's \textit{The Art of Computer Programming}:

\begin{quotation}
Programs are meant to be read by humans and only incidentally for computers to
execute. The process of preparing programs for a digital computer is especially
attractive because it not only can be economically and scientifically rewarding,
it can also be an aesthetic experience much like composing poetry or music.
\end{quotation}

\section{Nested Quote}
In his review, the critic noted:

\begin{quote}
The author argues convincingly that ``the future of document processing lies in
hybrid approaches that combine rule-based heuristics with machine learning.''
This is a balanced view that acknowledges the strengths of both paradigms.
\end{quote}

\section{Display Quote with Attribution}
\begin{quote}
The only way to do great work is to love what you do. If you haven't found it
yet, keep looking. Don't settle.

\hfill --- Steve Jobs
\end{quote}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 18. Nested Tables
# ──────────────────────────────────────────────────────────────
DOCUMENTS["18_nested_tables"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Multiple Tables}
\author{Data Team}
\begin{document}
\maketitle

\section{Server Configuration}
\begin{table}[h]
\centering
\caption{Production Servers}
\begin{tabular}{|l|c|r|l|}
\hline
\textbf{Server} & \textbf{CPU Cores} & \textbf{RAM (GB)} & \textbf{Role} \\
\hline
web-01 & 8 & 32 & Load Balancer \\
web-02 & 16 & 64 & Application \\
web-03 & 16 & 64 & Application \\
db-01 & 32 & 128 & Primary DB \\
db-02 & 32 & 128 & Replica DB \\
cache-01 & 8 & 64 & Redis Cache \\
\hline
\end{tabular}
\end{table}

\section{API Endpoints}
\begin{table}[h]
\centering
\caption{REST API Routes}
\begin{tabular}{|l|l|l|l|}
\hline
\textbf{Method} & \textbf{Path} & \textbf{Description} & \textbf{Auth} \\
\hline
POST & /api/upload & Upload PDF file & API Key \\
GET & /api/jobs/\{id\}/status & Check job status & API Key \\
GET & /api/jobs/\{id\}/result & Download result & API Key \\
GET & /api/health & Health check & None \\
DELETE & /api/jobs/\{id\} & Cancel job & API Key \\
\hline
\end{tabular}
\end{table}

\section{Performance Metrics}
\begin{table}[h]
\centering
\caption{Conversion Benchmarks by Document Type}
\begin{tabular}{|l|r|r|r|r|}
\hline
\textbf{Document Type} & \textbf{Pages} & \textbf{Time (s)} & \textbf{Blocks} & \textbf{Score} \\
\hline
Simple Article & 2 & 0.3 & 12 & 98\% \\
Technical Report & 15 & 2.1 & 89 & 95\% \\
Academic Paper & 10 & 1.8 & 67 & 93\% \\
Financial Report & 30 & 4.5 & 203 & 91\% \\
User Manual & 50 & 7.2 & 412 & 89\% \\
\hline
\end{tabular}
\end{table}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 19. Multi-Level Headings
# ──────────────────────────────────────────────────────────────
DOCUMENTS["19_headings"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Multi-Level Heading Structure}
\author{Structure Tester}
\begin{document}
\maketitle

\section{Level 1: Architecture}
This section tests heading level detection across multiple depths.

\subsection{Level 2: Frontend}
The frontend uses vanilla HTML, CSS, and JavaScript.

\subsubsection{Level 3: HTML Structure}
The HTML file contains the drag-and-drop upload zone, progress display,
result view, and error handling sections.

\subsubsection{Level 3: CSS Design System}
CSS variables define the color palette, typography, spacing, and animations.
The design uses a dark theme with glassmorphism effects.

\subsection{Level 2: Backend}
The backend is built with FastAPI and Python.

\subsubsection{Level 3: API Routes}
Five routes handle the conversion lifecycle: upload, status, download Markdown,
download ZIP, and content preview.

\subsubsection{Level 3: Pipeline}
The conversion pipeline consists of six modular layers.

\section{Level 1: Testing}
Comprehensive tests verify each layer independently and the full pipeline
end-to-end.

\subsection{Level 2: Unit Tests}
Each pipeline module has dedicated unit tests with synthetic PDF fixtures.

\subsection{Level 2: Integration Tests}
End-to-end tests verify that real PDFs convert correctly with all content
preserved.

\section{Level 1: Deployment}
Deployment instructions for both development and production environments.
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 20. Definition Lists and Descriptions
# ──────────────────────────────────────────────────────────────
DOCUMENTS["20_definitions"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\title{Technical Glossary}
\author{Documentation Team}
\begin{document}
\maketitle

\section{Core Concepts}

\begin{description}
\item[Glyph] The smallest unit of text in a PDF. Represents a single character
with position, font, and size metadata.

\item[Content Block] A group of related text lines that form a logical unit such
as a paragraph, heading, or list item.

\item[Font Catalog] A registry of all fonts used in a document, including the
identified body font and heading fonts.

\item[Reading Order] The sequence in which content blocks should be read to
reconstruct the logical flow of the document.

\item[Intermediate Representation] The structured data model that connects all
pipeline layers, containing blocks, their types, and metadata.
\end{description}

\section{Pipeline Stages}

\begin{description}
\item[Extraction] Layer 1. Raw PDF data retrieval using PyMuPDF.
\item[Assembly] Layer 2. Character-to-block construction.
\item[Layout Analysis] Layer 3. Spatial structure detection.
\item[Semantic Analysis] Layer 4. Content type classification.
\item[Table Extraction] Layer 5. Structured table recovery.
\item[Emission] Layer 6. Markdown text generation.
\end{description}

\section{File Formats}

\begin{description}
\item[PDF] Portable Document Format. Page-oriented, position-based rendering.
\item[Markdown] Lightweight semantic markup. Line-oriented, structure-based.
\item[YAML] YAML Ain't Markup Language. Used for frontmatter metadata.
\item[ZIP] Archive format for bundling Markdown output with extracted images.
\end{description}
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 21. Hyperlinks and URLs
# ──────────────────────────────────────────────────────────────
DOCUMENTS["21_hyperlinks"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\title{Hyperlinks and URLs}
\author{Link Tester}
\begin{document}
\maketitle

\section{Web Links}
Visit the official Python website at \url{https://www.python.org} for the latest
Python releases. The PyMuPDF documentation is available at
\url{https://pymupdf.readthedocs.io}.

\section{Named Links}
For more information, see the \href{https://github.com/pymupdf/PyMuPDF}{PyMuPDF
GitHub repository}. The \href{https://fastapi.tiangolo.com}{FastAPI documentation}
provides excellent tutorials. You can also check the
\href{https://pdfplumber.readthedocs.io}{pdfplumber documentation} for table
extraction details.

\section{Email Links}
Contact the maintainer at \href{mailto:developer@example.com}{developer@example.com}
for support questions.

\section{Internal References}
See Section~\ref{sec:conclusion} for the conclusion.
See Table~\ref{tab:links} for a summary of all URLs.

\begin{table}[h]
\centering
\caption{URL Reference Table}
\label{tab:links}
\begin{tabular}{|l|l|}
\hline
\textbf{Resource} & \textbf{URL} \\
\hline
Python & https://www.python.org \\
PyMuPDF & https://pymupdf.readthedocs.io \\
FastAPI & https://fastapi.tiangolo.com \\
pdfplumber & https://pdfplumber.readthedocs.io \\
\hline
\end{tabular}
\end{table}

\section{Conclusion}
\label{sec:conclusion}
All hyperlinks should be preserved in the Markdown output using the standard
link syntax: [text](url).
\end{document}
"""

# ──────────────────────────────────────────────────────────────
# 22. Full Technical Report
# ──────────────────────────────────────────────────────────────
DOCUMENTS["22_full_report"] = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\title{PD2MD: An Intelligent PDF to Markdown Converter\\
\large Technical Design Document}
\author{Engineering Team}
\date{April 2026}
\begin{document}
\maketitle

\begin{abstract}
We present PD2MD, a modular pipeline for converting digital PDF documents to
clean, structured Markdown. Our system prioritizes content accuracy over
formatting fidelity, making it ideal for preparing documents for AI and LLM
consumption. The pipeline consists of six layers: extraction, assembly, layout
analysis, semantic classification, table extraction, and Markdown emission.
Evaluation on 117 test cases shows 100\% content accuracy across diverse
document types.
\end{abstract}

\section{Introduction}
The growing use of large language models for document analysis has created a
need for high-quality text extraction from PDF files. While PDF is the dominant
format for published documents, its page-oriented representation makes it
challenging to extract logical structure.

\subsection{Problem Statement}
Given a digital PDF file, produce a Markdown document that:
\begin{enumerate}
    \item Preserves all text content character-perfectly
    \item Identifies headings, paragraphs, and lists
    \item Extracts tables with correct cell values
    \item Includes embedded images with references
    \item Removes running headers and footers
\end{enumerate}

\subsection{Design Principles}
\begin{itemize}
    \item \textbf{Content first}: Every word must survive conversion
    \item \textbf{Modular}: Each layer is independently testable
    \item \textbf{No ML required}: CPU-only, deterministic output
    \item \textbf{Configurable}: Image format, frontmatter, validation
\end{itemize}

\section{Architecture}

\subsection{Pipeline Overview}
The conversion pipeline consists of six sequential layers:

\begin{table}[h]
\centering
\caption{Pipeline Layers}
\begin{tabular}{clll}
\toprule
\textbf{Layer} & \textbf{Name} & \textbf{Input} & \textbf{Output} \\
\midrule
1 & Extractor & PDF file & Raw glyphs, images, vectors \\
2 & Assembler & Raw glyphs & Text blocks, font catalog \\
3 & Layout & Text blocks & Ordered content blocks \\
4 & Semantics & Content blocks & Classified blocks \\
5 & Tables & Classified blocks & Blocks with table data \\
6 & Emitter & All blocks & Markdown file \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Data Model}
The central data structure is the \texttt{ContentBlock}, which carries:
\begin{itemize}
    \item Block type (heading, paragraph, list item, table, etc.)
    \item Bounding box coordinates
    \item Text content with span-level formatting
    \item Optional table data or image reference
\end{itemize}

\section{Evaluation}

\subsection{Test Suite}
We evaluate PD2MD using 147 automated tests across 8 test suites:

\begin{table}[h]
\centering
\caption{Test Results}
\begin{tabular}{lrc}
\toprule
\textbf{Suite} & \textbf{Tests} & \textbf{Status} \\
\midrule
Extractor & 20 & Pass \\
Assembler & 23 & Pass \\
Layout Analyzer & 18 & Pass \\
Semantic Analyzer & 18 & Pass \\
Table Extractor & 15 & Pass \\
Emitter & 23 & Pass \\
Hardening & 17 & Pass \\
Advanced Features & 13 & Pass \\
\midrule
\textbf{Total} & \textbf{147} & \textbf{All Pass} \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Performance}
Average conversion time per page is 0.15 seconds for simple documents and
0.45 seconds for complex layouts with tables. Memory usage stays below 100 MB
for documents up to 100 pages.

\section{Future Work}
Potential improvements include:
\begin{enumerate}
    \item Support for scanned PDFs via OCR integration
    \item Multi-column academic paper handling improvements
    \item Mathematical equation extraction to LaTeX notation
    \item Nested list depth preservation
    \item Custom Markdown flavor output (GitHub, CommonMark, etc.)
\end{enumerate}

\section{Conclusion}
PD2MD demonstrates that high-fidelity PDF to Markdown conversion is achievable
with a carefully designed pipeline of spatial analysis heuristics. By prioritizing
content accuracy and modularity, the system provides reliable document extraction
for AI and LLM applications without requiring machine learning models or GPU
resources.
\end{document}
"""


# ──────────────────────────────────────────────────────────────
# Compile everything
# ──────────────────────────────────────────────────────────────

def compile_latex(name: str, source: str) -> bool:
    """Compile a LaTeX file to PDF."""
    tex_path = LATEX_DIR / f"{name}.tex"
    tex_path.write_text(source.strip(), encoding="utf-8")

    # Run pdflatex twice (for references/TOC)
    for pass_num in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(PDF_DIR), str(tex_path)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0 and pass_num == 1:
            print(f"  WARN: {name} pdflatex returned {result.returncode}")

    pdf_path = PDF_DIR / f"{name}.pdf"
    if pdf_path.exists():
        size_kb = pdf_path.stat().st_size / 1024
        print(f"  [OK] {name}.pdf ({size_kb:.0f} KB)")
        return True
    else:
        print(f"  [FAIL] {name}.pdf not created")
        # Check log for errors
        log_path = PDF_DIR / f"{name}.log"
        if log_path.exists():
            log = log_path.read_text(encoding="utf-8", errors="replace")
            errors = [l for l in log.split("\n") if l.startswith("!")]
            if errors:
                for e in errors[:3]:
                    print(f"    {e}")
        return False


def main():
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(DOCUMENTS)} LaTeX documents...")
    print()

    success = 0
    fail = 0

    for name, source in sorted(DOCUMENTS.items()):
        try:
            if compile_latex(name, source):
                success += 1
            else:
                fail += 1
        except subprocess.TimeoutExpired:
            print(f"  [FAIL] {name} — timed out")
            fail += 1
        except Exception as e:
            print(f"  [FAIL] {name} — {e}")
            fail += 1

    print()
    print(f"{'=' * 50}")
    print(f"Compiled: {success}/{success + fail} ({fail} failed)")

    # Clean up aux files
    for ext in ["aux", "log", "out", "toc", "nav", "snm"]:
        for f in PDF_DIR.glob(f"*.{ext}"):
            f.unlink(missing_ok=True)

    print(f"PDFs saved to: {PDF_DIR}")


if __name__ == "__main__":
    main()
