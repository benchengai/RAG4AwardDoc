"""Build the v2 index: the PDF converted to Markdown, cut into 500-character chunks.

Run once with `python build_v2.py` before `python run.py v2`. The only change
from v1 is the text extraction: pymupdf4llm turns the PDF into Markdown, so pay
tables come out as rows like "|Retail Employee Level 1|27.81|34.76|...|".
Chunking stays at a fixed 500 characters, so any score change comes from the
extraction alone.
"""
import pymupdf4llm
from rag import build

PDF = "retail.pdf"

# Headings are detected from font sizes (the default): retail.pdf has no
# bookmarks, so TocHeaders would find none.
md_text = pymupdf4llm.to_markdown(PDF)
# Same fixed 500-character cut as v1, so only the extraction changes.
chunks = [md_text[i:i + 500] for i in range(0, len(md_text), 500)]
# Embed the chunks and store them as the "retail_v2" collection in ./db.
build("retail_v2", chunks)
