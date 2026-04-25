"""
PD2MD Document Data Models.

These dataclasses define the Intermediate Representation (IR) that flows
between pipeline layers. Each layer consumes and produces these models,
making the pipeline fully modular and testable.

Hierarchy:
    DocumentResult
    └── PageResult
        ├── ContentBlock (semantically classified)
        │   └── TextBlock
        │       └── TextLine
        │           └── TextSpan (styled run of text)
        ├── ExtractedImage
        └── VectorPath
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BlockType(Enum):
    """Semantic classification for content blocks."""
    HEADING = auto()
    PARAGRAPH = auto()
    LIST_ITEM = auto()
    CODE_BLOCK = auto()
    TABLE = auto()
    IMAGE = auto()
    BLOCKQUOTE = auto()
    HORIZONTAL_RULE = auto()
    HEADER = auto()       # Running page header (excluded from output)
    FOOTER = auto()       # Running page footer (excluded from output)
    FOOTNOTE = auto()
    UNKNOWN = auto()


class PageType(Enum):
    """Classification of a PDF page based on extractable content."""
    DIGITAL = auto()      # Has extractable text
    SCANNED = auto()      # Image-only, no text (out of scope for now)
    MIXED = auto()        # Some text, some image regions


class ListStyle(Enum):
    """Type of list marker."""
    UNORDERED = auto()    # •, -, *, etc.
    ORDERED = auto()      # 1., a), (i), etc.


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class BBox:
    """Axis-aligned bounding box. Origin is top-left of the page.
    
    (x0, y0) = top-left corner
    (x1, y1) = bottom-right corner
    All coordinates are in PDF points (1 point = 1/72 inch).
    """
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2

    def overlaps(self, other: BBox) -> bool:
        """Check if this bbox overlaps with another."""
        return not (
            self.x1 <= other.x0 or other.x1 <= self.x0
            or self.y1 <= other.y0 or other.y1 <= self.y0
        )

    def contains(self, other: BBox) -> bool:
        """Check if this bbox fully contains another."""
        return (
            self.x0 <= other.x0 and self.y0 <= other.y0
            and self.x1 >= other.x1 and self.y1 >= other.y1
        )

    def merge(self, other: BBox) -> BBox:
        """Return the smallest bbox containing both."""
        return BBox(
            x0=min(self.x0, other.x0),
            y0=min(self.y0, other.y0),
            x1=max(self.x1, other.x1),
            y1=max(self.y1, other.y1),
        )

    def vertical_distance(self, other: BBox) -> float:
        """Vertical gap between this bbox's bottom and other's top."""
        return other.y0 - self.y1

    def as_tuple(self) -> tuple[float, float, float, float]:
        """Return as (x0, y0, x1, y1) tuple for library interop."""
        return (self.x0, self.y0, self.x1, self.y1)


# ---------------------------------------------------------------------------
# Layer 1 Output — Raw Extraction
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class RawGlyph:
    """A single character extracted from the PDF with full metadata.
    
    This is the atomic unit of extraction — everything else is built
    from collections of these.
    """
    char: str
    bbox: BBox
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    is_monospace: bool
    color: tuple[int, int, int]   # RGB 0-255
    origin_y: float               # Baseline y-coordinate (for superscript detection)


@dataclass(slots=True)
class ExtractedImage:
    """An image extracted from the PDF."""
    image_index: int              # Sequential index within the page
    page_number: int
    bbox: BBox
    xref: int                     # PDF cross-reference number
    width: int                    # Image pixel width
    height: int                   # Image pixel height
    color_space: str              # e.g., "RGB", "CMYK", "Gray"
    bits_per_component: int
    saved_path: Path | None = None  # Populated after saving to disk
    caption: str | None = None    # Associated caption text (set later)


@dataclass(slots=True)
class VectorPath:
    """A vector drawing element (line, rectangle, curve).
    
    Used primarily for detecting table borders and background shading.
    """
    path_type: str                # "line", "rect", "curve"
    bbox: BBox
    stroke_color: tuple[int, int, int] | None  # RGB if stroked
    fill_color: tuple[int, int, int] | None    # RGB if filled
    line_width: float
    # For lines specifically:
    is_horizontal: bool = False
    is_vertical: bool = False
    # Raw points for more complex analysis:
    points: list[tuple[float, float]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Layer 2 Output — Text Assembly
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class TextSpan:
    """A contiguous run of text with uniform styling.
    
    This is a word or part of a word where font, size, bold/italic
    are all consistent. The fundamental building block for emphasis detection.
    """
    text: str
    bbox: BBox
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    is_monospace: bool
    is_superscript: bool = False
    is_subscript: bool = False
    color: tuple[int, int, int] = (0, 0, 0)
    link_url: str | None = None   # Populated by link extraction


@dataclass(slots=True)
class TextLine:
    """A horizontal line of text, composed of one or more styled spans."""
    spans: list[TextSpan]
    bbox: BBox

    @property
    def text(self) -> str:
        """Plain text content of the entire line."""
        return "".join(span.text for span in self.spans)

    @property
    def dominant_font_size(self) -> float:
        """Most common font size in this line (by character count)."""
        if not self.spans:
            return 0.0
        size_counts: dict[float, int] = {}
        for span in self.spans:
            size_counts[span.font_size] = (
                size_counts.get(span.font_size, 0) + len(span.text)
            )
        return max(size_counts, key=size_counts.get)  # type: ignore[arg-type]

    @property
    def is_all_bold(self) -> bool:
        return all(s.is_bold for s in self.spans if s.text.strip())

    @property
    def is_all_italic(self) -> bool:
        return all(s.is_italic for s in self.spans if s.text.strip())


@dataclass(slots=True)
class TextBlock:
    """A group of consecutive lines forming a visual block on the page.
    
    This is the output of spatial clustering — lines that belong together
    visually. Not yet semantically classified (that happens in Layer 4).
    """
    lines: list[TextLine]
    bbox: BBox

    @property
    def text(self) -> str:
        """Plain text of all lines, joined with newlines."""
        return "\n".join(line.text for line in self.lines)

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def left_indent(self) -> float:
        """Left edge x-coordinate (useful for indent detection)."""
        if not self.lines:
            return 0.0
        return min(line.bbox.x0 for line in self.lines)


# ---------------------------------------------------------------------------
# Layer 3/4 Output — Semantic Classification
# ---------------------------------------------------------------------------

@dataclass
class TableCell:
    """A single cell in a table."""
    text: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    is_header: bool = False
    alignment: str = "left"  # "left", "center", "right"


@dataclass
class TableData:
    """Structured table data ready for Markdown conversion."""
    cells: list[TableCell]
    num_rows: int
    num_cols: int
    has_header: bool = True
    bbox: BBox | None = None

    def get_cell(self, row: int, col: int) -> TableCell | None:
        """Get cell at specific position."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def get_row(self, row: int) -> list[TableCell]:
        """Get all cells in a specific row."""
        return sorted(
            [c for c in self.cells if c.row == row],
            key=lambda c: c.col,
        )


