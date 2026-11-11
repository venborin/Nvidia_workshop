"""Module 3: put table rows next to their sources so you can audit them.

    python 03_table/audit.py 3 7 12      rows 3, 7 and 12 of 03_table/records.jsonl
    python 03_table/audit.py 5           any other row
    python 03_table/audit.py --mark 3    print row 3, then mark it checked by a person

For each row this prints the record field by field, excerpt last, says
whether the excerpt appears word for word in the source file, and names the
file to open. The judging is yours: is each value right, wrong, guessed where
the document is silent, or backed by an excerpt that does not support it?
With --mark, each row's source file is added to 03_table/checked.txt (once),
with a fingerprint of its claim and excerpt, and viewer.py shows that row as
checked by a person until a rerun changes what it says.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "03_table" / "records.jsonl"
CHECKED = ROOT / "03_table" / "checked.txt"


def excerpt_found(excerpt, text):
    """The same check as starter.py: word for word, spacing ignored."""
    excerpt, text = " ".join(excerpt.split()), " ".join(text.split())
    return bool(excerpt) and excerpt in text


def find_source(name):
    """The file a row came from. New rows hold a path such as corpus/doc_003.txt
    or mine/notes.txt; older rows (the saved table) hold only the file name."""
    if not name:
        return None
    path = Path(name) if Path(name).is_absolute() else ROOT / name
    if path.is_file():
        return path
    if "/" not in name:
        for d in ("corpus", "mine"):
            if (ROOT / d / name).is_file():
                return ROOT / d / name
    return None


def check_key(row):
    """What checked.txt records for a row: its source file, so a sample doc_001
    and your own mine/doc_001.txt stay apart (a bare name in the saved table,
    doc_001.txt, is a corpus/ file; no source falls back to doc_id), then a short
    fingerprint of the row's main_claim and excerpt, so a rerun that changes
    what you checked clears the mark."""
    source = str(row.get("source", "")).strip()
    where = (source if "/" in source else "corpus/" + source) if source else str(row.get("doc_id", "")).strip()
    if not where:
        return ""
    claim = f'{row.get("main_claim", "")}\n{row.get("excerpt", "")}'
    return f"{where} {hashlib.sha1(claim.encode()).hexdigest()[:8]}"


def mark(row, n):
    """Add the row's source file to checked.txt unless it is there already, and say so."""
    key = check_key(row)
    if not key:
        print(f"Row {n} has no source or doc_id, so it was not marked.\n")
        return
    where = key.split(" ")[0]
    old = CHECKED.read_text(errors="replace") if CHECKED.exists() else ""
    if key in {line.strip() for line in old.splitlines()}:
        print(f"{where} was already marked as checked by a person in {CHECKED.relative_to(ROOT)}.\n")
        return
    with open(CHECKED, "a") as f:
        f.write(("\n" if old and not old.endswith("\n") else "") + key + "\n")
    print(f"Marked {where} as checked by a person in {CHECKED.relative_to(ROOT)}.\n")


if not TABLE.exists():
    raise SystemExit("No table yet. Run:  python 03_table/run_folder.py   (or --saved to copy the saved run)")

rows = [json.loads(line) for line in open(TABLE) if line.strip()]
wanted = [int(a) for a in sys.argv[1:] if a.isdigit()] or [3, 7, 12]
marking = "--mark" in sys.argv[1:]
if marking and not any(a.isdigit() for a in sys.argv[1:]):
    raise SystemExit("Name the rows to mark, for example:  python 03_table/audit.py --mark 3")

for n in wanted:
    print(f"==== row {n} of {len(rows)}")
    if not 1 <= n <= len(rows):
        print("no such row\n")
        continue
    row = rows[n - 1]
    fields = [k for k in row if k != "excerpt"] + (["excerpt"] if "excerpt" in row else [])
    width = max(len(k) for k in fields)
    for k in fields:
        print(f"{k:<{width}}  {row[k]}")
    source = find_source(row.get("source", ""))
    if source is None:
        print(f"\nSource file {row.get('source')!r} not found.\n")
        if marking:
            mark(row, n)
        continue
    if "excerpt" in row:
        found = excerpt_found(row["excerpt"], source.read_text(errors="replace"))
        print("\nIs the excerpt really in the document?", "yes" if found else "NO, check it")
    shown = source.relative_to(ROOT) if source.is_relative_to(ROOT) else source
    print(f"Open {shown} and check each value against it.\n")
    if marking:
        mark(row, n)
