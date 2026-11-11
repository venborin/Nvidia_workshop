"""Stop 3: check every row of results/values.csv against its source. No model.

    python 03_lit/check_values.py                  checks results/values.csv
    python 03_lit/check_values.py other.csv        checks another file

One row is one reported value. Columns (a header row with these names, and
every row with exactly these eleven fields; put a field in double quotes when
it contains a comma):

    source      a PDF (corpus/papers/x.pdf, mine/x.pdf) or doi:<DOI> for a paper
                found by 03_lit/lit.py, whose abstract is then the text
    page        the page the quote is on, a whole number (from 03_lit/pages.py);
                0 for an abstract
    quote       one sentence copied word for word from that page
    value       the number or range as printed, e.g. 5.6, -14.86, 10-20, 1.2e-3
    unit        the unit as printed, e.g. Mg C ha-1
    conditions  what the value depends on: site, depth, years, comparison, method
    value_std   the value in the one standard unit you chose, with its sign;
                empty if it cannot be converted without inventing something
    unit_std    that standard unit
    conversion  how value_std was computed from the value v, as arithmetic,
                e.g. v / 8  or  v * 10 / 1.5  (anything after # is a comment)
    status      ok, or flagged when a row cannot be made to pass
    note        why a row is flagged, or anything a reader should know

For each row it checks, and says plainly which check failed:
  0. the row has all eleven fields, a whole-number page and a status of ok or flagged;
  1. the quote is in the source, on the page given (or running across that
     page's break); an abstract is page 0;
  2. every number in value appears in the quote (signs are compared by size only,
     since prose often says "a loss of 13.4" where the value is -13.4);
  3. a doi: source is verified in Crossref (title and first author match);
  4. when value_std is filled in, conversion applied to value, sign included,
     gives it (within 2%).
A row marked flagged with a reason in note is accepted even when a check fails;
the failure is still printed. A row that fails check 0 is never accepted: its
fields cannot be trusted to be where the header says. Deleting a row is never the fix.

Every run is appended to results/check-log.txt: the time, the file, the tally,
and one line per row with its verdict and reason, so the log shows how the rows
changed from one check to the next. The papers used through doi: rows are
written to results/sources.bib, each with its DOI check and retraction line, and
each one's abstract to results/papers/<doi>.txt, so it can be read like a PDF's
text. A file outside results/ (the saved run, say) is checked and printed only:
nothing in results/ is written. A table with no rows, or with columns other than
the eleven, is refused. Exit status 1 while any row fails unflagged.
"""
import csv
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from quotes import normal, pdf_pages, scanned   # noqa: E402

COLUMNS = ["source", "page", "quote", "value", "unit", "conditions",
           "value_std", "unit_std", "conversion", "status", "note"]
STATUSES = ("ok", "flagged")
# A number: optional sign, digits with an optional decimal part, optional exponent.
# A sign counts only when it does not follow a letter, digit or point, so "10-20"
# is a range of two numbers, "ha-1" is a unit, and "-14.86" or "(−0.32)" is one
# negative number. A decimal written without its zero (".5", "-.5", "0-.5") is
# read as the decimal it is, not as 5.
NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
                    r"|(?<![\w.])\.\d+(?:[eE][-+]?\d+)?"
                    r"|\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
LIVE = True          # False when checking a file outside results/: nothing in results/ is then written
_pdf_cache = {}
_doi_cache = {}
_doi_records = {}


def numbers(text):
    """The numbers in a piece of text, as floats with their signs:
    "1,250" -> [1250.0], "−0.32" -> [-0.32], "10–20" -> [10.0, 20.0],
    "1.2e-3" -> [0.0012], ".5" -> [0.5], "-.5" -> [-0.5]."""
    text = normal(text or "")
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)          # thousands separators
    out = []
    for token in NUMBER.findall(text):
        try:
            out.append(float(token))
        except ValueError:
            continue
    return out


