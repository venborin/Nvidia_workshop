"""Your own documents: drop them in mine/, run this, and they are ready.

    python convert.py

Drag PDF, Word (.docx), Markdown or text files from your laptop onto the
mine/ folder in the file tree (or right-click mine/ and choose Upload). This
script writes a .txt next to each one and prints one line per file: how many
pages it had and how much text came out. A PDF that yields almost no text is
a scanned image; the line says so, and the sample corpus is always enough.

mine/ is listed in .gitignore, so nothing in it is ever committed or pushed.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINE = ROOT / "mine"
MINE.mkdir(exist_ok=True)


def from_pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n\n".join(pages).strip(), len(pages)


def from_docx(path):
    import docx
    d = docx.Document(str(path))
    return "\n".join(p.text for p in d.paragraphs).strip(), None


def from_text(path):
    return path.read_text(errors="replace").strip(), None


READERS = {".pdf": from_pdf, ".docx": from_docx, ".md": from_text, ".markdown": from_text}

files = sorted(p for p in MINE.iterdir()
               if p.is_file() and p.suffix.lower() in READERS and p.name.lower() != "readme.md")  # mine/README.md is the folder's note, not a document
if not files:
    print("Nothing to convert yet. Drop PDF, .docx or .md files into mine/ and run this again.")
    print("Plain .txt files in mine/ need no conversion.")
    sys.exit(0)

for path in files:
    out = path.with_suffix(".txt")
    try:
        text, pages = READERS[path.suffix.lower()](path)
    except Exception as err:
        print(f"{path.name}: could not read ({str(err)[:60]}); skipped")
        continue
    out.write_text(text)
    words = len(text.split())
    where = f"{pages} pages, " if pages else ""
    verdict = ""
    if words < 50:
        verdict = "   almost no text: probably a scanned image, use the sample corpus for this one"
    elif words > 6000:
        verdict = "   long: the labs work best under about three pages, consider trimming"
    print(f"{path.name}: {where}{words} words -> {out.name}{verdict}")

print(f"\nDone. {len(files)} file(s) converted. For PDFs, Stop 3 reads them directly: python 03_lit/pdfask.py")
