"""Smoke test for lit.py: the cases that go wrong on the day, checked before the day.

    python 03_lit/smoke_test.py            offline (cache only), then live if the network is up
    python 03_lit/smoke_test.py --offline  offline only

Offline mode replaces urllib's urlopen with one that always raises, so every
answer has to come from 03_lit/cache/. Live mode talks to OpenAlex and Crossref
and costs two OpenAlex searches ($0.002 of the daily budget). Prints PASS or FAIL
for each case and exits with 1 if any case fails.

The cases: three shipped papers verify; a DOI that does not exist; a known
retracted paper (Wakefield et al. 1998, The Lancet); a paper with no abstract;
a title mismatch and an author mismatch; a DataCite DOI; service failures
(network down with and without a saved answer, a timeout that is not
retried on every call, a 503 that is retried twice);
and BibTeX escaping and keys.
"""
import json
import socket
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lit                                            # noqa: E402

TOPIC = "cover crops soil organic carbon"            # a fallback topic with a saved answer
NO_SUCH_DOI = "10.5555/osu-workshop-no-such-doi-2026"
RETRACTED = ("10.1016/S0140-6736(97)11096-0",
             "Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive "
             "developmental disorder in children", "Wakefield")
NO_ABSTRACT = "10.1038/171737a0"                     # Watson and Crick 1953: OpenAlex has no abstract
DATACITE = "10.5281/zenodo.19505214"                 # a real Zenodo DOI, registered with DataCite
PAPERS = [("10.5194/soil-10-139-2024", "Cover crops improve soil structure and change organic "
           "carbon distribution in macroaggregate fractions", "Norman Gentsch"),
          ("10.1038/s41598-020-70224-6", "Cumulative impact of cover crops on soil carbon "
           "sequestration and profitability in a temperate humid climate", "Chahal, I."),
          ("10.1038/s41598-020-69407-y", "Cover crops and chicken grazing in a winter fallow field "
           "improve soil carbon and nitrogen contents and decrease methane emissions", ["Huabin Zheng"])]

results = []


def check(mode, name, ok, detail=""):
    """Record and print one case."""
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  [{mode}] {name}" + (f"\n        {detail}" if detail and not ok else ""))


def case(mode, name, test):
    """Run one case; an exception is a failure, not a crash of the whole test."""
    lit._DOWN.clear()                                 # each case starts with no host marked as down
    try:
        ok, detail = test()
    except Exception as err:
        ok, detail = False, f"raised {type(err).__name__}: {err}"
    check(mode, name, ok, detail)


def network_up():
    """True if Crossref answers a TCP connection within a few seconds."""
    try:
        socket.create_connection(("api.crossref.org", 443), timeout=5).close()
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- the cases, for both modes

def shipped_papers():
    states = [lit.verify(d, t, a) for d, t, a in PAPERS]
    ok = all(s["state"] == "verified" and s["retraction"]["retracted"] is False for s in states)
    return ok, [(s["doi"], s["state"], s["reason"]) for s in states]


def no_such_doi():
    v = lit.verify(NO_SUCH_DOI, "Anything", "Anyone")
    return v["state"] == "missing" and "invented" in v["reason"], (v["state"], v["reason"])


def no_doi_at_all():
    v = lit.verify(None, "A paper with no DOI", "Smith")
    return v["state"] == "missing", (v["state"], v["reason"])


def retracted():
    doi, title, author = RETRACTED
    v = lit.verify(doi, title, author)
    r = v["retraction"]
    ok = (v["state"] == "verified" and r["retracted"] is True and r["line"].startswith("RETRACTED")
          and "10.1016/s0140-6736(10)60175-4" in r["line"])
    return ok, (v["state"], r["line"])


def clean_line():
    v = lit.verify(*PAPERS[0])
    line = v["retraction"]["line"]
    return line.startswith("no retraction found in Crossref as of 20"), line


def no_abstract():
    found = lit.lookup(NO_ABSTRACT)
    record = found["record"]
    if record is None:
        return False, found["note"]
    record["verification"] = lit.verify(record["doi"], record["title"], record["authors"])
    bib = lit.bibtex([record])
    ok = (record["abstract"] is None and record["verification"]["state"] == "verified"
          and "@article{watson1953molecular," in bib)
    return ok, (record["abstract"], record["verification"]["state"], bib[:200])


def title_mismatch():
    v = lit.verify(NO_ABSTRACT, "Highly accurate protein structure prediction with AlphaFold", "Watson")
    ok = v["state"] == "mismatched" and "title differs" in v["reason"] and "author" not in v["reason"]
    return ok, (v["state"], v["reason"])


