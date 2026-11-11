"""Module 3: the table as a web page, each row beside its source document.

    python 03_table/viewer.py                  03_table/records.jsonl -> two pages
    python 03_table/viewer.py other.jsonl      another table
    python 03_table/viewer.py --public-mine    also put rows from mine/ on the public page
                                               (values and excerpt only, never the document)

It writes two pages, each one file with nothing loaded from anywhere else:

  03_table/evidence.html     every row, and each document's text. Private: it
                             stays in your Codespace and is never committed.
  site/evidence/index.html   rows from corpus/ only, unless --public-mine. PUBLIC:
                             site/ is your website, so this page is live at once
                             and on GitHub Pages within about a minute.

On the page, click a column header to sort, type in the box to filter, and
click a row to read its document with the excerpt highlighted. The excerpt
backs main_claim and nothing else; every other value is the model's reading of
the document, to check by hand. Mark a row as checked by a person with
    python 03_table/audit.py --mark 3
"""
import html
import hashlib
import json
import os
import posixpath
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "03_table" / "records.jsonl"
CHECKED = ROOT / "03_table" / "checked.txt"
PRIVATE = ROOT / "03_table" / "evidence.html"
SITE = ROOT / "site"
PUBLIC = SITE / "evidence" / "index.html"
LIVE_URL = Path.home() / ".osu-llm-workshop-site-url"
PAGES_URL = Path.home() / ".osu-llm-workshop-pages-url"
NO_AUTOPUBLISH = Path.home() / ".osu-llm-workshop-no-autopublish"


# The two functions below are copied from audit.py, because importing audit.py
# would run it. They must stay exactly the same as there, so the page and
# audit.py always give the same answer for the same row.

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


def esc(value):
    return html.escape(value, quote=True)


