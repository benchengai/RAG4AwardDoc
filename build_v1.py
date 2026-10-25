"""Build the v1 index: plain PDF text cut into fixed 500-character chunks.

Run once with `python build_v1.py` before `python run.py v1`. This is the
baseline the later versions are compared against: no overlap, no metadata,
and chunk boundaries that ignore clauses and tables, which is what breaks the
pay rate tables.
"""
import fitz  # PyMuPDF
from rag import build

PDF = "retail.pdf"

# Extract the text of every page and join it into one long string.
text = "".join(page.get_text() for page in fitz.open(PDF))
# Cut every 500 characters, wherever that lands: mid-word, mid-table.
chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
# Embed the chunks and store them as the "retail_v1" collection in ./db.
build("retail_v1", chunks)
