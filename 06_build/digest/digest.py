"""Stop 6 recipe 3: what is new on your topic since you last looked.

    python 06_build/digest/digest.py                       the query saved below (start here)
    python 06_build/digest/digest.py "your query" --n 15   another query, more papers

    The two bad inputs, from saved answers, so they need no network and no model:
    python 06_build/digest/digest.py --records 06_build/digest/fixtures/no-match.json
    python 06_build/digest/digest.py --records 06_build/digest/fixtures/no-abstract.json

Each run asks OpenAlex for the 25 papers that best match the query, keeps
those from this year and last, drops the ones an earlier run has already shown
you (the list of seen papers is results/digest-seen.json), takes the newest N
of what is left, checks each DOI in Crossref, and writes a new file,
results/digest-<date>.md (a second run the same day writes digest-<date>-2.md,
so no digest is ever overwritten): title, authors, venue, the DOI's state, the
retraction line, and a two-sentence summary written by the model from the
abstract. A paper with no abstract gets no summary, never an invented one.

--records FILE reads a saved search answer instead of asking OpenAlex, writes
results/digest-test-<date>.md and leaves the seen list alone: for testing.

Change QUERY to your own and this is a program you run every Monday.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "03_lit"))
import lit                                 # noqa: E402

QUERY = "cover crops soil organic carbon"   # yours here
N = 10                                     # how many new papers to report at most
POOL = 25                                  # how many best matches to look through

RESULTS = ROOT / "results"
SEEN = RESULTS / "digest-seen.json"


def summary(record):
    """Two sentences from the abstract, or a plain note that there is none."""
    if not record.get("abstract"):
        return "No abstract in OpenAlex, so no summary. Read the paper."
    import llm                             # only needed when there is an abstract
    return llm.ask("In two sentences, say what this study did and what it found, using only the abstract. "
                   "Keep its numbers. Do not add anything the abstract does not say.\n\nAbstract:\n"
                   + record["abstract"][:6000])


def new_file(stem):
    """results/<stem>.md, or <stem>-2.md, -3.md ... if that exists: never overwrite."""
    out = RESULTS / f"{stem}.md"
    k = 2
    while out.exists():
        out = RESULTS / f"{stem}-{k}.md"
        k += 1
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(description="What is new on your topic since the last run.")
    ap.add_argument("query", nargs="?", default=QUERY, help="what to search for, in quotes")
    ap.add_argument("--n", type=int, default=N, help="how many new papers to report at most")
    ap.add_argument("--records", help="a saved search answer (JSON) to use instead of OpenAlex, for testing")
    opts = ap.parse_args()
    query, n = opts.query, opts.n
    RESULTS.mkdir(exist_ok=True)
    testing = bool(opts.records)
    seen = set() if testing else (set(json.loads(SEEN.read_text())) if SEEN.exists() else set())

    if testing:
        found = json.loads(Path(opts.records).read_text())
        query = found.get("query", query)
        found.setdefault("note", f"Saved answer from {opts.records}, not live.")
        found.setdefault("error", None)
        found.setdefault("date_utc", "saved")
    else:
        # Newest-first search ranks any paper that mentions the words anywhere, so
        # take the best matches and keep the recent ones instead.
        found = lit.search(query, n=POOL, sort="relevance")
    print(found["note"])
    if found["error"] and not found["records"]:
        raise SystemExit("No digest this time: the search did not answer. Nothing was changed.")
    records = [r for r in found["records"] if "error" not in r]
    if not records:
        raise SystemExit(f'Nothing matches "{query}". Check the spelling, or use fewer words. Nothing was changed.')
    this_year = date.today().year
    recent = [r for r in records if (r.get("year") or 0) >= this_year - 1]
    if not recent:
        raise SystemExit(f"None of the {len(records)} best matches is from {this_year - 1} or later. Nothing was changed.")
    # Drop what an earlier run showed before taking the newest n, so a paper
    # that did not fit last time is shown this time instead of never.
    unseen = [r for r in recent if (r.get("doi") or r.get("openalex_id")) not in seen]
    new = sorted(unseen, key=lambda r: r.get("year") or 0, reverse=True)[:n]
    print(f"{len(recent)} recent papers among the best matches for \"{query}\"; {len(unseen)} not shown before; "
          f"reporting {len(new)}.")

    lines = [f"# Digest: {query}", "",
             f"Run {found['date_utc']} UTC. {len(records)} best matches, {len(recent)} from the last two years, "
             f"{len(unseen)} not shown before, {len(new)} reported here. {found['note']}", ""]
    for r in new:
        authors = ", ".join(a["name"] for a in r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        if r.get("doi"):
            v = lit.verify(r["doi"], r["title"], r["authors"])
            state, retraction = v["state"], v["retraction"]["line"]
        else:
            state, retraction = "missing (no DOI)", "no DOI, so no retraction check"
        lines += [f"## {r['title']}", "",
                  f"{authors} ({r.get('year')}). {r.get('venue') or 'venue not stated'}. "
                  + (f"https://doi.org/{r['doi']}" if r.get("doi") else "no DOI"), "",
                  f"DOI check: {state}. Retraction: {retraction}.", "",
                  summary(r), ""]
        print(f"  {state:<12} {r['title'][:80]}")
        seen.add(r.get("doi") or r.get("openalex_id"))
    if not new:
        lines.append("Nothing new since the last run.")
    out = new_file(f"digest-test-{date.today().isoformat()}" if testing else f"digest-{date.today().isoformat()}")
    out.write_text("\n".join(lines) + "\n")
    if not testing:
        SEEN.write_text(json.dumps(sorted(s for s in seen if s), indent=1))
    print(f"\nWrote {out.relative_to(ROOT)}.")
    if not testing:
        print("To run it every Monday at 7 on a machine that stays on (a Thursday task), add to crontab -e:")
        print(f"  0 7 * * 1  cd {ROOT} && python3 06_build/digest/digest.py >> results/digest.log 2>&1")


if __name__ == "__main__":
    main()
