"""
Layer 6: Markdown Emission.

Converts the fully classified ContentBlocks into Markdown text:
  - Document-level frontmatter (YAML metadata)
  - Block-by-block emission in reading order
  - Inline formatting (bold, italic, code, links)
  - Image references
  - Table rendering
  - Whitespace cleanup and polish
  - Output package assembly (markdown + images folder)

Content accuracy principle: The emitted Markdown must contain every
word, number, and symbol from the original PDF. Formatting may adapt
to Markdown's limitations, but content is NEVER lost.
"""

from __future__ import annotations

import logging
import re
import shutil
import zipfile
from pathlib import Path

from backend.app.models.document import (
    BlockType,
    ContentBlock,
    DocumentMetadata,
    DocumentResult,
    FontCatalog,
    ListStyle,
    TextBlock,
    TextLine,
    TextSpan,
)
from backend.app.pipeline.table_extractor import table_to_markdown

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 6.1 — Document-Level Structure
# ---------------------------------------------------------------------------

def emit_frontmatter(metadata: DocumentMetadata) -> str:
    """Generate YAML frontmatter from document metadata.

    Only includes non-empty fields.
    """
    lines = ["---"]

    if metadata.title:
        lines.append(f"title: \"{_escape_yaml(metadata.title)}\"")
    if metadata.author:
        lines.append(f"author: \"{_escape_yaml(metadata.author)}\"")
    if metadata.subject:
        lines.append(f"subject: \"{_escape_yaml(metadata.subject)}\"")
    if metadata.keywords:
        lines.append(f"keywords: \"{_escape_yaml(metadata.keywords)}\"")
    if metadata.creation_date:
        lines.append(f"date: \"{metadata.creation_date}\"")
    lines.append(f"source: \"{metadata.source_filename}\"")
    lines.append(f"pages: {metadata.page_count}")

    lines.append("---")
    return "\n".join(lines)


def _escape_yaml(text: str) -> str:
    """Escape special characters for YAML string values."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------------------
# Step 6.2 — Block-by-Block Emission
# ---------------------------------------------------------------------------

def emit_block(block: ContentBlock, images_dir: str = "images") -> str:
    """Convert a single ContentBlock to its Markdown representation.

    Args:
        block: A classified ContentBlock.
        images_dir: Relative path to images directory for image references.

    Returns:
        Markdown string for this block.
    """
    if block.block_type == BlockType.HEADING:
        return _emit_heading(block)
    elif block.block_type == BlockType.PARAGRAPH:
        return _emit_paragraph(block)
    elif block.block_type == BlockType.LIST_ITEM:
        return _emit_list_item(block)
    elif block.block_type == BlockType.CODE_BLOCK:
        return _emit_code_block(block)
    elif block.block_type == BlockType.TABLE:
        return _emit_table(block)
    elif block.block_type == BlockType.IMAGE:
        return _emit_image(block, images_dir)
    elif block.block_type == BlockType.BLOCKQUOTE:
        return _emit_blockquote(block)
    elif block.block_type == BlockType.HORIZONTAL_RULE:
        return "---"
    elif block.block_type == BlockType.FOOTNOTE:
        return _emit_footnote(block)
    elif block.block_type in (BlockType.HEADER, BlockType.FOOTER):
        return ""  # Excluded from output
    else:
        # UNKNOWN: emit as plain paragraph (safety net)
        return _emit_paragraph(block)


def _emit_heading(block: ContentBlock) -> str:
    """Emit a heading with proper # prefix."""
    level = min(6, max(1, block.heading_level))
    prefix = "#" * level
    text = _emit_inline_text(block.text_block) if block.text_block else ""
    return f"{prefix} {text.strip()}"


def _emit_paragraph(block: ContentBlock) -> str:
    """Emit a paragraph with inline formatting."""
    if not block.text_block:
        return ""
    return _emit_inline_text(block.text_block).strip()


def _emit_list_item(block: ContentBlock) -> str:
    """Emit a list item with proper marker."""
    indent = "  " * block.list_level

    if block.list_style == ListStyle.ORDERED:
        marker = f"{block.list_marker}"
        if not marker.endswith(".") and not marker.endswith(")"):
            marker += "."
    else:
        marker = "-"

    text = ""
    if block.text_block:
        raw_text = _emit_inline_text(block.text_block).strip()
        # Remove the original bullet/number marker from the text
        # (already represented by the markdown marker)
        text = _strip_list_marker(raw_text)

    return f"{indent}{marker} {text}"


def _strip_list_marker(text: str) -> str:
    """Remove the leading list marker from text content.

    The marker is already being emitted separately, so we strip it
    from the content to avoid duplication.
    """
    # Strip bullet markers (•, ·, -, *, etc.)
    text = re.sub(
        r'^[\s]*[•\-\*\u2022\u2023\u25E6\u2043\u2219\u25AA\u25CB\u25CF\u2013\u2014\xB7\xB0]\s*',
        '', text
    )
    # Strip ordered markers (1., a), (i), etc.)
    text = re.sub(
        r'^[\s]*(\d{1,3}[.)]\s*|[a-zA-Z][.)]\s*|\([a-zA-Z0-9]+\)\s*|[ivxIVX]{1,4}[.)]\s*)',
        '', text
    )
    return text


