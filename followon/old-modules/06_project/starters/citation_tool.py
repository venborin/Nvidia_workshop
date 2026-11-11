"""A citation checker against Crossref's public catalogue. A tested starting point: run it, then change it.

    python 06_project/starters/citation_tool.py

What it accepts: one citation as text. That can be a DOI (10.1038/171737a0),
a DOI link (https://doi.org/10.1038/171737a0), or a reference written out
with authors, year and title, in any common style, such as

    Watson, J. D., & Crick, F. H. C. (1953). Molecular structure of nucleic
    acids. Nature, 171, 737-738. https://doi.org/10.1038/171737a0

on one line. 'all' checks every line of sample_citations.txt, a small test
bibliography with some deliberate mistakes in it.

With a DOI it fetches that DOI's record and compares the title, the first
author's surname and the year with what the citation says. Without one it
asks Crossref for the three closest records and compares the same way. It
reports what it found, never a guess, and it says when it could not look.

Crossref holds most journal articles, but not everything: arXiv preprints and
datasets are registered with DataCite, and many books are elsewhere. So "no
match in this service" means look further, not "this does not exist".

Etiquette: one request at a time, a 10 second timeout, at most one retry, and
answers are cached. crossref_cache.json, next to this file, holds the answers
for the sample citations, so they work offline; new lookups are cached under
~/.cache/osu-llm-workshop/crossref/. Set CROSSREF_MAILTO to your own email
address to identify yourself to Crossref (a shared address shares one rate
limit). Test switch: CROSSREF_API=http://127.0.0.1:9 points the tool at an
address where nothing answers, to see what it does offline.
"""
import difflib
import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CITATIONS = HERE / "sample_citations.txt"     # or yours: HERE.parents[3] / "mine" / "your_list.txt", one citation per line
COMMITTED = HERE / "crossref_cache.json"
LOCAL = Path.home() / ".cache" / "osu-llm-workshop" / "crossref"
API = os.environ.get("CROSSREF_API", "https://api.crossref.org").rstrip("/")
MAILTO = os.environ.get("CROSSREF_MAILTO", "").strip()
SAME_TITLE = 0.85                             # title similarity needed to call two titles the same
DOI = re.compile(r"10\.\d{4,9}/[^\s\"<>]+")
_last = 0.0                                   # when the last request went out
SUPPORT = ("Existence is not support: a record shows the work exists, not that it says "
           "what it was cited for. Read it before you rely on it.")


