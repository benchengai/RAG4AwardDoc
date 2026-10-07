import fitz
from rag import PDF, build

text = "".join(page.get_text() for page in fitz.open(PDF))
chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
build("retail_v1", chunks)