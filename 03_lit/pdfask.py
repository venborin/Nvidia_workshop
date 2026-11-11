"""Stop 3: papers become an evidence table, every value with its page and a quote.

    python 03_lit/pdfask.py                     your PDFs in mine/, or the three shipped papers
    python 03_lit/pdfask.py mine/a.pdf mine/b.pdf   these papers

For each paper it pulls the text out of the PDF here, page by page, and keeps
that text in results/papers/. The model reads exactly that text and fills one
row: the question, the method, the sample and the finding, each with a sentence
copied from the paper and the page it is on. Then the program looks for every
copied sentence in the text the model saw, and says which it found and on which
page.

Found means the sentence is in the paper. It does not mean the sentence
supports the value beside it: that is what you check.

Writes results/table.jsonl (one row per paper) and results/evidence-table.html
(right-click it in the file tree and choose Download to open it on your laptop).
Both stay in your Codespace: results/ is never committed.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pydantic import BaseModel, Field   # noqa: E402

import llm                              # noqa: E402

RESULTS = ROOT / "results"
TEXTS = RESULTS / "papers"
SHIPPED = ROOT / "corpus" / "papers"
MAX_CHARS = 120_000      # about 30,000 tokens: a long paper's body; the rest is said to be cut


class Evidence(BaseModel):
    value: str = Field(description="The answer in one or two sentences, in the paper's own terms, or 'not stated'.")
    quote: str = Field(description="One sentence copied word for word from the paper that supports the value, or '' if not stated.")
    page: int = Field(description="The page number, from the === page N === markers, where the quote is. 0 if not stated.")


class PaperRow(BaseModel):
    title: str = Field(description="The paper's title, or 'not stated'.")
    year: str = Field(description="Four-digit publication year, or 'not stated'.")
    question: Evidence = Field(description="The research question or aim.")
    method: Evidence = Field(description="How the study was done: design, data, analysis.")
    sample: Evidence = Field(description="What was studied and how many: subjects, sites, specimens, runs, with units.")
    finding: Evidence = Field(description="The main result, with the numbers the paper gives.")


RULES = (
    "You fill in one row of an evidence table for one research paper. The paper's text is given "
    "with === page N === markers. For each field give the value, one sentence copied word for word "
    "from the paper that supports it, and the page number of that sentence. Copy the sentence exactly, "
    "including numbers and punctuation; do not join sentences or fix wording. If the paper does not "
    "state something, write 'not stated', an empty quote and page 0. Never guess."
)
FIELDS = ("question", "method", "sample", "finding")


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
                 "—": "-", "−": "-", " ": " ", "­": ""}.items():
        text = text.replace(a, b)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return " ".join(text.split())


def find_quote(quote, pages):
    """The page (counting from 1) where the quote appears word for word, or 0.
    Also tries the whole paper at once, for a sentence that runs across a page break."""
    q = normal(quote)
    if len(q) < 12:
        return 0
    for number, text in enumerate(pages, 1):
        if q in normal(text):
            return number
    return -1 if q in normal(" ".join(pages)) else 0


def paper_text(pages):
    """The text the model reads, with page markers, cut at MAX_CHARS."""
    text = "".join(f"\n=== page {n} ===\n{t}" for n, t in enumerate(pages, 1))
    return text[:MAX_CHARS], len(text) > MAX_CHARS


def row_for(path):
    """Read one PDF, ask for its row, check every quote. Returns a plain dict."""
    pages = pdf_pages(path)
    chars = sum(len(p.strip()) for p in pages)
    TEXTS.mkdir(parents=True, exist_ok=True)
    (TEXTS / f"{path.stem}.txt").write_text("".join(f"\n=== page {n} ===\n{t}" for n, t in enumerate(pages, 1)))
    if chars < 200 * max(1, len(pages)) / 4:
        return {"file": path.name, "pages": len(pages),
                "error": "almost no text: a scanned PDF. Use another paper, or one of corpus/papers/."}
    text, cut = paper_text(pages)
    record = llm.ask_json(f"Paper file: {path.name}\n{text}", PaperRow, system=RULES)
    row = {"file": path.name, "pages": len(pages), "cut": cut, "model": llm.LAST.get("model"),
           "title": record.title, "year": record.year}
    for field in FIELDS:
        ev = getattr(record, field)
        found = find_quote(ev.quote, pages) if ev.quote.strip() else 0
        row[field] = {"value": ev.value, "quote": ev.quote, "page_claimed": ev.page,
                      "found": "yes" if found else ("not stated" if not ev.quote.strip() else "NO"),
                      "page_found": found if found > 0 else None}
    return row


def write_html(rows, out):
    """One self-contained page: a row per paper, each field with its quote and whether it was found."""
    esc = html.escape
    cells = []
    for r in rows:
        if "error" in r:
            cells.append(f"<tr><td>{esc(r['file'])}</td><td colspan=4>{esc(r['error'])}</td></tr>")
            continue
        tds = []
        for f in FIELDS:
            e = r[f]
            mark = {"yes": "found", "NO": "NOT FOUND", "not stated": "not stated"}[e["found"]]
            page = f" p. {e['page_found']}" if e["page_found"] else ""
            tds.append(f"<td><p>{esc(e['value'])}</p><blockquote>{esc(e['quote'])}</blockquote>"
                       f"<p class='{e['found'].replace(' ', '-')}'>{mark}{page}</p></td>")
        cells.append(f"<tr><td><b>{esc(r['title'])}</b><br>{esc(r['year'])}<br><small>{esc(r['file'])}</small></td>{''.join(tds)}</tr>")
    out.write_text(f"""<!doctype html><meta charset=utf-8><title>Evidence table</title>