def same(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def evaluate(conversion, v):
    """Apply a conversion such as "v / 8" or "v*10/1.5" to v. Only numbers, v,
    + - * / and brackets are allowed (no powers). Returns a finite float, or
    raises ValueError with a reason a person can act on."""
    expr = (conversion or "").split("#")[0].strip().replace("×", "*").replace("÷", "/").replace("−", "-")
    hint = ("If the value cannot be converted without inventing something, leave value_std and "
            "conversion empty: that is not a failure")
    if not expr:
        raise ValueError("no conversion given")
    if "**" in expr or not re.fullmatch(r"[\sv0-9.+\-*/()eE]+", expr) or "v" not in expr:
        raise ValueError(f"'{expr}' is not arithmetic in v (allowed: numbers, v, + - * / and brackets). {hint}")
    try:
        got = eval(expr, {"__builtins__": {}}, {"v": v})   # noqa: S307 (the check above admits arithmetic only)
        got = float(got)
    except ZeroDivisionError:
        raise ValueError("conversion divides by zero") from None
    except (SyntaxError, TypeError, NameError, OverflowError) as e:
        raise ValueError(f"'{expr}' cannot be worked out ({type(e).__name__}). {hint}") from None
    if not math.isfinite(got):
        raise ValueError(f"'{expr}' gives {got}, not a finite number")
    return got


def pdf_text(source):
    if source not in _pdf_cache:
        path = (ROOT / source) if not Path(source).is_absolute() else Path(source)
        _pdf_cache[source] = pdf_pages(path) if path.exists() else None
    return _pdf_cache[source]


def quote_on_page(quote, pages, page):
    """Where the quote is, judged from the cited page outward:
    ("here", page), ("break", page) when it runs across the cited page's break,
    ("elsewhere", n) when it is only on page n, or ("missing", 0)."""
    q = normal(quote)
    if len(q) < 12:
        return ("missing", 0)
    if 1 <= page <= len(pages) and q in normal(pages[page - 1]):
        return ("here", page)
    for n, text in enumerate(pages, 1):                         # whole on another page
        if q in normal(text):
            return ("elsewhere", n)
    for a, b in ((page - 1, page), (page, page + 1)):           # across the break before or after it
        if 1 <= a and b <= len(pages) and q in normal(pages[a - 1] + " " + pages[b - 1]):
            return ("break", page)
    for n in range(1, len(pages)):                              # across some other break
        if q in normal(pages[n - 1] + " " + pages[n]):
            return ("elsewhere", n)
    return ("missing", 0)


def _cached_search_record(doi):
    """An OpenAlex record for this DOI from a saved search answer, for when the
    network is down and the DOI itself was never looked up."""
    import lit
    want = lit.bare_doi(doi)
    for path in lit.cache_files():
        try:
            entry = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not str(entry.get("url", "")).startswith(lit.OPENALEX + "/works?"):
            continue
        for work in (entry.get("body") or {}).get("results") or []:
            if lit.bare_doi(work.get("doi")) == want:
                return lit._record(work)
    return None


def doi_record(doi):
    """(abstract, verification state, reason) for a DOI, via 03_lit/lit.py."""
    if doi not in _doi_cache:
        import lit
        found = lit.lookup(doi)
        rec = found.get("record") or (_cached_search_record(doi) if found.get("error") else None)
        if not rec:
            _doi_cache[doi] = (None, "missing", found.get("note") or "OpenAlex has no record of this DOI.")
        else:
            v = lit.verify(doi, rec.get("title"), rec.get("authors"))
            _doi_cache[doi] = (rec.get("abstract"), v["state"], v["reason"])
            _doi_records[doi] = dict(rec, verification=v)
            if rec.get("abstract") and LIVE:
                papers = ROOT / "results" / "papers"
                papers.mkdir(parents=True, exist_ok=True)
                (papers / f"{doi_slug(doi)}.txt").write_text(
                    f"{rec.get('title')} ({rec.get('year')}), doi:{doi}\n"
                    f"The abstract, as OpenAlex holds it: the text a doi: row's quote is checked against (page 0).\n\n"
                    f"{rec['abstract']}\n")
    return _doi_cache[doi]


def doi_slug(doi):
    return "doi_" + re.sub(r"[^A-Za-z0-9.]+", "_", doi).strip("_")


def structure(row):
    """Problems with the row's shape (check 0): these are never accepted by a flag."""
    problems = []
    extra = row.get(None)
    if extra:
        problems.append(f"the row has {len(COLUMNS) + len(extra)} fields, not {len(COLUMNS)}: "
                        "a comma in a field that is not inside double quotes")
    short = [c for c in COLUMNS if row.get(c) is None]
    if short:
        problems.append(f"the row has only {len(COLUMNS) - len(short)} of {len(COLUMNS)} fields "
                        f"(missing: {', '.join(short)}), so every field after the gap is in the wrong column")
    status = (row.get("status") or "").strip().lower()
    if not short and not extra and status not in STATUSES:
        problems.append(f"status '{row.get('status')}' must be ok or flagged")
    page = (row.get("page") or "").strip()
    if not re.fullmatch(r"\d+", page):
        problems.append(f"page '{page}' must be a whole number (0 for an abstract)")
    return problems


def check_row(row):
    """A list of problems with one row's evidence; empty when it passes."""
    problems = []
    source = (row.get("source") or "").strip()
    quote = (row.get("quote") or "").strip()
    value = (row.get("value") or "").strip()
    page_text = (row.get("page") or "").strip()
    page = int(page_text) if re.fullmatch(r"\d+", page_text) else None
    if not source:
        return ["no source"]
    if not quote:
        problems.append("no quote")

    # 1 and 3: the quote is in the source, where the row says.
    if source.lower().startswith("doi:"):
        abstract, state, reason = doi_record(source[4:].strip())
        if state != "verified":
            problems.append(f"DOI not verified ({state}): {reason}")
        if quote and abstract is None:
            problems.append("OpenAlex has no abstract for this DOI, so the quote cannot be checked; use the paper itself, or flag the row")
        elif quote and normal(quote) not in normal(abstract):
            problems.append("quote is not in the abstract word for word")
        if page not in (0, None):
            problems.append("an abstract has no pages: use page 0")
    else:
        pages = pdf_text(source)
        if pages is None:
            problems.append(f"no file {source}")
        elif scanned(pages):
            problems.append(f"{source} has almost no text (a scan); nothing in it can be checked")
        elif quote and page is not None:
            where, n = quote_on_page(quote, pages, page)
            if where == "missing":
                problems.append("quote not found in the paper word for word (copy it from 03_lit/pages.py output; for a table, copy the table's line as printed)")
            elif where == "elsewhere":
                problems.append(f"quote is on page {n}, not page {page}")

    # 2: the value comes from the quote (by size: prose often carries the sign in words).
    if not value:
        problems.append("no value")
    elif quote:
        have = [abs(x) for x in numbers(quote)]
        wanted = numbers(value)
        if not wanted:
            problems.append(f"value '{value}' has no number in it")
        else:
            missing = [f"{w:g}" for w in wanted if not any(same(abs(w), h) for h in have)]
            if missing:
                problems.append(f"{', '.join(missing)} from the value is not in the quote")

    # 4: the conversion reproduces value_std, sign included.
    std = (row.get("value_std") or "").strip()
    if std:
        ends, std_ends = numbers(value), numbers(std)
        if not (row.get("unit_std") or "").strip():
            problems.append("value_std is filled in but unit_std is empty")
        if len(ends) != len(std_ends):
            problems.append(f"value has {len(ends)} number(s) but value_std has {len(std_ends)}")
        else:
            try:
                for v, s in zip(ends, std_ends):
                    got = evaluate(row.get("conversion"), v)
                    if abs(got - s) > 0.02 * max(abs(s), 1e-9):
                        problems.append(f"conversion '{row.get('conversion')}' turns {v:g} into {got:.4g}, not {s:g}")
                        break
            except ValueError as e:
                problems.append(f"conversion: {e}")
    return problems


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = Path(argv[0]) if argv else ROOT / "results" / "values.csv"
    if not path.exists():
        print(f"No {path}. Write it first: one row per reported value, with these columns:\n  " + ",".join(COLUMNS))
        return 1
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = [{(k.strip() if isinstance(k, str) else k): v for k, v in r.items()} for r in reader]
    absent = [c for c in COLUMNS if c not in header]
    if absent:
        print(f"{path} is missing column(s): {', '.join(absent)}. The header must be:\n  " + ",".join(COLUMNS))
        return 1
    unknown = [h for h in header if h not in COLUMNS]
    twice = sorted({h for h in header if header.count(h) > 1})
    if unknown or twice:
        print(f"{path} has " + " and ".join(
            ([f"column(s) the table does not have: {', '.join(unknown)}"] if unknown else [])
            + ([f"column(s) named twice: {', '.join(twice)}"] if twice else []))
            + ". The header must be exactly:\n  " + ",".join(COLUMNS))
        return 1
    if not rows:
        print(f"{path} has a header and no rows: nothing was checked. Add one row per reported value.")
        return 1
    global LIVE
    try:
        path.resolve().relative_to((ROOT / "results").resolve())
    except ValueError:
        LIVE = False      # a saved or other file: check and print, but leave results/ as the live run left it

    counts = {"pass": 0, "flagged": 0, "fail": 0}
    lines, verdicts = [], []
    for n, row in enumerate(rows, 2):            # line 1 is the header
        shape = structure(row)
        problems = shape + check_row({k: v for k, v in row.items() if k is not None})
        flagged = (row.get("status") or "").strip().lower() == "flagged"
        src = (row.get("source") or "").strip()
        src = src if src.lower().startswith("doi:") else (Path(src).name or src)
        label = f"line {n:>3}  {src} p{(row.get('page') or '').strip() or '?'}: {(row.get('value') or '').strip()} {(row.get('unit') or '').strip()}"
        if not problems:
            counts["pass"] += 1
            lines.append(f"PASS     {label}")
            verdicts.append(f"  line {n} PASS")
        elif flagged and not shape and (row.get("note") or "").strip():
            counts["flagged"] += 1
            lines.append(f"FLAGGED  {label}\n           " + "; ".join(problems) + f"\n           accepted because: {row['note'].strip()}")
            verdicts.append(f"  line {n} FLAGGED: " + "; ".join(problems) + f" | note: {row['note'].strip()}")
        else:
            counts["fail"] += 1
            why = "; ".join(problems)
            if flagged and shape:
                why += "; a flag cannot accept a row whose fields are out of place"
            elif flagged:
                why += "; flagged but note is empty: say why"
            lines.append(f"FAIL     {label}\n           {why}")
            verdicts.append(f"  line {n} FAIL: {why}")
    summary = (f"{len(rows)} rows: {counts['pass']} pass, {counts['flagged']} flagged, {counts['fail']} fail. "
               + ("Fix each failing row, or set its status to flagged and say why in note. Do not delete rows to make this pass."
                  if counts["fail"] else "Every row passes or is flagged with a reason."))
    print("\n".join(lines))
    print(summary)
    bib = ROOT / "results" / "sources.bib"
    uses_doi = any((r.get("source") or "").strip().lower().startswith("doi:") for r in rows)
    if not LIVE:
        print("This file is not in results/, so results/sources.bib and results/check-log.txt were left as they are.")
        return 1 if counts["fail"] else 0
    if not uses_doi and bib.exists():
        bib.unlink()          # the table no longer uses a searched paper: an old list would describe other rows
        print("No doi: rows in this table, so the old results/sources.bib was removed.")
    if _doi_records:
        import lit
        bib.parent.mkdir(parents=True, exist_ok=True)
        bib.write_text("% The papers found by search that values.csv uses as sources (doi: rows),\n"
                       "% written by 03_lit/check_values.py from OpenAlex and Crossref records, not by a model.\n\n"
                       + lit.bibtex(list(_doi_records.values())))
        print(f"Wrote results/sources.bib: {len(_doi_records)} searched paper(s) used as sources, each DOI checked; "
              "their abstracts are in results/papers/doi_*.txt.")
    log = ROOT / "results" / "check-log.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        shown = path.resolve().relative_to(ROOT)
    except ValueError:
        shown = path
    with open(log, "a") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {shown}  {summary}\n" + "\n".join(verdicts) + "\n")
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
