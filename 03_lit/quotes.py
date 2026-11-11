"""Stop 3: a PDF's text page by page, and finding a quote in it. No model, no network.

The same three functions as pdfask.py (copied, so that pages.py and
check_values.py run without a model connection), used by:

    03_lit/pages.py          prints a paper's text with === page N === markers
    03_lit/check_values.py   checks every quote in results/values.csv against that text
"""
import re


def pdf_pages(path):
    """The text of each page, in order. pypdf reads the text layer the PDF already has;
    a scanned page has none, so it comes back nearly empty."""
    from pypdf import PdfReader
    return [(page.extract_text() or "") for page in PdfReader(str(path)).pages]


def normal(text):
    """Text reduced for matching: ligatures and curly quotes made plain, words broken
    across lines by a hyphen joined again, and all spacing made single spaces."""
    for a, b in {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
                 "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-",
                 "—": "-", "−": "-", " ": " ", "­": ""}.items():
        text = text.replace(a, b)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return " ".join(text.split())


def find_quote(quote, pages):
    """The page (counting from 1) where the quote appears word for word, or 0.
    Also tries the whole paper at once, for a sentence that runs across a page break (-1)."""
    q = normal(quote)
    if len(q) < 12:
        return 0
    for number, text in enumerate(pages, 1):
        if q in normal(text):
            return number
    return -1 if q in normal(" ".join(pages)) else 0


def scanned(pages):
    """True when a PDF has almost no text layer: a picture of pages."""
    chars = sum(len(p.strip()) for p in pages)
    return chars < 200 * max(1, len(pages)) / 4
