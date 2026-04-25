"""Quick diagnostic to show block structure for definitions PDF."""
from pathlib import Path
from backend.app.pipeline.extractor import PDFExtractor
from backend.app.pipeline.assembler import assemble_page

ext = PDFExtractor()
pages = ext.extract(Path("test_docs/pdfs/20_definitions.pdf"))
for p in pages[:1]:
    blocks, fc = assemble_page(p)
    for i, b in enumerate(blocks):
        bold_info = ""
        if b.lines:
            spans = b.lines[0].spans
            if len(spans) > 1:
                bold_info = f"  [spans: {len(spans)}, first_bold={spans[0].is_bold}, first_text={spans[0].text[:30]!r}]"
            elif len(spans) == 1:
                bold_info = f"  [1 span, bold={spans[0].is_bold}]"
        print(f"Block {i}: {len(b.lines)}L | {b.text[:70]!r}{bold_info}")
