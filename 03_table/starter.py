"""Module 3: from one document to one record.

    python 03_table/starter.py                  the sample document
    python 03_table/starter.py corpus/doc_013.txt   the one with missing values (stretch)

Your edit is not in this file. It is the two marked lines in records.py:
the name of your column and its one-line description. This program fills the
record for one document and prints it, field by field, excerpt last.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from docs import load               # noqa: E402
from llm import ask_json            # noqa: E402
from records import Record, FIELDS  # noqa: E402

DOCUMENT = sys.argv[1] if len(sys.argv) > 1 else "corpus/doc_001.txt"

RULES = (
    "You fill in one record for one research document. Copy doc_id and source exactly as given. "
    "The excerpt must be one sentence copied word for word from the document that supports main_claim. "
    "If the document does not state a value, write exactly: not stated. Never guess."
)


def excerpt_found(excerpt, text):
    """True if the excerpt appears word for word in the text. Spacing and line
    breaks are ignored; every word and every punctuation mark must match."""
    excerpt, text = " ".join(excerpt.split()), " ".join(text.split())
    return bool(excerpt) and excerpt in text


def where(path):
    """The file's path from the top of the repository (corpus/doc_001.txt,
    mine/notes.txt), or the full path for a file outside it."""
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def make_record(doc, path):
    """Fill one record for one document. doc_id and source are set here from
    the file itself, so a record always points at the file it came from."""
    source = where(path)
    prompt = f"Document id: {doc['doc_id']}\nSource file: {source}\n\n{doc['text']}"
    record = ask_json(prompt, Record, system=RULES)
    record.doc_id, record.source = doc["doc_id"], source
    return record


def short_error(err):
    """One line for a failed document: the kind of error and its first line,
    with anything that looks like a key or token removed."""
    first = (str(err).strip().splitlines() or [""])[0]
    first = re.sub(r"\b(sk|nvapi)-[A-Za-z0-9_\-]+|Bearer\s+\S+|\b[A-Za-z0-9_\-]{24,}", "[removed]", first)
    return f"{type(err).__name__}: {first}"[:160]


if __name__ == "__main__":
    doc = load(DOCUMENT)
    record = make_record(doc, DOCUMENT)
    width = max(len(f) for f in FIELDS)
    for field in [f for f in FIELDS if f != "excerpt"] + ["excerpt"]:
        print(f"{field:<{width}}  {getattr(record, field)}")
    print()
    print("Is the excerpt really in the document?",
          "yes" if excerpt_found(record.excerpt, doc["text"]) else "NO, check it")