def author_mismatch():
    doi, title, _ = PAPERS[1]
    v = lit.verify(doi, title, ["Smith, J."])
    ok = v["state"] == "mismatched" and "first author differs" in v["reason"]
    return ok, (v["state"], v["reason"])


def nothing_to_compare():
    v = lit.verify(PAPERS[1][0])
    return v["state"] == "mismatched" and "no title was passed" in v["reason"], (v["state"], v["reason"])


def datacite():
    v = lit.verify(DATACITE, "Anything", "Anyone")
    return v["state"] == "missing" and "DataCite" in v["reason"], (v["state"], v["reason"])


def search_topic():
    s = lit.search(TOPIC)
    ok = (len(s["records"]) == 3 and s["query"] == TOPIC and s["sort_field"] == "relevance_score:desc"
          and s["url"].startswith("https://api.openalex.org/works?") and "mailto" not in s["url"])
    return ok, {k: s[k] for k in ("source", "note", "error", "url")}


def cli_writes_files():
    """The command line writes refs.bib and lit-search.json (into a temporary folder here)."""
    saved = lit.RESULTS
    with tempfile.TemporaryDirectory() as tmp:
        lit.RESULTS = Path(tmp)
        try:
            result = lit.run(TOPIC)
            bib = (Path(tmp) / "refs.bib").read_text()
            data = json.loads((Path(tmp) / "lit-search.json").read_text())
        finally:
            lit.RESULTS = saved
    ok = (bib.count("@article{") + bib.count("@misc{") == len(result["records"]) == 3
          and data["query"] == TOPIC and all("verification" in r for r in data["records"]))
    return ok, bib[:300]


def bibtex_doi_letters():
    doi = "10.1016/j.solener.2021.03.005"
    text = lit.bibtex([{"title": "Solar test", "year": 2021, "doi": doi, "type": "article",
                        "authors": [{"name": "A Smith", "family": "Smith"}], "venue": "Solar Energy"}])
    return ("doi = {" + doi + "}") in text, text.splitlines()[-2].strip()


def bibtex_rules():
    record = {"title": "The 50% rule & soil_C: {a} #1 test", "doi": "10.1/x_(y)", "year": 2021, "type": "article",
              "authors": [{"name": "José Ñúñez-García", "family": "Ñúñez-García"}], "venue": "J. Soil & Water"}
    bib = lit.bibtex([record, dict(record)])
    # "The" is skipped, so the key's title word is "50"; the repeat gets an "a".
    ok = ("@article{nunezgarcia202150," in bib and "@article{nunezgarcia202150a," in bib
          and "doi = {10.1/x_(y)}" in bib
          and r"{The 50\% rule \& soil\_C: \{a\} \#1 test}" in bib and r"J. Soil \& Water" in bib
          and bib == lit.bibtex([record, dict(record)]))
    return ok, bib


COMMON = [("three shipped papers verify, no retraction", shipped_papers),
          ("DOI that does not exist -> missing", no_such_doi),
          ("no DOI at all -> missing", no_doi_at_all),
          ("known retraction (Wakefield 1998) is flagged", retracted),
          ("clean record says 'no retraction found in Crossref as of <date>'", clean_line),
          ("paper with no abstract still verifies and gets BibTeX", no_abstract),
          ("title mismatch -> mismatched, says title", title_mismatch),
          ("author mismatch -> mismatched, says first author", author_mismatch),
          ("DOI alone, nothing to compare -> mismatched, says why", nothing_to_compare),
          ("DataCite DOI -> missing, names DataCite", datacite),
          ("search on a fallback topic returns 3 recorded results", search_topic),
          ("command line writes refs.bib and lit-search.json", cli_writes_files),
          ("BibTeX keys and escaping are deterministic", bibtex_rules),
          ("BibTeX keeps every letter of a DOI (regression: an s was once stripped)", bibtex_doi_letters)]


# ---------------------------------------------------------------- service failures (offline only)

def failing_urlopen(*args, **kwargs):
    raise urllib.error.URLError("simulated outage: the network is down")


def outage_uses_cache():
    v = lit.verify(*PAPERS[0])
    s = lit.search(TOPIC)
    ok = (v["state"] == "verified" and v["source"] == "cache" and "CACHED" in v["note"]
          and "(cached answer)" in v["retraction"]["line"]
          and s["source"] == "cache" and s["note"].startswith("CACHED") and len(s["records"]) == 3)
    return ok, (v["note"], v["retraction"]["line"], s["note"])


def outage_without_cache():
    v = lit.verify("10.5555/osu-workshop-never-fetched", "Anything", "Anyone")
    s = lit.search("a query nobody has run osu workshop")
    ok = (v["state"] == "unavailable" and "simulated outage" in v["reason"]
          and s["records"] == [] and s["error"] and "cover crops soil organic carbon" in s["note"])
    return ok, (v["state"], v["reason"], s["note"])


