"""
Layer 1: Raw PDF Extraction.

Extracts all raw content from a PDF using PyMuPDF:
  - Document metadata
  - Per-page text at glyph level (characters with positions, fonts, styles)
  - Embedded images (raster)
  - Vector paths (lines, rectangles — for table border detection)
  - Page classification (digital vs scanned)

This layer's output is the foundation for ALL downstream processing.
Content accuracy is the #1 priority — every character must be correct.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image as PILImage

from backend.app.models.document import (
    BBox,
    DocumentMetadata,
    ExtractedImage,
    PageType,
    RawGlyph,
    VectorPath,
)
from backend.app.utils.fonts import is_bold_font, is_italic_font, is_monospace_font

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 1.1 — Document Metadata Extraction
# ---------------------------------------------------------------------------

def extract_metadata(doc: fitz.Document) -> DocumentMetadata:
    """Extract document-level metadata from the PDF's /Info dictionary and structure.

    Args:
        doc: An open PyMuPDF document.

    Returns:
        DocumentMetadata populated with all available fields.
    """
    meta = doc.metadata or {}

    # Check if the PDF has a structure tree (tagged PDF)
    is_tagged = False
    try:
        catalog = doc.pdf_catalog()
        if catalog:
            # Check for /MarkInfo with /Marked = true
            mark_info = doc.xref_get_key(catalog, "MarkInfo")
            if mark_info and mark_info[0] != "null":
                is_tagged = True
    except Exception:
        pass  # Not a strict requirement

    return DocumentMetadata(
        title=meta.get("title", "") or "",
        author=meta.get("author", "") or "",
        subject=meta.get("subject", "") or "",
        keywords=meta.get("keywords", "") or "",
        creator=meta.get("creator", "") or "",
        producer=meta.get("producer", "") or "",
        creation_date=meta.get("creationDate", "") or "",
        modification_date=meta.get("modDate", "") or "",
        page_count=doc.page_count,
        is_tagged=is_tagged,
        is_encrypted=doc.is_encrypted,
    )


# ---------------------------------------------------------------------------
# Step 1.2 — Per-Page Text Extraction (Glyph Level)
# ---------------------------------------------------------------------------

def extract_page_glyphs(page: fitz.Page) -> list[RawGlyph]:
    """Extract every character from a page with full metadata.

    Uses PyMuPDF's "rawdict" mode to get individual character data including
    exact bounding boxes, font information, and styling.

    Args:
        page: A PyMuPDF page object.

    Returns:
        List of RawGlyph objects, one per character, in file order.
        (Reading order is established later in Layer 3.)
    """
    glyphs: list[RawGlyph] = []

    try:
        text_dict = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_LIGATURES)
    except Exception as e:
        logger.error(f"Failed to extract text from page {page.number}: {e}")
        return glyphs

    for block in text_dict.get("blocks", []):
        # Skip image blocks — we handle images separately in Step 1.3
        if block.get("type") != 0:  # type 0 = text, type 1 = image
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font_name = span.get("font", "")
                font_size = span.get("size", 0.0)
                font_flags = span.get("flags", 0)
                origin_y = span.get("origin", (0, 0))[1]

                # Determine styling from font name and flags
                bold = is_bold_font(font_name, font_flags)
                italic = is_italic_font(font_name, font_flags)
                mono = is_monospace_font(font_name, font_flags)

                # Parse color (PyMuPDF gives it as an int)
                color_int = span.get("color", 0)
                color_r = (color_int >> 16) & 0xFF
                color_g = (color_int >> 8) & 0xFF
                color_b = color_int & 0xFF

                # Extract individual characters from the span
                for char_info in span.get("chars", []):
                    c = char_info.get("c", "")
                    if not c:
                        continue

                    bbox_raw = char_info.get("bbox", (0, 0, 0, 0))
                    char_origin_y = char_info.get("origin", (0, origin_y))[1]

                    glyph = RawGlyph(
                        char=c,
                        bbox=BBox(
                            x0=bbox_raw[0],
                            y0=bbox_raw[1],
                            x1=bbox_raw[2],
                            y1=bbox_raw[3],
                        ),
                        font_name=font_name,
                        font_size=font_size,
                        is_bold=bold,
                        is_italic=italic,
                        is_monospace=mono,
                        color=(color_r, color_g, color_b),
                        origin_y=char_origin_y,
                    )
                    glyphs.append(glyph)

    return glyphs


# ---------------------------------------------------------------------------
# Step 1.3 — Image Extraction
# ---------------------------------------------------------------------------

def extract_page_images(
    page: fitz.Page,
    doc: fitz.Document,
    output_dir: Path,
    page_number: int,
    image_format: str = "png",
    jpeg_quality: int = 85,
) -> list[ExtractedImage]:
    """Extract all embedded raster images from a page.

    Each image is saved to disk and an ExtractedImage record is created
    with its bounding box on the page for later placement in Markdown.

    Args:
        page: A PyMuPDF page object.
        doc: The parent document (needed for xref-based extraction).
        output_dir: Directory to save extracted images.
        page_number: 0-based page number.
        image_format: "png" or "jpeg".
        jpeg_quality: JPEG quality if format is "jpeg".

    Returns:
        List of ExtractedImage objects.
    """
    images: list[ExtractedImage] = []
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    try:
        image_list = page.get_images(full=True)
    except Exception as e:
        logger.error(f"Failed to get images from page {page_number}: {e}")
        return images

    for img_idx, img_info in enumerate(image_list):
        xref = img_info[0]

        try:
            # Extract the image data
            base_image = doc.extract_image(xref)
            if not base_image:
                logger.warning(f"Could not extract image xref={xref} on page {page_number}")
                continue

            img_bytes = base_image["image"]
            img_ext = base_image.get("ext", "png")
            img_width = base_image.get("width", 0)
            img_height = base_image.get("height", 0)
            color_space_val = base_image.get("colorspace", 0)
            bpc = base_image.get("bpc", 8)

            # Determine color space name
            if isinstance(color_space_val, int):
                cs_map = {1: "Gray", 3: "RGB", 4: "CMYK"}
                color_space = cs_map.get(color_space_val, f"CS({color_space_val})")
            else:
                color_space = str(color_space_val)

            # Get the image's bounding box on the page
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    r = rects[0]  # Take the first occurrence
                    bbox = BBox(x0=r.x0, y0=r.y0, x1=r.x1, y1=r.y1)
                else:
                    bbox = BBox(x0=0, y0=0, x1=float(img_width), y1=float(img_height))
            except Exception:
                bbox = BBox(x0=0, y0=0, x1=float(img_width), y1=float(img_height))

            # Convert and save the image
            try:
                pil_img = PILImage.open(io.BytesIO(img_bytes))

                # Convert CMYK to RGB
                if pil_img.mode == "CMYK":
                    pil_img = pil_img.convert("RGB")
                elif pil_img.mode not in ("RGB", "RGBA", "L"):
                    pil_img = pil_img.convert("RGB")

                # Determine output format and filename
                if image_format.lower() == "jpeg":
                    out_ext = "jpg"
                    save_kwargs = {"quality": jpeg_quality, "optimize": True}
                    if pil_img.mode == "RGBA":
                        pil_img = pil_img.convert("RGB")
                else:
                    out_ext = "png"
                    save_kwargs = {"optimize": True}

                filename = f"page{page_number + 1}_img{img_idx + 1}.{out_ext}"
                save_path = images_dir / filename
                pil_img.save(str(save_path), **save_kwargs)

            except Exception as e:
                # Fallback: save raw bytes with original extension
                logger.warning(f"PIL conversion failed for xref={xref}, saving raw: {e}")
                filename = f"page{page_number + 1}_img{img_idx + 1}.{img_ext}"
                save_path = images_dir / filename
                save_path.write_bytes(img_bytes)

            extracted = ExtractedImage(
                image_index=img_idx,
                page_number=page_number,
                bbox=bbox,
                xref=xref,
                width=img_width,
                height=img_height,
                color_space=color_space,
                bits_per_component=bpc,
                saved_path=save_path,
            )
            images.append(extracted)

        except Exception as e:
            logger.error(f"Failed to extract image xref={xref} on page {page_number}: {e}")
            continue

    return images


# ---------------------------------------------------------------------------
# Step 1.4 — Vector Path Extraction (for Table Detection)
# ---------------------------------------------------------------------------

def extract_page_vectors(page: fitz.Page) -> list[VectorPath]:
    """Extract vector drawing elements (lines, rectangles) from a page.

    These are used downstream for:
      - Table border detection (horizontal + vertical lines forming a grid)
      - Background shading detection (filled rectangles behind text)
      - Horizontal rule detection

    Args:
        page: A PyMuPDF page object.

    Returns:
        List of VectorPath objects. Short decorative elements are filtered out.
    """
    vectors: list[VectorPath] = []
    MIN_LINE_LENGTH = 10.0  # Ignore tiny decorative marks

    try:
        drawings = page.get_drawings()
    except Exception as e:
        logger.error(f"Failed to get drawings from page {page.number}: {e}")
        return vectors

    for drawing in drawings:
        items = drawing.get("items", [])
        rect = drawing.get("rect")
        stroke_color = drawing.get("color")  # stroke color
        fill_color = drawing.get("fill")     # fill color
        width = drawing.get("width", 0.0)

        if not rect:
            continue

        bbox = BBox(x0=rect.x0, y0=rect.y0, x1=rect.x1, y1=rect.y1)

        # Skip tiny marks
        if bbox.width < MIN_LINE_LENGTH and bbox.height < MIN_LINE_LENGTH:
            continue

        # Convert colors to RGB tuples
        def color_to_rgb(c) -> tuple[int, int, int] | None:
            if c is None:
                return None
            if isinstance(c, (list, tuple)):
                if len(c) == 3:
                    return (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
                elif len(c) == 1:
                    v = int(c[0] * 255)
                    return (v, v, v)
            return (0, 0, 0)

        sc = color_to_rgb(stroke_color)
        fc = color_to_rgb(fill_color)

        # Determine path type and geometry
        is_horizontal = bbox.height < 3.0 and bbox.width >= MIN_LINE_LENGTH
        is_vertical = bbox.width < 3.0 and bbox.height >= MIN_LINE_LENGTH

        if is_horizontal or is_vertical:
            path_type = "line"
        elif fc is not None and bbox.area > 100:
            path_type = "rect"
        else:
            path_type = "curve"

        # Collect raw points from items
        points: list[tuple[float, float]] = []
        for item in items:
            op = item[0]  # operator: "l" (line), "re" (rect), "c" (curve), "m" (move)
            if op == "l" and len(item) >= 3:
                points.append((item[1].x, item[1].y))
                points.append((item[2].x, item[2].y))
            elif op == "re" and len(item) >= 2:
                r = item[1]
                points.append((r.x0, r.y0))
                points.append((r.x1, r.y1))
            elif op == "m" and len(item) >= 2:
                points.append((item[1].x, item[1].y))

        vector = VectorPath(
            path_type=path_type,
            bbox=bbox,
            stroke_color=sc,
            fill_color=fc,
            line_width=width,
            is_horizontal=is_horizontal,
            is_vertical=is_vertical,
            points=points,
        )
        vectors.append(vector)

    return vectors


# ---------------------------------------------------------------------------
# Step 1.5 — Page Classification
# ---------------------------------------------------------------------------

def classify_page(page: fitz.Page, min_char_threshold: int = 20) -> PageType:
    """Classify a page as DIGITAL, SCANNED, or MIXED.

    A digital page has extractable text. A scanned page is image-only.
    A mixed page has some text but also large image regions.

    Args:
        page: A PyMuPDF page object.
        min_char_threshold: Minimum characters to consider a page as having text.

    Returns:
        PageType classification.
    """
    # Count extractable text characters
    text = page.get_text("text")
    char_count = len(text.strip())

    # Count images
    images = page.get_images(full=False)
    has_images = len(images) > 0

    if char_count >= min_char_threshold:
        if has_images:
            # Check if images cover most of the page
            total_image_area = 0.0
            page_area = page.rect.width * page.rect.height
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    rects = page.get_image_rects(xref)
                    for r in rects:
                        total_image_area += r.width * r.height
                except Exception:
                    pass

            if total_image_area > page_area * 0.7:
                return PageType.MIXED
        return PageType.DIGITAL
    elif has_images:
        return PageType.SCANNED
    else:
        # No text and no images — probably a blank or vector-only page
        return PageType.DIGITAL  # Treat as digital (may just be empty)


# ---------------------------------------------------------------------------
# Full Page Extraction (combines all steps)
# ---------------------------------------------------------------------------

def extract_page(
    page: fitz.Page,
    doc: fitz.Document,
    output_dir: Path,
    image_format: str = "png",
    jpeg_quality: int = 85,
) -> dict:
    """Extract all content from a single page.

    This is the main entry point for Layer 1 — it combines Steps 1.2-1.5
    into a single call per page.

    Args:
        page: A PyMuPDF page object.
        doc: The parent document.
        output_dir: Directory for saving extracted images.
        image_format: "png" or "jpeg".
        jpeg_quality: JPEG quality if using JPEG format.

    Returns:
        Dict with keys: glyphs, images, vectors, page_type, width, height
    """
    page_number = page.number

    return {
        "page_number": page_number,
        "width": page.rect.width,
        "height": page.rect.height,
        "page_type": classify_page(page),
        "glyphs": extract_page_glyphs(page),
        "images": extract_page_images(
            page, doc, output_dir, page_number, image_format, jpeg_quality
        ),
        "vectors": extract_page_vectors(page),
    }


def extract_document(
    pdf_path: Path,
    output_dir: Path,
    image_format: str = "png",
    jpeg_quality: int = 85,
) -> dict:
    """Extract all content from an entire PDF document.

    This is the top-level Layer 1 function that:
      1. Opens the PDF
      2. Extracts metadata
      3. Processes each page
      4. Returns the complete raw extraction

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory for outputs (images, etc).
        image_format: "png" or "jpeg".
        jpeg_quality: JPEG quality if using JPEG format.

    Returns:
        Dict with keys: metadata, pages
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Opening PDF: {pdf_path}")
    doc = fitz.open(str(pdf_path))

    try:
        metadata = extract_metadata(doc)
        metadata.source_filename = pdf_path.name

        logger.info(
            f"PDF opened: {doc.page_count} pages, "
            f"title='{metadata.title}', tagged={metadata.is_tagged}"
        )

        pages = []
        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            logger.info(f"Extracting page {page_idx + 1}/{doc.page_count}")

            page_data = extract_page(
                page, doc, output_dir, image_format, jpeg_quality
            )
            pages.append(page_data)

            glyph_count = len(page_data["glyphs"])
            image_count = len(page_data["images"])
            vector_count = len(page_data["vectors"])
            logger.info(
                f"  Page {page_idx + 1}: {glyph_count} glyphs, "
                f"{image_count} images, {vector_count} vectors, "
                f"type={page_data['page_type'].name}"
            )

        return {
            "metadata": metadata,
            "pages": pages,
        }

    finally:
        doc.close()