def norm(text):
    """Lowercase, accents and punctuation removed, one space between words."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def find_doi(text):
    """(doi, the text with the DOI and any doi.org or doi: prefix removed)."""
    m = DOI.search(text)
    if not m:
        return None, text
    doi = m.group(0).rstrip(".,;")
    while doi.endswith(")") and doi.count("(") < doi.count(")"):
        doi = doi[:-1]
    rest = re.sub(r"(https?://(dx\.)?doi\.org/|doi:\s*)?" + re.escape(doi), " ", text, flags=re.I)
    return doi, rest


def trim(item):
    """The four things the comparison uses, from one Crossref work."""
    first = (item.get("author") or [{}])[0]
    years = {(item.get(k) or {}).get("date-parts", [[None]])[0][0]
             for k in ("issued", "published-print", "published-online")}
    return {"DOI": item.get("DOI", "?"), "title": (item.get("title") or ["(no title)"])[0],
            "first_author": first.get("family") or first.get("name") or "",
            "years": sorted(y for y in years if isinstance(y, int))}


def fetch(url):
    """{'status': 200 or 404, 'records': [...]}, or a string saying why the lookup failed."""
    global _last
    agent = "osu-llm-workshop-citation-check/1.0 (OSU LLM workshop teaching tool)"
    if MAILTO:
        agent = agent[:-1] + f"; mailto:{MAILTO})"
        url += ("&" if "?" in url else "?") + "mailto=" + urllib.parse.quote(MAILTO)
    why = "?"
    for attempt in (1, 2):                     # at most one retry
        time.sleep(max(0.0, _last + 1 - time.monotonic()))   # at most one request a second
        _last = time.monotonic()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": agent})
            with urllib.request.urlopen(request, timeout=10) as response:
                message = json.load(response)["message"]
            items = message.get("items", [message])
            return {"status": 200, "records": [trim(i) for i in items]}
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return {"status": 404, "records": []}
            why = f"Crossref answered HTTP {err.code}"
            if err.code != 429 and err.code < 500:
                break
        except Exception as err:               # timeout, no network, a reply that is not JSON
            why = f"{type(err).__name__}: {err}"
        if attempt == 1:
            time.sleep(2)
    return why


def lookup(key, url):
    """(entry, where it came from). Committed cache first, then the local cache, then Crossref."""
    try:
        committed = json.loads(COMMITTED.read_text())
    except (OSError, ValueError):
        committed = {}
    if key in committed:
        return committed[key], "the cache committed with this tool"
    local = LOCAL / (hashlib.sha1(key.encode()).hexdigest() + ".json")
    try:
        return json.loads(local.read_text()), "your local cache"
    except (OSError, ValueError):
        pass
    entry = fetch(url)
    if isinstance(entry, dict):
        try:
            LOCAL.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(entry))
        except OSError:
            pass                               # a cache that cannot be written is not worth failing over
    return entry, "Crossref, just now"


def key_and_url(citation):
    """The cache key and the Crossref URL for one citation."""
    doi, rest = find_doi(citation)
    if doi:
        return f"doi:{doi.lower()}", f"{API}/works/{urllib.parse.quote(doi, safe='/')}"
    return (f"query:{norm(citation)}",
            f"{API}/works?rows=3&query.bibliographic={urllib.parse.quote(citation.strip())}")


def title_similarity(title, text):
    """How closely the record's title matches some run of sentences in the citation, 0 to 1."""
    target = norm(title)
    pieces = [p for p in (norm(s) for s in re.split(r"[.?!][\"'”’]?\s+", text)) if p]
    best = 0.0
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces) + 1):
            span = " ".join(pieces[i:j])
            best = max(best, difflib.SequenceMatcher(None, target, span).ratio())
            if len(span) > 2 * len(target):
                break
    return best


def compare(record, text):
    """[(field, agrees, evidence)] for title, first author and year, skipping what the citation does not give."""
    out = []
    if len(re.findall(r"[A-Za-z]{2,}", text)) >= 3:
        ratio = title_similarity(record["title"], text)
        out.append(("title", ratio >= SAME_TITLE, f"title similarity {ratio:.2f}"))
        surname = norm(record["first_author"])
        if not surname:
            out.append(("first author", True, "the record lists no author, so none was compared"))
        else:
            found = f" {surname} " in f" {norm(text)} "
            out.append(("first author", found, f"first author {record['first_author']} "
                        + ("appears in the citation" if found else "does not appear in the citation")))
    cited = {int(y) for y in re.findall(r"(?<!\d)(1[6-9]\d\d|20\d\d)(?!\d)", text)}
    if cited:
        shown = "/".join(map(str, record["years"])) or "none"
        agrees = bool(cited & set(record["years"]))
        out.append(("year", agrees, f"cited {'/'.join(map(str, sorted(cited)))}, record {shown}"))
    return out


def describe(record):
    years = "/".join(map(str, record["years"])) or "no year"
    return (f"\"{record['title']}\"; first author {record['first_author'] or 'not listed'}; "
            f"{years}; DOI {record['DOI']}")


