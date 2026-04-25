"""
Generate test PDF fixtures for PD2MD testing.

Run this script once to create all test PDFs in the fixtures/ directory.
Uses PyMuPDF to programmatically create PDFs with known content,
so we can verify extraction results deterministically.
"""

from pathlib import Path
import fitz  # PyMuPDF


FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)


def create_simple_text_pdf():
    """Test #1: Simple single-column text with headings and paragraphs."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Title (large, bold)
    page.insert_text(
        (72, 72),
        "Document Title",
        fontname="helv",
        fontsize=24,
        color=(0, 0, 0),
    )

    # Subtitle / Author
    page.insert_text(
        (72, 110),
        "By John Doe",
        fontname="helv",
        fontsize=14,
        color=(0.3, 0.3, 0.3),
    )

    # Section heading
    page.insert_text(
        (72, 160),
        "1. Introduction",
        fontname="helv",
        fontsize=16,
        color=(0, 0, 0),
    )

    # Paragraph
    body_text = (
        "This is the first paragraph of the document. It contains regular text "
        "that should be extracted accurately. Every word matters for AI consumption, "
        "so the converter must preserve content exactly as written."
    )
    rc = page.insert_textbox(
        fitz.Rect(72, 180, 523, 260),
        body_text,
        fontname="helv",
        fontsize=11,
        color=(0, 0, 0),
    )

    # Second paragraph
    body_text2 = (
        "This is the second paragraph, separated from the first by a gap. "
        "Paragraph detection should identify these as two distinct blocks. "
        "Numbers like 3.14159 and special chars like & < > should be preserved."
    )
    rc = page.insert_textbox(
        fitz.Rect(72, 270, 523, 350),
        body_text2,
        fontname="helv",
        fontsize=11,
        color=(0, 0, 0),
    )

    # Sub-section heading
    page.insert_text(
        (72, 380),
        "1.1 Background",
        fontname="helv",
        fontsize=14,
        color=(0, 0, 0),
    )

    # More text
    body_text3 = (
        "Background information goes here. This section tests sub-heading "
        "detection based on font size differences relative to the body text."
    )
    rc = page.insert_textbox(
        fitz.Rect(72, 400, 523, 460),
        body_text3,
        fontname="helv",
        fontsize=11,
        color=(0, 0, 0),
    )

    # Second section
    page.insert_text(
        (72, 490),
        "2. Methods",
        fontname="helv",
        fontsize=16,
        color=(0, 0, 0),
    )

    body_text4 = (
        "The methods section describes the technical approach used. "
        "Content accuracy is paramount for AI/LLM consumption use cases."
    )
    rc = page.insert_textbox(
        fitz.Rect(72, 510, 523, 570),
        body_text4,
        fontname="helv",
        fontsize=11,
        color=(0, 0, 0),
    )

    path = FIXTURES_DIR / "simple_text.pdf"
    doc.save(str(path))
    doc.close()
    print(f"Created: {path}")


def create_formatted_text_pdf():
    """Test #9: Document with bold, italic, and mixed formatting."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    y = 72

    # Title
    page.insert_text((72, y), "Formatted Document", fontname="helv", fontsize=20)
    y += 50

    # Bold text
    page.insert_text((72, y), "This text is bold.", fontname="helv", fontsize=11)
    # Create a bold version by using helvetica-bold
    # PyMuPDF fontname "hebo" = Helvetica-Bold
    y += 25
    page.insert_text((72, y), "Bold text here.", fontname="hebo", fontsize=11)

    y += 25
    # Italic
    page.insert_text((72, y), "Italic text here.", fontname="heit", fontsize=11)

    y += 25
    # Bold-Italic
    page.insert_text((72, y), "Bold-Italic text here.", fontname="hebi", fontsize=11)

    y += 25
    # Monospace (Courier)
    page.insert_text((72, y), "code_variable = 42", fontname="cour", fontsize=11)

    y += 40
    # Mixed line — we'll simulate with separate positioned inserts
    page.insert_text((72, y), "Normal ", fontname="helv", fontsize=11)
    page.insert_text((115, y), "bold ", fontname="hebo", fontsize=11)
    page.insert_text((143, y), "normal ", fontname="helv", fontsize=11)
    page.insert_text((185, y), "italic ", fontname="heit", fontsize=11)
    page.insert_text((220, y), "end.", fontname="helv", fontsize=11)

    path = FIXTURES_DIR / "formatted_text.pdf"
    doc.save(str(path))
    doc.close()
    print(f"Created: {path}")


