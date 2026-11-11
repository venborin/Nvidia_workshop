"""Module 5's two tools: search the table, read one document. Supplied.

    python 05_agent/tools.py             test read_document alone on doc_001
    python 05_agent/tools.py doc_009     test it on another id

read_document returns the text of one document. That is where the planted
document matters: whatever a document says is evidence for the model to weigh,
never an instruction for it to follow. The program, not the document, decides
what tools exist and what they are allowed to do. Both tools only read, which
limits what the agent can change. They do not stop it repeating whatever it
can read, so read_document is also limited in what it can open: only a .txt
file directly inside corpus/ or mine/, named by its doc_id.
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# The same search tool as Module 4, loaded from its file (both files are
# called tools.py, so a plain import would find this one instead).
_spec = importlib.util.spec_from_file_location("module4_tools", Path(__file__).resolve().parents[1] / "04_tool" / "tools.py")
_m4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m4)
search_records = _m4.search_records
# The model sees a tool's name, parameters and docstring, nothing else. To try
# a different docstring for search here without editing Module 4, assign one on
# a line just below this comment:  search_records.__doc__ = """..."""


def use_saved_table():
    """Make search_records search the saved table, corpus/records.jsonl, for this
    run only. Your 03_table/records.jsonl is not touched. Same as --saved."""
    _m4.USE_SAVED = True


FOLDERS = [ROOT / "corpus", ROOT / "mine"]
LIMIT = 12000                                   # characters returned per read
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-][A-Za-z0-9_. -]*$")   # no slash, no backslash


def read_document(doc_id: str) -> str:
    """Return the text of one document, given its doc_id exactly as it appears
    in a search result (for example doc_004). Use this after a search, when the
    record's main_claim is not enough and you need the details: methods,
    numbers, limitations, or where two studies differ. At most the first 12000
    characters are returned; a longer document ends with a [truncated ...] line
    saying how much was left out."""
    name = str(doc_id).strip()
    if not SAFE_ID.match(name) or ".." in name:
        return f"error: {name!r} is not a doc_id. Use an id from a search result, for example doc_004."
    matches = []
    for folder in FOLDERS:
        base = folder.resolve()
        path = (folder / f"{name}.txt").resolve()   # follows any link, then checks where it landed
        if path.parent == base and path.is_file():
            matches.append(path)
    if not matches:
        return f"error: no document with doc_id {name!r}"
    if len(matches) > 1:
        return (f"error: doc_id {name!r} exists in both corpus/ and mine/, so it is ambiguous. "
                "Rename the copy in mine/ and rebuild the table.")
    text = matches[0].read_text(errors="replace")
    if len(text) <= LIMIT:
        return text
    return text[:LIMIT] + f"\n[truncated: this is the first {LIMIT} of {len(text)} characters]"


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("-")]
    print(read_document(ids[0] if ids else "doc_001")[:400])
