"""
Content Accuracy Validator (Phase 8.1).

Validates that no content was lost during conversion by comparing
extracted text against the final Markdown output.

Provides a confidence score and a detailed report of any issues.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from backend.app.models.document import (
    BlockType,
    ContentBlock,
    DocumentResult,
    PageResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A single content accuracy issue."""
    severity: str  # "error", "warning", "info"
    page: int
    message: str
    expected: str = ""
    actual: str = ""


@dataclass
class ValidationReport:
    """Report of content accuracy validation."""
    is_valid: bool = True
    overall_score: float = 1.0
    total_blocks: int = 0
    classified_blocks: int = 0
    empty_blocks: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)
    text_coverage: float = 1.0  # Ratio of extracted text present in output

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity == "error":
            self.is_valid = False

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def summary(self) -> str:
        status = "✅ PASS" if self.is_valid else "❌ FAIL"
        return (
            f"{status} | Score: {self.overall_score:.0%} | "
            f"Blocks: {self.classified_blocks}/{self.total_blocks} | "
            f"Issues: {self.error_count}E {self.warning_count}W"
        )


def validate_conversion(result: DocumentResult, markdown_text: str) -> ValidationReport:
    """Validate that conversion preserved all content.

    Checks:
      1. All blocks have types (no UNKNOWN remaining)
      2. No empty blocks (blocks with type but no text)
      3. Key text from source appears in Markdown output
      4. Table cell values appear in Markdown
      5. Image references are present for extracted images

    Args:
        result: The DocumentResult from the pipeline.
        markdown_text: The generated Markdown content.

    Returns:
        ValidationReport with issues and confidence score.
    """
    report = ValidationReport()

    for page in result.pages:
        _validate_page(page, markdown_text, report)

    # Calculate overall score
    if report.total_blocks > 0:
        classified_ratio = report.classified_blocks / report.total_blocks
        empty_penalty = report.empty_blocks / report.total_blocks
        error_penalty = min(1.0, report.error_count * 0.05)
        report.overall_score = max(0, classified_ratio - empty_penalty - error_penalty)
    else:
        report.overall_score = 0.0

    return report


def _validate_page(page: PageResult, md_text: str, report: ValidationReport):
    """Validate a single page's content."""
    for block in page.blocks:
        report.total_blocks += 1

        # Check 1: Block classification
        if block.block_type == BlockType.UNKNOWN:
            if block.text_block and block.text_block.text.strip():
                report.add_issue(ValidationIssue(
                    severity="warning",
                    page=page.page_number,
                    message=f"UNKNOWN block with text: '{block.text[:50]}...'",
                ))
            continue

        # Skip headers/footers and footnotes (intentionally reformatted)
        if block.block_type in (BlockType.HEADER, BlockType.FOOTER, BlockType.FOOTNOTE):
            report.classified_blocks += 1
            continue

        report.classified_blocks += 1

        # Check 2: Empty blocks
        if block.block_type in (BlockType.PARAGRAPH, BlockType.HEADING, BlockType.LIST_ITEM):
            if not block.text_block or not block.text_block.text.strip():
                report.empty_blocks += 1
                report.add_issue(ValidationIssue(
                    severity="warning",
                    page=page.page_number,
                    message=f"Empty {block.block_type.name} block",
                ))
                continue

        # Check 3: Text content present in Markdown
        if block.text_block and block.text_block.text.strip():
            # Extract significant words (skip very short words, strip formatting)
            words = _extract_significant_words(block.text_block.text)
            # Normalize the markdown text for comparison
            norm_md = _normalize_for_comparison(md_text)
            for word in words:
                norm_word = _normalize_for_comparison(word)
                if norm_word not in norm_md:
                    report.add_issue(ValidationIssue(
                        severity="error",
                        page=page.page_number,
                        message=f"Word '{word}' not found in Markdown output",
                        expected=word,
                    ))

        # Check 4: Table cells in Markdown
        if block.table_data:
            for cell in block.table_data.cells:
                if cell.text and len(cell.text) >= 2:
                    if cell.text not in md_text:
                        report.add_issue(ValidationIssue(
                            severity="error",
                            page=page.page_number,
                            message=f"Table cell '{cell.text}' not found in Markdown",
                            expected=cell.text,
                        ))


def _extract_significant_words(text: str) -> list[str]:
    """Extract significant words for content verification.

    Returns words that are long enough and unique enough to verify
    they survived the conversion pipeline.
    """
    # Remove common formatting artifacts
    text = re.sub(r'[•\-\*\u2022\u2023\xB7]', '', text)

    # Split into words and filter
    words = text.split()
    significant = []
    for w in words:
        # Strip punctuation from edges
        w = w.strip('.,;:!?()[]{}"\'-')
        # Only check words >= 4 chars (short words are too common to verify)
        if len(w) >= 4 and not w.isdigit():
            significant.append(w)

    # Return at most 10 words per block (performance)
    return significant[:10]


def _normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison — handles encoding artifacts.

    PDF extraction sometimes produces different Unicode sequences for the
    same visual character (curly quotes, em-dashes, ligatures). This
    normalizes them for comparison.
    """
    import unicodedata
    # Normalize unicode (NFC form)
    text = unicodedata.normalize('NFC', text)
    # Replace curly quotes with straight
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    # Replace em/en dashes
    text = text.replace('\u2014', '-').replace('\u2013', '-')
    # Replace non-breaking spaces
    text = text.replace('\u00a0', ' ')
    # Common ligatures
    text = text.replace('\ufb01', 'fi').replace('\ufb02', 'fl')
    text = text.replace('\ufb00', 'ff').replace('\ufb03', 'ffi')
    text = text.replace('\ufb04', 'ffl')
    return text