def create_table_pdf():
    """Test #3: Document with a bordered table."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    page.insert_text((72, 60), "Table Example", fontname="helv", fontsize=18)

    # Draw a simple 3-column, 4-row table
    table_x = 72
    table_y = 90
    col_widths = [150, 150, 150]
    row_height = 25
    num_rows = 4

    # Table data
    data = [
        ["Name", "Age", "City"],
        ["Alice", "30", "New York"],
        ["Bob", "25", "London"],
        ["Charlie", "35", "Tokyo"],
    ]

    # Draw grid lines and text
    for row_idx in range(num_rows + 1):
        y = table_y + row_idx * row_height
        # Horizontal line
        page.draw_line(
            fitz.Point(table_x, y),
            fitz.Point(table_x + sum(col_widths), y),
            color=(0, 0, 0),
            width=1,
        )

    for col_idx in range(len(col_widths) + 1):
        x = table_x + sum(col_widths[:col_idx])
        # Vertical line
        page.draw_line(
            fitz.Point(x, table_y),
            fitz.Point(x, table_y + num_rows * row_height),
            color=(0, 0, 0),
            width=1,
        )

    # Insert text in cells
    for row_idx, row_data in enumerate(data):
        for col_idx, cell_text in enumerate(row_data):
            x = table_x + sum(col_widths[:col_idx]) + 5
            y = table_y + row_idx * row_height + 17
            fn = "hebo" if row_idx == 0 else "helv"
            page.insert_text((x, y), cell_text, fontname=fn, fontsize=10)

    # Text after table
    page.insert_text(
        (72, table_y + num_rows * row_height + 40),
        "Text after the table should be extracted correctly.",
        fontname="helv",
        fontsize=11,
    )

    path = FIXTURES_DIR / "bordered_table.pdf"
    doc.save(str(path))
    doc.close()
    print(f"Created: {path}")


def create_with_images_pdf():
    """Test #2: Document with embedded images."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    page.insert_text((72, 60), "Document with Images", fontname="helv", fontsize=18)

    page.insert_text(
        (72, 100),
        "Below is an embedded image:",
        fontname="helv",
        fontsize=11,
    )

    # Create a simple colored rectangle image using Pillow, then embed
    from PIL import Image as PILImage
    import io

    img = PILImage.new("RGB", (200, 100), color=(65, 105, 225))  # Royal blue
    # Draw a simple pattern
    for x in range(200):
        for y in range(100):
            if (x + y) % 20 < 10:
                img.putpixel((x, y), (255, 215, 0))  # Gold checkerboard

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Insert image into PDF
    img_rect = fitz.Rect(72, 120, 272, 220)
    page.insert_image(img_rect, stream=img_bytes.getvalue())

    page.insert_text(
        (72, 245),
        "Figure 1: A test pattern image",
        fontname="heit",
        fontsize=10,
        color=(0.3, 0.3, 0.3),
    )

    page.insert_text(
        (72, 280),
        "Text continues after the image.",
        fontname="helv",
        fontsize=11,
    )

    path = FIXTURES_DIR / "with_images.pdf"
    doc.save(str(path))
    doc.close()
    print(f"Created: {path}")


def create_multipage_pdf():
    """Test #17 (lite): Multi-page document for cross-page testing."""
    doc = fitz.open()

    for page_num in range(3):
        page = doc.new_page(width=595, height=842)

        # Running header
        page.insert_text(
            (72, 30),
            "PD2MD Test Document",
            fontname="helv",
            fontsize=9,
            color=(0.5, 0.5, 0.5),
        )

        # Page number
        page.insert_text(
            (520, 810),
            f"Page {page_num + 1}",
            fontname="helv",
            fontsize=9,
            color=(0.5, 0.5, 0.5),
        )

        # Content
        page.insert_text(
            (72, 72),
            f"Chapter {page_num + 1}",
            fontname="helv",
            fontsize=18,
        )

        text = (
            f"This is the content of chapter {page_num + 1}. "
            f"Each page has a running header and page number that should be "
            f"detected and filtered out. The body content should be extracted "
            f"in the correct reading order across pages."
        )
        page.insert_textbox(
            fitz.Rect(72, 100, 523, 200),
            text,
            fontname="helv",
            fontsize=11,
        )

    path = FIXTURES_DIR / "multipage.pdf"
    doc.save(str(path))
    doc.close()
    print(f"Created: {path}")


def create_with_lists_pdf():
    """Test #10: Document with bullet and numbered lists."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    y = 60
    page.insert_text((72, y), "Lists Example", fontname="helv", fontsize=18)
    y += 40

    page.insert_text((72, y), "Unordered list:", fontname="helv", fontsize=11)
    y += 20

    bullets = ["First item", "Second item", "Third item with more text"]
    for item in bullets:
        page.insert_text((90, y), "\u2022", fontname="helv", fontsize=11)
        page.insert_text((105, y), item, fontname="helv", fontsize=11)
        y += 18

    y += 15
    page.insert_text((72, y), "Ordered list:", fontname="helv", fontsize=11)
    y += 20

    for i, item in enumerate(["Alpha step", "Beta step", "Gamma step"], 1):
        page.insert_text((90, y), f"{i}.", fontname="helv", fontsize=11)
        page.insert_text((108, y), item, fontname="helv", fontsize=11)
        y += 18

    path = FIXTURES_DIR / "with_lists.pdf"
    doc.save(str(path))
    doc.close()
    print(f"Created: {path}")


if __name__ == "__main__":
    create_simple_text_pdf()
    create_formatted_text_pdf()
    create_table_pdf()
    create_with_images_pdf()
    create_multipage_pdf()
    create_with_lists_pdf()
    print("\nAll test PDFs generated!")