def as_text(value):
    """A value as one string: text as it is, anything else as JSON."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def is_not_stated(text):
    return text.strip().strip(".").lower() == "not stated"


def folder_of(source, path):
    """'corpus', 'mine' or 'other': the folder the row's document is in. Decided
    from the real file when there is one, so a saved row's bare file name
    (doc_001.txt) counts as corpus/ and a link out of corpus/ does not."""
    if path is not None:
        real = path.resolve()
        for d in ("corpus", "mine"):
            if real.is_relative_to((ROOT / d).resolve()):
                return d
        return "other"
    name = posixpath.normpath(source) if source else ""
    for d in ("corpus", "mine"):
        if name.startswith(d + "/"):
            return d
    return "other"


def read_rows(table):
    rows = []
    with open(table, encoding="utf-8", errors="replace") as f:
        for number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                raise SystemExit(f"Line {number} of {table} is not a JSON record. Run the folder script again.")
            rows.append(row if isinstance(row, dict) else {"error": "this line is not a record"})
    return rows


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


def read_checked():
    try:
        return {line.strip() for line in CHECKED.read_text(errors="replace").splitlines() if line.strip()}
    except OSError:
        return set()


def describe(rows, checked):
    """Everything the pages show about each row, worked out once."""
    out = []
    for n, row in enumerate(rows, 1):
        source = as_text(row.get("source", ""))
        path = find_source(source)
        text = None
        if path is not None:
            try:
                text = path.read_text(errors="replace")
            except OSError:
                path = None
        if "excerpt" not in row:
            found = "n/a"
        elif text is None:
            found = "unknown"
        else:
            found = "yes" if excerpt_found(as_text(row["excerpt"]), text) else "no"
        out.append({
            "n": n,
            "row": row,
            "source": source,
            "folder": folder_of(source, path),
            "text": text,
            "found": found,
            "checked": "yes" if check_key(row) in checked else "no",
            "error": "error" in row,
        })
    return out


def columns_of(rows):
    """Every field any row has, in the order first seen, excerpt last (as audit.py prints)."""
    cols = []
    for row in rows:
        for k in row:
            if k not in cols:
                cols.append(k)
    if "excerpt" in cols:
        cols.remove("excerpt")
        cols.append("excerpt")
    return cols


def highlighted(text, excerpt):
    """The document with whitespace normalized, as excerpt_found compares it,
    and the excerpt marked where it was found. Escaped before marking."""
    norm = " ".join(text.split())
    ex = " ".join(excerpt.split())
    i = norm.find(ex) if ex else -1
    if i < 0:
        return esc(norm)
    return esc(norm[:i]) + "<mark>" + esc(norm[i:i + len(ex)]) + "</mark>" + esc(norm[i + len(ex):])


FOUND_WORDS = {
    "yes": "yes",
    "no": "no",
    "n/a": "no excerpt",
    "unknown": "source file not found",
}


def label(kind, value):
    return f'<span class="tag {kind}-{esc(value.replace("/", ""))}">{esc(FOUND_WORDS.get(value, value) if kind == "found" else value)}</span>'


def detail(item, public):
    row, n = item["row"], item["n"]
    parts = [f'<p class="where">Row {n}: {esc(as_text(row.get("doc_id", "")))}, from {esc(item["source"] or "no source given")}</p>']
    parts.append(
        f'<p>Excerpt found in source: {label("found", item["found"])} '
        f'Checked by a person: {label("checked", item["checked"])}</p>')
    if item["error"]:
        parts.append(f'<p class="errline">This row is an error: {esc(as_text(row["error"]))}</p>')
    if not public and item["checked"] == "no" and row.get("doc_id"):
        parts.append(f'<p class="hint">When you have checked this row against the document: '
                     f'<code>python 03_table/audit.py --mark {n}</code></p>')
    show_text = item["text"] is not None and (not public or item["folder"] == "corpus")
    if show_text:
        excerpt = as_text(row.get("excerpt", "")) if item["found"] == "yes" else ""
        note = ("The excerpt is highlighted. " if excerpt else
                "The excerpt was not found word for word, so nothing is highlighted. ")
        parts.append(f'<p class="hint">{note}Line breaks are shown as spaces, the way the check compares them.</p>')
        parts.append(f'<div class="doc">{highlighted(item["text"], excerpt)}</div>')
    elif item["text"] is not None:
        parts.append('<p class="hint">The document text is not on the public page, because this '
                     'document is from mine/. Its values and excerpt are shown above.</p>')
    else:
        parts.append(f'<p class="hint">Source file {esc(repr(item["source"]))} not found, '
                     'so there is no document to show.</p>')
    return "\n".join(parts)


def cell(row, key):
    if key not in row:
        return '<td class="empty"></td>'
    text = as_text(row[key])
    if key == "error":
        return f'<td class="errcell">{esc(text)}</td>'
    if is_not_stated(text):
        return f'<td><span class="ns">{esc(text)}</span></td>'
    return f"<td>{esc(text)}</td>"


def page(items, public, public_mine, table_name):
    cols = columns_of([it["row"] for it in items])
    long_cols = {k for k in cols if any(len(as_text(it["row"].get(k, ""))) > 60 for it in items)}
    heads = ["#", "excerpt found in source", "checked by a person"] + cols
    th = "".join(
        f'<th scope="col"{" class=long" if h in long_cols else ""}>'
        f'<button type="button" data-col="{i}">{esc(h)}<span class="arrow"></span></button></th>'
        for i, h in enumerate(heads))
    bodies = []
    for it in items:
        row = it["row"]
        cls = ' class="err"' if it["error"] else ""
        mark = '<span class="badge">error</span> ' if it["error"] else ""
        cells = (f'<td class="num">{mark}{it["n"]}</td>'
                 f'<td>{label("found", it["found"])}</td>'
                 f'<td>{label("checked", it["checked"])}</td>'
                 + "".join(cell(row, k) for k in cols))
        bodies.append(
            f'<tbody{cls}>\n<tr class="data" tabindex="0" aria-expanded="false">{cells}</tr>\n'
            f'<tr class="detail" hidden><td colspan="{len(heads)}">{detail(it, public)}</td></tr>\n</tbody>')
    if public:
        which = "rows from the sample documents in corpus/"
        if public_mine:
            which += ", and rows from mine/ with their values and excerpt but never their document text"
        scope = f"Public copy: {which}. Anyone with the address can read it."
        title = "Evidence table"
    else:
        scope = "Private copy: every row, with each document's text. It stays in your Codespace."
        title = "Evidence table (private)"
    made = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_err = sum(1 for it in items if it["error"])
    counts = f"{len(items)} rows from {esc(table_name)}, made {made}."
    if n_err:
        counts += f" {n_err} of them are error rows."
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{
  color-scheme: light;
  --bg: #ffffff; --fg: #1a1a1a; --muted: #555555; --line: #c8c8c8;
  --head: #eef1f5; --zebra: #f7f8fa; --hover: #fff6d6; --focus: #1f5fbf;
  --yes: #1d6b2f; --yes-bg: #e3f3e6; --no: #9b1c1c; --no-bg: #fbe4e4;
  --na: #555555; --na-bg: #ececec; --mark: #ffe066;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 16px 20px 48px; background: var(--bg); color: var(--fg);
  font: 18px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
h1 {{ font-size: 1.6em; margin: 0 0 6px; }}
p {{ margin: 6px 0; max-width: 60em; }}
.scope {{ font-weight: 600; }}
.backs {{ border-left: 5px solid var(--focus); padding: 6px 12px; background: var(--head); }}
.tools {{ margin: 14px 0 10px; display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }}
.tools input {{ font: inherit; padding: 6px 10px; min-width: 18em; border: 2px solid var(--line); border-radius: 6px; }}
.tools input:focus {{ outline: none; border-color: var(--focus); }}
.wrap {{ overflow-x: auto; border: 1px solid var(--line); }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }}
th {{ background: var(--head); position: sticky; top: 0; z-index: 1; white-space: nowrap; }}
th.long {{ min-width: 18em; }}
th button {{ font: inherit; font-weight: 700; background: none; border: 0; padding: 0; cursor: pointer; color: inherit; }}
th button:focus-visible {{ outline: 3px solid var(--focus); }}
.arrow {{ display: inline-block; width: 1.1em; color: var(--focus); }}
td {{ max-width: 30em; }}
tbody:nth-of-type(even) tr.data {{ background: var(--zebra); }}
tr.data {{ cursor: pointer; }}
tr.data:hover, tr.data:focus {{ background: var(--hover); outline: none; }}
tr.data[aria-expanded="true"] {{ background: var(--hover); }}
tr.detail td {{ background: var(--bg); border-bottom: 3px solid var(--focus); padding: 10px 14px 16px; }}
td.num {{ white-space: nowrap; font-variant-numeric: tabular-nums; }}
td.empty {{ background: repeating-linear-gradient(45deg, transparent, transparent 6px, var(--na-bg) 6px, var(--na-bg) 12px); }}
.ns {{ font-style: italic; color: var(--na); background: var(--na-bg); border: 1px dashed var(--na); border-radius: 4px; padding: 0 5px; }}
.tag {{ display: inline-block; font-weight: 700; border-radius: 4px; padding: 0 7px; white-space: nowrap; }}
.found-yes, .checked-yes {{ color: var(--yes); background: var(--yes-bg); }}
.found-no {{ color: var(--no); background: var(--no-bg); }}
.checked-no, .found-na, .found-unknown {{ color: var(--na); background: var(--na-bg); }}
tbody.err tr.data {{ background: var(--no-bg); }}
tbody.err tr.data td:first-child {{ border-left: 6px solid var(--no); }}
.badge {{ background: var(--no); color: #fff; font-weight: 700; border-radius: 4px; padding: 0 6px; font-size: 0.85em; text-transform: uppercase; }}
.errcell, .errline {{ color: var(--no); font-weight: 600; }}
.where {{ font-weight: 700; }}
.hint {{ color: var(--muted); }}
code {{ font-family: ui-monospace, Menlo, Consolas, monospace; background: var(--head); padding: 0 4px; border-radius: 3px; }}
.doc {{ max-width: 60em; padding: 10px 14px; border: 1px solid var(--line); border-radius: 6px; background: var(--zebra); white-space: normal; overflow-wrap: anywhere; }}
mark {{ background: var(--mark); color: inherit; padding: 1px 2px; border-radius: 2px; }}
@media (max-width: 600px) {{
  body {{ padding: 12px 16px 32px; font-size: 16px; }}
  .tools input {{ min-width: 0; width: 100%; }}
}}
</style>
</head>
<body>
<h1>{esc(title)}</h1>
<p class="scope">{esc(scope)}</p>
<p class="backs">Each row's excerpt is a sentence copied from its source document to back <code>main_claim</code>, and only <code>main_claim</code>. No other value has evidence attached: check those against the document yourself. "Excerpt found in source" is the program's check that the sentence is really there, word for word. Whether it supports the claim is a person's judgement: "checked by a person" says yes only for rows someone has marked.</p>
<p class="hint">{counts} Click a column header to sort. Click a row to open its document.</p>
<div class="tools">
<label for="filter">Filter rows:</label>
<input id="filter" type="search" placeholder="type any word or value" autocomplete="off">
<span id="shown" aria-live="polite"></span>
</div>
<div class="wrap">
<table id="t">
<thead><tr>{th}</tr></thead>
{chr(10).join(bodies)}
</table>
</div>
<script>
(function () {{
  var table = document.getElementById("t");
  var filter = document.getElementById("filter");
  var shown = document.getElementById("shown");
  var bodies = Array.prototype.slice.call(table.tBodies);
  var sortCol = -1, sortDir = 1;

  function toggle(tr) {{
    var detail = tr.nextElementSibling;
    var open = detail.hidden;
    detail.hidden = !open;
    tr.setAttribute("aria-expanded", open ? "true" : "false");
  }}
  bodies.forEach(function (tb) {{
    var tr = tb.rows[0];
    tr.addEventListener("click", function () {{ toggle(tr); }});
    tr.addEventListener("keydown", function (e) {{
      if (e.key === "Enter" || e.key === " ") {{ e.preventDefault(); toggle(tr); }}
    }});
  }});

  function key(tb, col) {{
    return (tb.rows[0].cells[col].textContent || "").trim().toLowerCase();
  }}
  function isNum(s) {{ return /^-?\\d+(\\.\\d+)?$/.test(s.replace(/^error\\s+/, "")); }}
  function num(s) {{ return parseFloat(s.replace(/^error\\s+/, "")); }}
  function compare(a, b) {{
    if (isNum(a) && isNum(b)) return num(a) - num(b);
    if (isNum(a)) return -1;
    if (isNum(b)) return 1;
    return a.localeCompare(b);
  }}
  var buttons = table.tHead.querySelectorAll("button");
  Array.prototype.forEach.call(buttons, function (btn) {{
    btn.addEventListener("click", function () {{
      var col = parseInt(btn.getAttribute("data-col"), 10);
      sortDir = (col === sortCol) ? -sortDir : 1;
      sortCol = col;
      bodies.sort(function (x, y) {{ return sortDir * compare(key(x, col), key(y, col)); }});
      bodies.forEach(function (tb) {{ table.appendChild(tb); }});
      Array.prototype.forEach.call(buttons, function (b) {{
        var on = parseInt(b.getAttribute("data-col"), 10) === col;
        b.querySelector(".arrow").textContent = on ? (sortDir > 0 ? " \\u25B2" : " \\u25BC") : "";
        b.parentNode.setAttribute("aria-sort", on ? (sortDir > 0 ? "ascending" : "descending") : "none");
      }});
    }});
  }});

  function applyFilter() {{
    var q = filter.value.trim().toLowerCase();
    var n = 0;
    bodies.forEach(function (tb) {{
      var hit = !q || tb.rows[0].textContent.toLowerCase().indexOf(q) >= 0;
      tb.hidden = !hit;
      if (hit) n++;
    }});
    shown.textContent = "Showing " + n + " of " + bodies.length + " rows";
  }}
  filter.addEventListener("input", applyFilter);
  applyFilter();
}})();
</script>
</body>
</html>
"""