def check_one(citation):
    """The verdict and its evidence for one citation, without the closing line."""
    doi, rest = find_doi(citation)
    key, url = key_and_url(citation)
    entry, source = lookup(key, url)
    if isinstance(entry, str):
        return (f"Checked: lookup unavailable. The Crossref lookup failed ({entry}), so nothing "
                "was established either way. Try again later; the citation is neither confirmed nor ruled out.")
    if entry["status"] == 404 or not entry["records"]:
        what = f"the DOI {doi}" if doi else "this reference"
        return (f"Checked: no match in this service. Crossref has no record of {what} (source: {source}). "
                "That is not proof the work does not exist: arXiv preprints (DOIs beginning 10.48550) and "
                "datasets are registered with DataCite, not Crossref, and many books are elsewhere. "
                + (f"See whether https://doi.org/{doi} resolves, or search for the title." if doi
                   else "Search for the title elsewhere before you conclude anything."))
    if doi:
        record = entry["records"][0]
        fields = compare(record, rest)
        differ = [f for f, ok, _ in fields if not ok]
        evidence = "; ".join(e for _, _, e in fields) or "only the DOI was given, so only the DOI was compared"
        verdict = (f"DOI found, metadata does not match ({', '.join(differ)} differ{'s' if len(differ) == 1 else ''})"
                   if differ else "DOI found, metadata matches")
        return f"Checked: {verdict}. Crossref record (source: {source}): {describe(record)}. Compared: {evidence}."
    scored = sorted(((title_similarity(r["title"], citation), r) for r in entry["records"]),
                    key=lambda pair: -pair[0])
    ratio, record = scored[0]
    fields = "; ".join(e for f, _, e in compare(record, citation) if f != "title") or "nothing else to compare"
    if ratio >= SAME_TITLE:
        return (f"Checked: possible match by title (similarity {ratio:.2f}). The citation gives no DOI; the "
                f"closest Crossref record (source: {source}) is {describe(record)}. Also compared: {fields}. "
                "Confirm it is the same work before adding the DOI.")
    return (f"Checked: no match in this service. None of the {len(scored)} closest Crossref records has this "
            f"title; the closest (similarity {ratio:.2f}, {SAME_TITLE} needed; source: {source}) is "
            f"{describe(record)}. That is not proof the work does not exist: datasets and arXiv preprints are "
            "registered with DataCite, and many books are elsewhere. But a reference nobody can find is one "
            "to ask its source about before you cite it.")


def check_citation(citation: str) -> str:
    """Use this to check whether a reference is real and correctly cited, before trusting
    or repeating it. Pass ONE citation per call: a DOI, a doi.org link, or a reference
    with authors, year and title, copied exactly. Or pass 'all' to check every entry in
    the test bibliography, sample_citations.txt. Looks each one up in Crossref and
    returns a verdict (DOI found, metadata matches; DOI found, metadata does not match;
    possible match by title; no match in this service; lookup unavailable) with the
    evidence: the Crossref record's title, first author, year and DOI, and which fields
    differ. A missing record is not proof a work does not exist, and a record that exists
    does not show the work supports the claim it was cited for."""
    text = " ".join(str(citation).split())
    if text.lower() in ("all", "*"):
        if not CITATIONS.exists():
            return f"Checked: nothing, because there is no file at {CITATIONS}.\n{SUPPORT}"
        lines = [ln.strip() for ln in CITATIONS.read_text().splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")]
        out = [f"Checked {len(lines)} citations from {CITATIONS.name}, one verdict each:"]
        for number, line in enumerate(lines, start=1):
            # The whole line, not a shortened one: a model shown half a title will finish it from memory.
            out.append(f"\n[{number}] {line}\n{check_one(line)}")
        return "\n".join(out) + f"\n\n{SUPPORT}"
    if len(text) < 6:
        return ("Checked: nothing, because that is not a citation. Give a DOI, a doi.org link, or a "
                f"reference with authors, year and title; or 'all' for {CITATIONS.name}.\n{SUPPORT}")
    return f"{check_one(text)}\n{SUPPORT}"


if __name__ == "__main__":
    print(check_citation("all"))
    print()
    print(check_citation("10.1038/171737a0"))
    print()
    print(check_citation("Smith"))
