"""Reading documents. Supplied; nothing to change here.

    from docs import load, folder
    d = load("corpus/doc_001.txt")   -> {"doc_id", "source", "title", "year", "text"}
    folder("corpus")                 -> a list of those, sorted by file name
    folder("mine")                   -> your own documents, after convert.py

A document is a plain text file. If it starts with "Title:" and "Year:" lines,
those are read; otherwise title and year are "not stated" and the model is
asked to find them. The doc_id is the file name without its extension.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(path):
    path = Path(path)
    text = path.read_text(errors="replace").strip()
    title = year = "not stated"
    head = text[:400]
    m = re.search(r"^Title:\s*(.+)$", head, flags=re.M)
    if m:
        title = m.group(1).strip()
    m = re.search(r"^Year:\s*(.+)$", head, flags=re.M)
    if m:
        year = m.group(1).strip()
    return {"doc_id": path.stem, "source": path.name, "title": title, "year": year, "text": text}


def folder(path):
    path = ROOT / path if not Path(path).is_absolute() else Path(path)
    files = sorted(p for p in path.glob("*.txt") if p.is_file())
    if not files:
        raise SystemExit(f"No .txt files in {path}. For your own documents: put them in mine/ and run  python convert.py")
    return [load(p) for p in files]


def body(doc):
    """The text with the header lines removed, for prompts that get the header separately."""
    return re.sub(r"^(Title|Year|Field):.*\n", "", doc["text"], flags=re.M).strip()