@dataclass
class ContentBlock:
    """A semantically classified content block — the core IR unit for emission.
    
    This is what Layer 4 produces and Layer 6 (emitter) consumes.
    Every piece of content in the final Markdown corresponds to one ContentBlock.
    """
    block_type: BlockType
    bbox: BBox
    confidence: float = 1.0       # 0.0 - 1.0 confidence in classification

    # Text content (for HEADING, PARAGRAPH, LIST_ITEM, CODE_BLOCK, etc.)
    text_block: TextBlock | None = None

    # For headings
    heading_level: int = 0         # 1-6 for H1-H6

    # For lists
    list_style: ListStyle | None = None
    list_level: int = 0            # Nesting depth (0 = top-level)
    list_marker: str = ""          # Original marker text ("•", "1.", "a)")

    # For tables
    table_data: TableData | None = None

    # For images
    image_ref: ExtractedImage | None = None

    # For code blocks
    code_language: str = ""        # Detected language hint

    # For footnotes
    footnote_id: str = ""          # e.g., "1", "2", "*"
    footnote_text: str = ""

    @property
    def text(self) -> str:
        """Get plain text content regardless of block type."""
        if self.text_block:
            return self.text_block.text
        if self.table_data:
            return "[TABLE]"
        if self.image_ref:
            return f"[IMAGE: {self.image_ref.caption or 'untitled'}]"
        return ""


# ---------------------------------------------------------------------------
# Document-Level Models
# ---------------------------------------------------------------------------

@dataclass
class FontInfo:
    """Information about a single font used in the document."""
    name: str
    size: float
    is_bold: bool
    is_italic: bool
    is_monospace: bool
    char_count: int = 0           # How many characters use this font


@dataclass
class FontCatalog:
    """Catalog of all fonts used in the document with statistics.
    
    Used to determine the dominant body font and classify other fonts
    relative to it (headings, emphasis, code).
    """
    fonts: list[FontInfo] = field(default_factory=list)
    body_font: FontInfo | None = None    # Most-used font = body text
    body_font_size: float = 0.0

    def identify_body_font(self) -> None:
        """Set body_font to the most-used font by character count."""
        if not self.fonts:
            return
        self.body_font = max(self.fonts, key=lambda f: f.char_count)
        self.body_font_size = self.body_font.size


@dataclass
class DocumentMetadata:
    """Metadata extracted from the PDF's /Info dictionary."""
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    creator: str = ""            # Software that created the PDF
    producer: str = ""           # PDF library used
    creation_date: str = ""
    modification_date: str = ""
    page_count: int = 0
    is_tagged: bool = False      # Has structure tree (PDF/UA)
    is_encrypted: bool = False
    source_filename: str = ""


@dataclass
class QualityWarning:
    """A warning about potential quality issues in the conversion."""
    page_number: int
    category: str              # "encoding", "reading_order", "table", etc.
    message: str
    severity: str = "warning"  # "info", "warning", "error"


@dataclass
class PageResult:
    """Complete processed result for a single page."""
    page_number: int
    width: float
    height: float
    page_type: PageType
    blocks: list[ContentBlock] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    vectors: list[VectorPath] = field(default_factory=list)
    warnings: list[QualityWarning] = field(default_factory=list)


@dataclass
class DocumentResult:
    """Complete result of the entire PDF conversion."""
    metadata: DocumentMetadata
    pages: list[PageResult] = field(default_factory=list)
    font_catalog: FontCatalog = field(default_factory=FontCatalog)
    warnings: list[QualityWarning] = field(default_factory=list)

    @property
    def total_blocks(self) -> int:
        return sum(len(p.blocks) for p in self.pages)

    @property
    def total_images(self) -> int:
        return sum(len(p.images) for p in self.pages)

    @property
    def total_tables(self) -> int:
        return sum(
            1 for p in self.pages
            for b in p.blocks
            if b.block_type == BlockType.TABLE
        )