def write(path, text):
    """Write the whole file at once, so the site never serves half a page."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def first_line(path):
    try:
        return path.read_text().strip().splitlines()[0].strip()
    except (OSError, IndexError):
        return ""


def shown(path):
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    unknown = [a for a in argv if a.startswith("-") and a != "--public-mine"]
    if unknown:
        raise SystemExit(f"Unknown option {unknown[0]}. Try:  python 03_table/viewer.py --help")
    public_mine = "--public-mine" in argv
    names = [a for a in argv if not a.startswith("-")]
    table = TABLE
    if names:
        table = Path(names[0])
        if not table.is_absolute() and not table.exists():
            table = ROOT / names[0]
    if not table.exists():
        raise SystemExit("No table yet. Run:  python 03_table/run_folder.py   (or --saved to copy the saved run)")
    if SITE.is_symlink():
        raise SystemExit("site/ is a symlink, so nothing was written there. It must be a real folder.")

    items = describe(read_rows(table), read_checked())
    allowed = ("corpus", "mine") if public_mine else ("corpus",)
    public_items = [it for it in items if it["folder"] in allowed]
    left_out = len(items) - len(public_items)

    write(PRIVATE, page(items, False, public_mine, table.name))
    write(PUBLIC, page(public_items, True, public_mine, table.name))

    print(f"Private page, all {len(items)} rows, with document text. It stays in your Codespace:")
    print(f"  {shown(PRIVATE)}")
    print("  To open it: right-click it in the Explorer, choose Download, and open the file.")
    print(f"Public page, {len(public_items)} of {len(items)} rows, on your website:")
    print(f"  {shown(PUBLIC)}")
    for word, f in (("Live now: ", LIVE_URL), ("Permanent:", PAGES_URL)):
        url = first_line(f)
        if url:
            print(f"  {word} {url.rstrip('/')}/evidence/")
    if left_out:
        mine_rows = sum(1 for it in items if it["folder"] == "mine")
        if mine_rows and not public_mine:
            print(f"  Left off the public page: {left_out} rows ({mine_rows} from mine/). "
                  "--public-mine adds the mine/ rows' values and excerpts, never their text.")
        else:
            print(f"  Left off the public page: {left_out} rows whose document is not in corpus/ or mine/.")
    print()
    index = SITE / "index.html"
    if NO_AUTOPUBLISH.exists():
        print("The public page is published: anyone with the live address can read it now.")
        print("Automatic publishing is off, so GitHub Pages gets it only when you run  bash publish-site.sh")
    elif not index.is_file() or "This site is empty for now" in index.read_text(errors="replace"):
        print("The public page is published: anyone with the live address can read it now.")
        print("It goes on GitHub Pages once site/ has a front page of its own (the website exercise).")
    else:
        print("The public page is published: anyone with the live address can read it now, "
              "and it goes on GitHub Pages within a minute.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
