"""Module 3: a folder of documents becomes a table.

    python 03_table/run_folder.py             corpus/  -> 03_table/records.jsonl
    python 03_table/run_folder.py mine        mine/    -> 03_table/records.jsonl
    python 03_table/run_folder.py --saved     copy the saved run instead (slow endpoint)

One record per document, one JSON line each, in the order of the files. A
document that fails twice is written with an error field, never dropped, so
the table always has one row per file. At the end it says how many excerpts
appear word for word in their documents and which rows to check first.
This is the script most people take home. The afternoon's tools search the table it writes.
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from docs import folder                   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "03_table" / "records.jsonl"
SAVED = ROOT / "corpus" / "records.jsonl"

if "--saved" in sys.argv:
    shutil.copy(SAVED, OUT)
    print(f"Copied the saved run to {OUT.relative_to(ROOT)} ({sum(1 for _ in open(OUT))} rows).")
    sys.exit(0)

from starter import make_record, excerpt_found, short_error, where   # noqa: E402

which = next((a for a in sys.argv[1:] if not a.startswith("-")), "corpus")
docs = folder(which)
base = Path(which) if Path(which).is_absolute() else ROOT / which
print(f"{len(docs)} documents in {which}/ -> {OUT.relative_to(ROOT)}\n")

t0 = time.time()
not_found = []
with open(OUT, "w") as out:
    for i, doc in enumerate(docs, 1):
        row = None
        for attempt in (1, 2):
            try:
                row = make_record(doc, base / doc["source"]).model_dump()
                break
            except Exception as err:
                last = err
                time.sleep(1)
        if row is None:
            row = {"doc_id": doc["doc_id"], "source": where(base / doc["source"]), "error": short_error(last)}
        out.write(json.dumps(row) + "\n")
        out.flush()
        if "error" in row or not excerpt_found(row.get("excerpt", ""), doc["text"]):
            not_found.append(f"row {i} ({doc['doc_id']})")
        claim = row.get("main_claim", row.get("error", ""))
        print(f"{i:>2}. {doc['doc_id']}  {claim[:80]}")

print(f"\nDone in {time.time() - t0:.0f} s. {len(docs) - len(not_found)} of {len(docs)} excerpts are word for word in their documents.")
if not_found:
    print("Check first (an error, or an excerpt not found word for word):", ", ".join(not_found))
picks = [n for n in (3, 7, 12) if n <= len(docs)] or list(range(1, min(len(docs), 3) + 1))
print(f"Next: python 03_table/audit.py {' '.join(map(str, picks))}   (rows of {OUT.relative_to(ROOT)} beside their sources)")
