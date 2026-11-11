"""Stop 6 recipe 2: an analysis's report and figures become one web page.

    python results/analysis.py > results/analysis-output.txt
    python 06_build/page/make_page.py --title "Palmer penguins"
        reads results/report.md and results/figures/, checks the report's numbers
        against results/analysis-output.txt, writes results/page/index.html

    Another analysis (the transfer test's unseen input, a shipped one):
    python 02_data/datasets/stillwater-weather/reference/analysis.py > results/weather-output.txt
    python 06_build/page/make_page.py --from 02_data/datasets/stillwater-weather/reference \\
        --output results/weather-output.txt --out results/page-weather --title "Stillwater weather"

    The bad input (a report naming a missing figure and a number typed by hand):
    python 06_build/page/make_page.py --from 06_build/page/bad --out results/page-bad

Options: --from FOLDER (holds report.md and figures/; default results), --output FILE
(what the analysis printed; default FOLDER/analysis-output.txt), --out FOLDER (where
index.html goes; default results/page), --title TEXT.

The page is one file, figures inside it, nothing loaded from anywhere else, so it
opens on any computer and can be emailed. It stays private in results/. To look
at it: right-click results/page/index.html in the Explorer, choose Download, and
open it on your laptop. To put it on your public site, only when the data may be
public (the shipped datasets may; your own data may not be):
    mkdir -p site/data && cp results/page/index.html site/data/index.html

Before it writes anything it checks that every figure the report names exists,
and that every number with three or more significant digits in the report was
printed by the analysis (rounding allowed), when the analysis output file exists. The footer of
the page says which checks ran.
"""
import argparse
import base64
import html
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RES = ROOT / "results"
IMAGE = (".png", ".jpg", ".jpeg", ".svg")
# A number: digits with optional thousands commas and decimals, and an optional
# exponent, so 1.200e+03 is one number, not two. A decimal written without its
# leading zero (.123) counts too.
NUMBER = r"(?<![\w.])(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?(?![\w])"


def markdown_to_html(md):
    """Enough Markdown for a report: headings, paragraphs, bullet lists, bold, code, tables."""
    out, in_list, table = [], False, []

    def inline(t):
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", t)

    def flush_table():
        if table:
            rows = [r for r in table if not re.match(r"^\|?\s*:?-{3,}", r)]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
            out.append(f"<table><tr>{head}</tr>{body}</table>")
            table.clear()

    for line in md.splitlines():
        if line.strip().startswith("|"):
            table.append(line); continue
        flush_table()
        if re.match(r"^\s*[-*] ", line):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(line.strip()[2:])}</li>"); continue
        if in_list:
            out.append("</ul>"); in_list = False
        m = re.match(r"^(#{1,4}) (.*)", line)
        if m:
            n = len(m.group(1)); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif re.match(r"^!\[.*\]\(.*\)", line.strip()):
            continue                     # figures are placed below, from the folder
        elif line.strip():
            out.append(f"<p>{inline(line)}</p>")
    flush_table()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _value_and_tolerance(raw):
    """(value, tolerance) for a number as written: 0.6 of a unit in its last digit,
    so a value printed with more digits and rounded once more still matches."""
    text = raw.replace(",", "")
    mantissa, _, exponent = text.lower().partition("e")
    places = len(mantissa.split(".")[1]) if "." in mantissa else 0
    shift = int(exponent) if exponent else 0
    return float(text), 0.6 * 10 ** (shift - places)


def numbers_not_printed(report, output):
    """Numbers in the report (three or more significant digits written) that no
    number in the script's output rounds to. 0.179 in the report matches 0.1794
    printed by the script, and 1.2e+03 matches 1200; a number typed in by hand
    matches nothing."""
    printed = [float(x.rstrip(",").replace(",", "")) for x in re.findall(NUMBER, output) if x.rstrip(",")]
    missing = []
    for raw in sorted({x.rstrip(",") for x in re.findall(NUMBER, report)}):
        mantissa = raw.replace(",", "").lower().split("e")[0]
        if len(mantissa.replace(".", "").lstrip("0")) < 3:     # significant digits: 0.01 has one
            continue
        value, tol = _value_and_tolerance(raw)
        if not any(abs(x - value) <= tol for x in printed):
            missing.append(raw)
    return missing