def retries_503():
    """A 503 is tried again, at most twice, and then the cache answers."""
    calls = []

    def busy(*args, **kwargs):
        calls.append(1)
        raise urllib.error.HTTPError(args[0].full_url, 503, "Service Unavailable", {}, None)
    urllib.request.urlopen = busy
    try:
        v = lit.verify(*PAPERS[0])
    finally:
        urllib.request.urlopen = failing_urlopen
    ok = len(calls) == 1 + lit.RETRIES and v["source"] == "cache" and "HTTP 503" in v["note"]
    return ok, (len(calls), v["note"])


def dead_host_asked_once():
    """A host that times out is tried three times once, then skipped for DOWN_FOR seconds."""
    calls = []

    def hangs(*args, **kwargs):
        calls.append(1)
        raise TimeoutError("simulated: the service did not answer in time")
    urllib.request.urlopen = hangs
    try:
        first = lit.verify(*PAPERS[0])
        second = lit.verify(*PAPERS[1])
    finally:
        urllib.request.urlopen = failing_urlopen
    ok = (len(calls) == 1 + lit.RETRIES and first["source"] == second["source"] == "cache"
          and "not tried again" in second["note"])
    return ok, (len(calls), second["note"])


def checker_numbers():
    """check_values.py reads a decimal written without its zero as that decimal
    (regression: ".5" was once read as 5, so a wrong value passed), keeps signs,
    ranges and units apart, and applies a conversion to the right magnitude."""
    import check_values as cv
    got = {t: cv.numbers(t) for t in (".5", "-.5", "0-.5", "a gain of .25 Mg", "10-20", "Mg C ha-1", "-14.86", "1,250", "Fig.5")}
    want = {".5": [0.5], "-.5": [-0.5], "0-.5": [0.0, 0.5], "a gain of .25 Mg": [0.25], "10-20": [10.0, 20.0],
            "Mg C ha-1": [1.0], "-14.86": [-14.86], "1,250": [1250.0], "Fig.5": [5.0]}
    row = dict(source="corpus/papers/none.pdf", page="1", quote="", value=".5", unit="", conditions="",
               value_std="-5", unit_std="x", conversion="v * -10", status="ok", note="")
    conv = [p for p in cv.check_row(row) if p.startswith("conversion")]
    return got == want and not conv, (got, conv)


def checker_refuses_bad_tables():
    """An empty table, an extra column and a column named twice are refused (exit 1);
    a file outside results/ is checked without touching results/."""
    import contextlib
    import io
    import check_values as cv
    head = ",".join(cv.COLUMNS)
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in (("empty.csv", head + "\n"), ("extra.csv", head + ",mood\nx,1,q,1,u,c,,,,ok,\n"),
                           ("twice.csv", head + ",note\nx,1,q,1,u,c,,,,ok,,\n")):
            path = Path(tmp) / name
            path.write_text(text)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cv.main([str(path)])
            out.append((name, rc, buf.getvalue().strip().replace(str(path), name)[:90]))
    said = [("no rows" in out[0][2]), ("does not have" in out[1][2]), ("named twice" in out[2][2])]
    return all(rc == 1 for _, rc, _ in out) and all(said), out


FAILURES = [("check_values reads .5 as 0.5, keeps signs and ranges", checker_numbers),
            ("check_values refuses an empty table and unexpected columns", checker_refuses_bad_tables),
            ("network down, saved answer -> cached, labeled with its date", outage_uses_cache),
            ("timeouts: the host is tried 3 times once, then skipped for a minute", dead_host_asked_once),
            ("network down, nothing saved -> unavailable, lists offline topics", outage_without_cache),
            ("HTTP 503 -> two retries, then the cache", retries_503)]


# ---------------------------------------------------------------- run

def run_offline():
    real_urlopen, real_sleep = urllib.request.urlopen, lit.time.sleep
    urllib.request.urlopen = failing_urlopen
    lit.time.sleep = lambda seconds: None            # no real waiting between retries in a test
    try:
        for name, test in COMMON + FAILURES:
            case("offline", name, test)
    finally:
        urllib.request.urlopen, lit.time.sleep = real_urlopen, real_sleep


def run_live():
    for name, test in COMMON:
        case("live", name, test)


if __name__ == "__main__":
    run_offline()
    if "--offline" in sys.argv:
        print("Live checks skipped (--offline).")
    elif network_up():
        run_live()
    else:
        print("Network unreachable: live checks skipped.")
    failed = results.count(False)
    print(f"\n{len(results) - failed} passed, {failed} failed.")
    sys.exit(1 if failed else 0)