def _emit_code_block(block: ContentBlock) -> str:
    """Emit a fenced code block.

    Strips PDF line numbers (e.g., '1 def foo():' → 'def foo():')
    from code listings that include them.
    """
    lang = block.code_language or ""
    text = block.text_block.text if block.text_block else ""

    # Strip leading PDF line numbers from each line.
    # Pattern: line starts with 1-3 digit number followed by space(s) then code.
    # We only strip if multiple lines have this pattern (to avoid false positives).
    lines = text.split("\n")
    numbered_count = sum(1 for l in lines if re.match(r'^\d{1,3}\s+\S', l))

    if numbered_count >= 2 and numbered_count >= len([l for l in lines if l.strip()]) * 0.5:
        stripped_lines = []
        for line in lines:
            m = re.match(r'^\d{1,3}\s+(.*)', line)
            if m:
                stripped_lines.append(m.group(1))
            else:
                stripped_lines.append(line)
        text = "\n".join(stripped_lines)

    # Clean up: remove leading/trailing blank lines within the block
    text = text.strip("\n")

    return f"```{lang}\n{text}\n```"


def _emit_table(block: ContentBlock) -> str:
    """Emit a markdown table."""
    if block.table_data:
        return table_to_markdown(block.table_data)
    elif block.text_block:
        # Fallback: emit as paragraph if table extraction failed
        return _emit_paragraph(block)
    return ""


def _emit_image(block: ContentBlock, images_dir: str) -> str:
    """Emit an image reference."""
    if not block.image_ref:
        return ""

    img = block.image_ref
    caption = img.caption or f"Image {img.image_index + 1}"
    alt_text = caption.replace('"', '\\"')

    if img.saved_path:
        # Use relative path from markdown file to images directory
        filename = img.saved_path.name
        path = f"{images_dir}/{filename}"
    else:
        path = f"{images_dir}/page{img.page_number + 1}_img{img.image_index + 1}.png"

    return f"![{alt_text}]({path})"


def _emit_blockquote(block: ContentBlock) -> str:
    """Emit a blockquote."""
    if not block.text_block:
        return ""
    text = _emit_inline_text(block.text_block)
    lines = text.strip().split("\n")
    return "\n".join(f"> {line}" for line in lines)


def _emit_footnote(block: ContentBlock) -> str:
    """Emit a footnote."""
    fid = block.footnote_id or "?"
    text = block.footnote_text or (block.text_block.text if block.text_block else "")
    return f"[^{fid}]: {text.strip()}"


# ---------------------------------------------------------------------------
# Inline Text Emission (handles bold, italic, code spans)
# ---------------------------------------------------------------------------

def _emit_inline_text(text_block: TextBlock) -> str:
    """Convert a TextBlock to Markdown with inline formatting.

    Processes each line's spans, wrapping styled runs in:
      - **bold** markers
      - *italic* markers
      - ***bold italic*** markers
      - `code` markers (monospace)
      - [text](url) for links
    """
    lines: list[str] = []

    for line in text_block.lines:
        line_parts: list[str] = []
        for span in line.spans:
            text = span.text
            if not text:
                continue

            # Apply link formatting
            if span.link_url:
                text = f"[{text.strip()}]({span.link_url})"
                line_parts.append(text)
                continue

            # Apply inline code formatting
            if span.is_monospace and not _is_all_whitespace(text):
                # Only wrap non-space text in backticks
                stripped = text.strip()
                leading = text[:len(text) - len(text.lstrip())]
                trailing = text[len(text.rstrip()):]
                if stripped:
                    text = f"{leading}`{stripped}`{trailing}"
                    line_parts.append(text)
                    continue

            # Apply bold/italic formatting
            if span.is_bold and span.is_italic:
                text = _wrap_emphasis(text, "***")
            elif span.is_bold:
                text = _wrap_emphasis(text, "**")
            elif span.is_italic:
                text = _wrap_emphasis(text, "*")

            # Superscript/subscript (Markdown doesn't have native support)
            if span.is_superscript:
                stripped = text.strip()
                if stripped:
                    text = f"^{stripped}^"
            elif span.is_subscript:
                stripped = text.strip()
                if stripped:
                    text = f"~{stripped}~"

            line_parts.append(text)

        lines.append("".join(line_parts))

    return "\n".join(lines)


def _wrap_emphasis(text: str, marker: str) -> str:
    """Wrap text in emphasis markers, preserving leading/trailing spaces.

    "  bold text  " → "  **bold text**  " (spaces outside markers)
    """
    if not text.strip():
        return text

    leading = text[:len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()):]
    content = text.strip()

    return f"{leading}{marker}{content}{marker}{trailing}"


def _is_all_whitespace(text: str) -> bool:
    return not text.strip()


# ---------------------------------------------------------------------------
# Step 6.3 — Whitespace & Formatting Polish
# ---------------------------------------------------------------------------