<style>body{{font:15px/1.45 system-ui,sans-serif;margin:24px}}table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:8px;vertical-align:top;max-width:28em}}blockquote{{margin:6px 0;padding-left:8px;border-left:3px solid #999;color:#333}}
.yes{{color:#176a2c}}.NO{{color:#b00020;font-weight:bold}}.not-stated{{color:#777}}</style>
<h1>Evidence table</h1><p>Found means the quoted sentence is in the paper's text, on that page. It does not mean the sentence supports the value: that is yours to check.</p>
<table><tr><th>Paper</th>{''.join(f'<th>{f}</th>' for f in FIELDS)}</tr>{''.join(cells)}</table>""")


def main():
    args = [Path(a) for a in sys.argv[1:]]
    if not args:
        args = sorted((ROOT / "mine").glob("*.pdf")) or sorted(SHIPPED.glob("*.pdf"))
    if not args:
        raise SystemExit("No PDFs: put some in mine/, or name them: python 03_lit/pdfask.py paper.pdf")
    RESULTS.mkdir(exist_ok=True)
    rows = []
    for path in args:
        path = path if path.is_absolute() else (Path.cwd() / path)
        print(f"Reading {path.name} ...", flush=True)
        try:
            row = row_for(path)
        except Exception as err:
            row = {"file": path.name, "error": f"{type(err).__name__}: {str(err).splitlines()[0][:160] if str(err) else ''}"}
        rows.append(row)
        if "error" in row:
            print(f"   {row['error']}")
            continue
        print(f"   {row['title'][:90]} ({row['year']}){'   [long paper: only the first part was read]' if row['cut'] else ''}")
        for f in FIELDS:
            e = row[f]
            verdict = {"yes": "quote found", "NO": "QUOTE NOT FOUND", "not stated": "not stated"}[e["found"]]
            where = f", page {e['page_found']}" if e["page_found"] else ""
            print(f"   {f:<9} ({verdict}{where})  {e['value'][:80]}")
    with open(RESULTS / "table.jsonl", "w") as out:
        for row in rows:
            out.write(json.dumps(row) + "\n")
    write_html(rows, RESULTS / "evidence-table.html")
    cost = f", about ${llm.TOTAL['cost']:.3f}" if llm.TOTAL["cost"] else ""
    print(f"\n{len(rows)} papers -> results/table.jsonl and results/evidence-table.html ({llm.TOTAL['calls']} model calls{cost})")
    print("The text the model read is in results/papers/. Check one quote that was found: does it support its value?")


if __name__ == "__main__":
    main()