def figures_named(report):
    """Every local image the report names: Markdown image destinations, with or
    without <angle brackets>, spaces or subfolders, and figures/... paths in text."""
    named = []
    for m in re.finditer(r"!\[[^\]]*\]\(\s*(<[^>]+>|[^)\"]+?)\s*(?:\"[^\"]*\")?\s*\)", report):
        named.append(m.group(1).strip("<>").strip())
    named += re.findall(r"(?<![\w/])figures/[\w./\- ]*?\.(?:png|jpe?g|svg)\b", report, re.I)
    out = []
    for n in named:
        n = urllib.parse.unquote(n)
        if re.match(r"^[a-z]+:", n, re.I) or n.startswith("data:"):
            continue                     # a web address, not a file here
        if n not in out:
            out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser(description="An analysis's report and figures become one web page.")
    ap.add_argument("--title", default="Dataset", help="the page's title")
    ap.add_argument("--from", dest="src", default=str(RES), help="folder with report.md and figures/ (default results)")
    ap.add_argument("--output", default=None, help="what the analysis printed (default FOLDER/analysis-output.txt)")
    ap.add_argument("--out", default=str(RES / "page"), help="where index.html goes (default results/page)")
    opts = ap.parse_args()
    src = Path(opts.src) if Path(opts.src).is_absolute() else Path.cwd() / opts.src
    out_dir = Path(opts.out) if Path(opts.out).is_absolute() else Path.cwd() / opts.out
    output_file = Path(opts.output) if opts.output else src / "analysis-output.txt"
    if not output_file.is_absolute():
        output_file = Path.cwd() / output_file

    report_path = src / "report.md"
    if not report_path.exists():
        raise SystemExit(f"No report.md in {src}: run Stop 2 first, or use the finished penguins analysis: "
                         "cp 06_build/page/from_reference.py results/analysis.py, then "
                         "python results/analysis.py > results/analysis-output.txt")
    report = report_path.read_text()
    problems = [f"the report names {n}, which does not exist" for n in figures_named(report)
                if not (src / n).exists()]
    checks = ["every figure the report names exists"]
    if output_file.exists():
        stray = numbers_not_printed(report, output_file.read_text())
        problems += [f"{n} is in the report but not in the analysis output ({output_file.name})" for n in stray[:10]]
        checks.append(f"every number with three or more significant digits in the report appears in the analysis output ({output_file.name})")
    else:
        print(f"Note: no {output_file.name}, so the numbers were not checked against the script.")
        checks.append("the numbers were NOT checked against any script output")
    if problems:
        print("NOT WRITTEN. Fix these first (or ask the agent to):")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    figdir = src / "figures"
    figures = sorted(p for p in figdir.rglob("*") if p.suffix.lower() in IMAGE) if figdir.exists() else []
    imgs = []
    for p in figures:
        kind = "svg+xml" if p.suffix.lower() == ".svg" else ("jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "png")
        data = base64.b64encode(p.read_bytes()).decode()
        imgs.append(f'<figure><img alt="{html.escape(p.stem)}" src="data:image/{kind};base64,{data}"><figcaption>{html.escape(p.stem)}</figcaption></figure>')
    footer = ("Built by make_page.py from report.md and " + f"{len(figures)} figure(s). Checked before writing: "
              + "; ".join(checks) + ". Nothing here says the analysis itself is right.")
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(opts.title)}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:52em;margin:2em auto;padding:0 1em;color:#222}}
img{{max-width:100%}}figure{{margin:1.5em 0}}figcaption{{color:#555;font-size:.9em}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:4px 8px}}
code{{background:#f3f3f3;padding:0 3px}}footer{{margin-top:3em;color:#666;font-size:.85em}}</style>
<h1>{html.escape(opts.title)}</h1>
{markdown_to_html(report)}
{''.join(imgs)}
<footer>{html.escape(footer)}</footer></html>"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page)
    shown = out_dir.relative_to(ROOT) if ROOT in out_dir.parents else out_dir
    print(f"Wrote {shown}/index.html ({len(figures)} figures, {len(page) // 1024} KB). "
          "It is private: right-click it in the Explorer, Download, and open it on your laptop.")


if __name__ == "__main__":
    main()