def polish_markdown(markdown: str) -> str:
    """Clean up the raw markdown output.

    Fixes:
      - Excessive blank lines (max 2 consecutive)
      - Trailing whitespace
      - Missing blank line before headings
      - Missing blank line before/after code blocks and tables
      - Normalize line endings
    """
    # Normalize line endings
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")

    lines = markdown.split("\n")
    polished: list[str] = []

    for i, line in enumerate(lines):
        # Strip trailing whitespace
        line = line.rstrip()

        # Ensure blank line before headings (except at document start)
        if line.startswith("#") and polished and polished[-1].strip():
            polished.append("")

        # Ensure blank line before code fences
        if line.startswith("```") and polished and polished[-1].strip():
            polished.append("")

        # Ensure blank line before tables
        if line.startswith("|") and polished and polished[-1].strip() and not polished[-1].startswith("|"):
            polished.append("")

        polished.append(line)

    # Remove excessive blank lines (max 2 consecutive)
    result: list[str] = []
    blank_count = 0
    for line in polished:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    # Ensure file ends with single newline
    text = "\n".join(result).strip() + "\n"
    return text


# ---------------------------------------------------------------------------
# Step 6.4 — Output Package Assembly
# ---------------------------------------------------------------------------

def emit_document(
    result: DocumentResult,
    output_dir: Path,
    include_frontmatter: bool = True,
) -> Path:
    """Emit the complete Markdown document from a DocumentResult.

    Produces:
      - output_dir/document.md    — The markdown file
      - output_dir/images/        — Extracted images (already saved by Layer 1)

    Args:
        result: Complete DocumentResult from the pipeline.
        output_dir: Directory to write output files.
        include_frontmatter: Whether to include YAML frontmatter.

    Returns:
        Path to the generated markdown file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []

    # Frontmatter
    if include_frontmatter:
        parts.append(emit_frontmatter(result.metadata))
        parts.append("")

    # Process each page
    for page_idx, page in enumerate(result.pages):
        if page_idx > 0:
            parts.append("")  # Page break gap

        # Merge consecutive code blocks into single fenced blocks
        i = 0
        page_blocks = page.blocks
        while i < len(page_blocks):
            block = page_blocks[i]

            if block.block_type == BlockType.CODE_BLOCK:
                # Collect consecutive code blocks
                code_group = [block]
                j = i + 1
                while j < len(page_blocks) and page_blocks[j].block_type == BlockType.CODE_BLOCK:
                    code_group.append(page_blocks[j])
                    j += 1

                # Merge all code texts into a single fenced block
                lang = ""
                code_lines = []
                for cb in code_group:
                    if cb.code_language and not lang:
                        lang = cb.code_language
                    text = cb.text_block.text if cb.text_block else ""
                    code_lines.extend(text.split("\n"))

                # Strip bare-number-only lines (PDF line counters like "4", "7", "9")
                code_lines = [l for l in code_lines if not re.match(r'^\s*\d{1,3}\s*$', l)]

                # Strip leading line numbers globally (e.g., "1 def foo():" → "def foo():")
                numbered_count = sum(1 for l in code_lines if re.match(r'^\d{1,3}\s+\S', l))
                non_empty = [l for l in code_lines if l.strip()]
                if numbered_count >= 2 and non_empty and numbered_count >= len(non_empty) * 0.4:
                    code_lines = [
                        re.sub(r'^\d{1,3}\s+', '', l) if re.match(r'^\d{1,3}\s+\S', l) else l
                        for l in code_lines
                    ]

                # Clean up: remove leading/trailing empty lines
                while code_lines and not code_lines[0].strip():
                    code_lines.pop(0)
                while code_lines and not code_lines[-1].strip():
                    code_lines.pop()
                code_text = "\n".join(code_lines)

                parts.append(f"```{lang}\n{code_text}\n```")
                parts.append("")
                i = j
            else:
                md = emit_block(block)
                if md:
                    parts.append(md)
                    parts.append("")  # Block separator
                i += 1

    # Footnotes at the end
    footnotes = []
    for page in result.pages:
        for block in page.blocks:
            if block.block_type == BlockType.FOOTNOTE:
                footnotes.append(emit_block(block))
    if footnotes:
        parts.append("")
        parts.append("---")
        parts.append("")
        for fn in footnotes:
            parts.append(fn)

    raw_md = "\n".join(parts)
    polished = polish_markdown(raw_md)

    # Write markdown file
    md_filename = result.metadata.source_filename.replace(".pdf", ".md") or "document.md"
    md_path = output_dir / md_filename
    md_path.write_text(polished, encoding="utf-8")

    logger.info(f"Markdown written to: {md_path} ({len(polished)} chars)")
    return md_path


def create_output_zip(output_dir: Path) -> Path:
    """Create a ZIP archive of the output directory.

    Args:
        output_dir: Directory containing markdown + images.

    Returns:
        Path to the ZIP file.
    """
    zip_path = output_dir.with_suffix(".zip")

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(output_dir.parent)
                zf.write(str(file_path), str(arcname))

    logger.info(f"ZIP created: {zip_path}")
    return zip_path
