"""Stop 6 recipe 1: a folder of documents you read every week becomes a table.

    python 06_build/table/build_table.py corpus/papers
    python 06_build/table/build_table.py mine 06_build/table/fields.json
    python 06_build/table/build_table.py 06_build/table/bad --out results/build-bad
        the bad input, written beside your good table instead of over it

The columns are yours: edit fields.json, one line per column, the sentence the
model reads to fill it. Every value comes back with a sentence quoted from the
document and the page it is on, and the program checks that the quote is really
there, the same check Stop 3 ran on every value. PDFs, .txt and .md files are read; anything else
is listed and skipped.

Writes results/build/table.csv (click it in the Explorer; the CSV viewer colours
the columns) and results/build/table.jsonl, or into the folder --out names. For
each column the CSV has the value, the quote it rests on, the page where the
program found that quote, and a check:
    yes          the quote is in the document word for word (on that page)
    NO           a quote was given but is not in the document
    not stated   the document does not say, and the model said so
    UNSUPPORTED  the model gave a value but no quote to back it: treat it as unchecked
Found means the sentence is there, not that it supports the value: read one row.
A document longer than 120,000 characters is read only from its start: the read
column says so, and its check says "not stated in the part read".
A document that fails is a row with an error, never dropped.
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "03_lit"))
from pydantic import BaseModel, Field, create_model   # noqa: E402

import llm                                            # noqa: E402
from pdfask import find_quote, pdf_pages, paper_text   # noqa: E402

OUT = ROOT / "results" / "build"


class Evidence(BaseModel):
    value: str = Field(description="The answer, in the document's own terms, or 'not stated'.")
    quote: str = Field(description="One sentence copied word for word from the document that supports the value, or ''.")
    page: int = Field(description="The page number from the === page N === markers, or 0.")


def row_model(fields):
    """A record with one Evidence per column, each described by your sentence."""
    return create_model("Row", **{name: (Evidence, Field(description=text)) for name, text in fields.items()})


def pages_of(path):
    """The document as a list of pages. A text file is one page."""
    if path.suffix.lower() == ".pdf":
        return pdf_pages(path)
    return [path.read_text(errors="replace")]


NOT_STATED = {"", "not stated", "not stated.", "none", "n/a", "na", "unknown"}


def check(value, quote, pages):
    """(status, page) for one value: see the module comment for the four statuses."""
    if not quote.strip():
        return ("not stated" if value.strip().lower() in NOT_STATED else "UNSUPPORTED"), ""
    hit = find_quote(quote, pages)
    if hit > 0:
        return "yes", hit
    if hit == -1:
        return "yes", "across a page break"
    return "NO", ""


def main():
    import argparse
    ap = argparse.ArgumentParser(description="A folder of documents becomes a table with your columns.")
    ap.add_argument("folder", help="the folder of PDFs, .txt or .md files")
    ap.add_argument("fields", nargs="?", default=str(HERE / "fields.json"), help="your columns (default 06_build/table/fields.json)")
    ap.add_argument("--out", default=str(OUT), help="where table.csv and table.jsonl go (default results/build)")
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    opts = ap.parse_args()
    out = Path(opts.out) if Path(opts.out).is_absolute() else Path.cwd() / opts.out
    folder = Path(opts.folder)
    folder = folder if folder.is_absolute() else Path.cwd() / folder
    fields_file = Path(opts.fields)
    fields = {k: v for k, v in json.loads(fields_file.read_text()).items() if not k.startswith("_")}
    Row = row_model(fields)
    rules = ("You fill one row of a table for one document. Its text has === page N === markers. "
             "For each column give the value, one sentence copied word for word that supports it, and its page. "
             "If the document does not say, write 'not stated', an empty quote and page 0. Never guess.")
    files = sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")
                   and not (p.suffix.lower() == ".md" and p.stem.isupper()))   # README.md, SOURCES.md: a folder's notes, not data
    usable = [p for p in files if p.suffix.lower() in (".pdf", ".txt", ".md")]
    for p in files:
        if p not in usable:
            print(f"skipped {p.name}: not a PDF, .txt or .md")
    if not usable:
        raise SystemExit(f"No PDF, .txt or .md files in {folder}.")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in usable:
        print(f"{path.name} ...", flush=True)
        row = {"file": path.name}
        try:
            pages = pages_of(path)
            if sum(len(p.strip()) for p in pages) < 200:
                raise ValueError("almost no text (a scan, or empty)")
            text, cut = paper_text(pages)
            rec = llm.ask_json(f"Document: {path.name}\n{text}", Row, system=rules)
            for name in fields:
                ev = getattr(rec, name)
                status, page = check(ev.value, ev.quote, pages)
                row[name] = ev.value
                row[f"{name}_quote"] = ev.quote
                row[f"{name}_page"] = page
                row[f"{name}_found"] = status
            row["cut"] = cut
            if cut:                          # the model saw only the start of a long document
                row["read"] = f"first {len(text):,} characters only"
                print(f"   long document: only the first {len(text):,} characters were read; "
                      "'not stated' here means not in that part")
                for name in fields:
                    if row[f"{name}_found"] == "not stated":
                        row[f"{name}_found"] = "not stated in the part read"
            else:
                row["read"] = "all"
        except Exception as err:
            row["error"] = f"{type(err).__name__}: {str(err).splitlines()[0][:150] if str(err) else ''}"
            print(f"   {row['error']}")
        rows.append(row)
    with open(out / "table.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    columns = ["file"] + [c for n in fields for c in (n, f"{n}_quote", f"{n}_page", f"{n}_found")] + ["read", "error"]
    with open(out / "table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    found = sum(r.get(f"{n}_found") == "yes" for r in rows for n in fields)
    asked = sum(r.get(f"{n}_found") in ("yes", "NO") for r in rows for n in fields)
    unsupported = sum(r.get(f"{n}_found") == "UNSUPPORTED" for r in rows for n in fields)
    shown = out.relative_to(ROOT) if ROOT in out.parents else out
    print(f"\n{len(rows)} rows -> {shown}/table.csv; {found} of {asked} quotes found word for word"
          + (f"; {unsupported} value(s) with no quote at all, marked UNSUPPORTED." if unsupported else "."))
    long_ones = [r["file"] for r in rows if r.get("cut")]
    if long_ones:
        print(f"Read only in part (too long): {', '.join(long_ones)}. See the read column.")
    print(f"{llm.TOTAL['calls']} model calls" + (f", about ${llm.TOTAL['cost']:.4f}" if llm.TOTAL["cost"] else ""))


if __name__ == "__main__":
    main()
