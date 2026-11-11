"""Find papers, check their DOIs, and write BibTeX. Standard library only.

    python 03_lit/lit.py "cover crops soil organic carbon"
    python 03_lit/lit.py "cover crops soil organic carbon" --n 5 --sort cited
    python 03_lit/lit.py --topics          the queries that work offline
    python 03_lit/lit.py "..." --offline    use only the saved answers in 03_lit/cache/

The command writes results/refs.bib and results/lit-search.json (results/ is
at the labs/ root and is never committed) and prints one line per paper:
title, year, DOI, verification state and retraction line.

Four functions do the work, and an agent can call them as tools:

    search(query, n=3, sort="relevance")   OpenAlex: candidate papers for a query
    lookup(doi)                            OpenAlex: the record for a DOI you already have (free)
    verify(doi, title=None, authors=None)  Crossref: does the DOI match, is it retracted
    bibtex(records)                        BibTeX text built from the metadata, no model

What the answers mean, and what they do not:
- search() returns candidates for a recorded query, in a recorded order, on a
  recorded date. It is not "the best papers on the topic".
- verify() says one of four things: verified, mismatched, missing, unavailable.
  "verified" means the DOI exists in Crossref and its title and first author
  match what you passed. It does not mean the paper supports any claim.
- The retraction line says "no retraction found in Crossref as of <date>" when
  Crossref lists none. That is a statement about Crossref on that date, not a
  guarantee about the paper.

Every live answer is saved in 03_lit/cache/. When a service cannot be reached,
the saved answer is used and the output says so, with the date it was saved.
No API key is needed. OpenAlex gives keyless users a small daily budget
shared by everyone on the same network address; if you have a free OpenAlex
key, put OPENALEX_API_KEY=... in .env and it is sent in a header.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# INSTRUCTOR: change this to a real address you read. OpenAlex and Crossref ask
# for one so they can contact you about a misbehaving script. It does not
# raise OpenAlex's daily budget; only an API key does.
MAILTO = "workshop@okstate.edu"

OPENALEX = "https://api.openalex.org"
CROSSREF = "https://api.crossref.org"
TIMEOUT = 15          # seconds to wait for one answer
RETRIES = 2           # extra tries after the first, for timeouts, 429 and 5xx
LONGEST_WAIT = 20     # a service asking us to wait longer than this is out of budget, not busy
SAME_TITLE = 0.85     # how alike two titles must be, 0 to 1, to count as the same

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
CACHE = HERE / "cache"   # the answers shipped with the workshop (offline topics); read, never written
# New live answers are saved outside the repository, so searching does not show up as
# changed files in git. OSU_LIT_CACHE moves it.
LOCAL_CACHE = Path(os.environ.get("OSU_LIT_CACHE") or Path.home() / ".cache" / "osu-llm-workshop" / "lit")
RESULTS = LABS / "results"

# The sort names you can pass to search(), and what OpenAlex calls them.
SORTS = {
    "relevance": "relevance_score:desc",
    "cited": "cited_by_count:desc",
    "date": "publication_date:desc",
}

# Only the fields we use, so answers (and the cache) stay small.
FIELDS = ("id,doi,display_name,publication_year,publication_date,type,authorships,"
          "primary_location,biblio,abstract_inverted_index,cited_by_count,open_access,relevance_score")

OFFLINE = False       # True makes every request fail at once, so only the cache answers (--offline)
DOWN_FOR = 60        # seconds to skip a host that did not answer at all, so a dead service costs one wait
_DOWN = {}            # {host: (when it failed, why)}


# ---------------------------------------------------------------- small helpers

def now_utc():
    """The current time in UTC, as text like 2026-11-11T15:04:05Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(text):
    """Lowercase, accents and punctuation removed, one space between words.
    Two titles that differ only in capitals, accents or punctuation come out equal."""
    text = re.sub(r"<[^>]+>", " ", text or "")            # Crossref titles can hold <i> tags
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def bare_doi(doi):
    """A DOI in one standard form: lowercase, no https://doi.org/ or doi: in front.
    Returns None for anything that does not look like a DOI."""
    if not doi:
        return None
    doi = str(doi).strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.I)
    return doi.lower() if doi.startswith("10.") and "/" in doi else None


def _openalex_key():
    """An OpenAlex API key from the environment, labs/.env, or the room's
    workshop-endpoint.txt (this copy's, or the template's current one), or ''.
    Optional. It is sent in a header, never in the URL, so it never reaches
    the cache, the results file or the screen."""
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    for path in (LABS / ".env", LABS / "workshop-endpoint.txt"):
        if key or not path.exists():
            continue
        for line in path.read_text(errors="replace").splitlines():
            if line.strip().startswith("OPENALEX_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key and _WORKSHOP_KEY[0] is None and not OFFLINE:
        # A copy made before the instructor added the room's key reads the
        # current workshop-endpoint.txt from the template, once per run.
        _WORKSHOP_KEY[0] = ""
        try:
            with urllib.request.urlopen(WORKSHOP_ENDPOINT_URL, timeout=5) as r:
                for line in r.read().decode(errors="replace").splitlines():
                    if line.strip().startswith("OPENALEX_API_KEY="):
                        _WORKSHOP_KEY[0] = line.split("=", 1)[1].strip()
        except Exception:
            pass
    return key or (_WORKSHOP_KEY[0] or "")


WORKSHOP_ENDPOINT_URL = "https://raw.githubusercontent.com/jhassell/osu-llm-workshop/main/workshop-endpoint.txt"
_WORKSHOP_KEY = [None]     # the online copy's key, fetched at most once per run


# ---------------------------------------------------------------- the network and the cache

def _cache_file(url, folder=None):
    """Where the saved answer for a URL lives. The key is a hash of the URL
    with mailto removed, so changing MAILTO does not orphan the saved answers."""
    return (folder or LOCAL_CACHE) / (hashlib.sha256(_without_mailto(url).encode()).hexdigest()[:20] + ".json")


def cache_files():
    """Every saved answer: this Codespace's own first, then the shipped ones."""
    return sorted(LOCAL_CACHE.glob("*.json")) + sorted(CACHE.glob("*.json"))


def _without_mailto(url):
    """The URL with its mailto parameter taken out."""
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True) if k != "mailto"]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query, safe=":,/")))


def _save(url, status, data):
    """Keep a live answer (a 200 or a 404) for the day the service is down."""
    if isinstance(data, dict) and isinstance(data.get("message"), dict):
        data["message"].pop("reference", None)          # Crossref reference lists are long and unused here
    if isinstance(data, dict) and isinstance(data.get("meta"), dict):
        for extra in ("notice", "x_query"):              # OpenAlex's advice to agents and its query echo
            data["meta"].pop(extra, None)                # are not data; an agent reading the cache should not act on them
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        for work in data["results"]:                     # OpenAlex authorships carry affiliations we never use
            work["authorships"] = [{"author": {"display_name": (a.get("author") or {}).get("display_name")}}
                                   for a in work.get("authorships") or []]
    entry = {"url": _without_mailto(url), "fetched_utc": now_utc(), "status": status, "body": data}
    try:
        LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
        _cache_file(url).write_text(json.dumps(entry, indent=1, ensure_ascii=False))
    except OSError:
        pass                                             # a cache we cannot write is no reason to fail


def _load(url):
    """The saved answer for a URL, or None."""
    for folder in (LOCAL_CACHE, CACHE):
        try:
            return json.loads(_cache_file(url, folder).read_text())
        except (OSError, ValueError):
            continue
    return None


def _open(url, headers):
    """One HTTP GET. Returns (status, response headers, body text). Kept separate
    so the smoke test can make the network fail in one place."""
    if OFFLINE:
        raise urllib.error.URLError("offline mode: the network was not used")
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status, dict(response.headers), response.read().decode("utf-8")


def get_json(url, headers=None):
    """Fetch a JSON answer, live if possible, from the cache if not.

    Returns a dict:
      ok           True if there is an answer to use (live or cached)
      status       200, or 404 when the service said there is no such thing
      data         the parsed JSON, or None
      source       "live" or "cache"
      fetched_utc  when the answer was fetched (for a cached one, the original date)
      error        why the live request failed, or None
      headers      the live response headers (empty for a cached answer)
    A timeout, a 429 or a 5xx is tried again, at most RETRIES more times.
    A 400 or 403 is not: asking again would get the same answer. A host that
    did not answer at all (timeouts, no network) is not asked again for
    DOWN_FOR seconds, so a dead service costs one wait, not one per paper."""
    headers = {"User-Agent": f"osu-llm-workshop-lit/1.0 (teaching tool; mailto:{MAILTO})", **(headers or {})}
    host = urllib.parse.urlsplit(url).netloc
    failed_at, error = _DOWN.get(host, (0, None))
    if time.monotonic() - failed_at > DOWN_FOR:
        error = None                                     # long enough ago: try the host again
    for attempt in range(0 if error else RETRIES + 1):   # a host that just failed is not asked again yet
        try:
            status, response_headers, body = _open(url, headers)
            data = json.loads(body)
            _save(url, status, data)
            return {"ok": True, "status": status, "data": data, "source": "live",
                    "fetched_utc": now_utc(), "error": None, "headers": response_headers}
        except urllib.error.HTTPError as err:
            if err.code == 404:
                _save(url, 404, None)                    # "no such DOI" is a real answer; keep it
                return {"ok": True, "status": 404, "data": None, "source": "live",
                        "fetched_utc": now_utc(), "error": None, "headers": dict(err.headers or {})}
            error = f"HTTP {err.code} {err.reason}"
            if err.code != 429 and err.code < 500:
                break                                    # our request is wrong; retrying will not help
            wait = _retry_after(err.headers, attempt)
            if wait is None:
                error += " (the service's daily budget is used up)"
                break
        except Exception as err:                         # timeout, no network, a reply that is not JSON
            error = f"{type(err).__name__}: {err}"
            wait = 2 * (attempt + 1)
            if attempt == RETRIES:
                _DOWN[host] = (time.monotonic(), f"{error}; not tried again for {DOWN_FOR} s")
        if attempt < RETRIES and not OFFLINE:
            time.sleep(wait)
    saved = _load(url)
    if saved:
        return {"ok": True, "status": saved["status"], "data": saved["body"], "source": "cache",
                "fetched_utc": saved["fetched_utc"], "error": error, "headers": {}}
    return {"ok": False, "status": None, "data": None, "source": None,
            "fetched_utc": None, "error": error, "headers": {}}


def _retry_after(headers, attempt):
    """Seconds to wait before trying again, or None if the wait is too long to be
    worth it (OpenAlex sends a long Retry-After when today's budget is spent)."""
    try:
        wait = float((headers or {}).get("Retry-After", ""))
    except ValueError:
        wait = 2 * (attempt + 1)
    return None if wait > LONGEST_WAIT else wait


def _cache_note(answer):
    """One plain sentence about where an answer came from."""
    if answer["source"] == "cache":
        return (f"CACHED answer saved on {answer['fetched_utc'][:10]}, not live: "
                f"the live request failed ({answer['error']}).")
    return f"Live answer, {answer['fetched_utc']}."


# ---------------------------------------------------------------- search (OpenAlex)

def search(query: str, n: int = 3, sort: str = "relevance") -> dict:
    """Search OpenAlex for papers matching a query. No API key needed.

    query: words to look for in titles, abstracts and full text, for example
           "cover crops soil organic carbon". Plain words work best.
    n:     how many papers to return (1 to 25).
    sort:  "relevance" (best match first), "cited" (most cited first) or
           "date" (newest first).

    Returns a dict that records exactly what was asked, so the search can be
    repeated and reported: query, sort (the name you gave), sort_field (what
    OpenAlex sorted by), date_utc, url (the request, without any key),
    source ("live" or "cache"), note (one sentence on where the answer came
    from), total_found, records, and error (None if all went well).

    Each record has: title, year, doi (or None), authors (a list of dicts with
    name and family), venue, volume, issue, pages, type, abstract (or None
    when OpenAlex has none), openalex_id, oa_url (a free copy, if known),
    cited_by_count.

    These are candidates returned by this query on this date, not a judgment
    of which papers are best. Check each DOI with verify()."""
    n = max(1, min(int(n), 25))
    sort = sort if sort in SORTS else "relevance"
    params = {"search": " ".join(str(query).split()), "per_page": n, "sort": SORTS[sort],
              "select": FIELDS, "mailto": MAILTO}
    url = f"{OPENALEX}/works?" + urllib.parse.urlencode(params, safe=":,")
    key = _openalex_key()
    answer = get_json(url, {"Authorization": f"Bearer {key}"} if key else None)
    result = {"query": params["search"], "sort": sort, "sort_field": SORTS[sort], "n": n,
              "date_utc": now_utc(), "url": _without_mailto(url), "service": "OpenAlex",
              "source": answer["source"], "fetched_utc": answer["fetched_utc"],
              "note": "", "total_found": None, "cost_usd": None, "budget_remaining": None,
              "records": [], "error": answer["error"]}
    if not answer["ok"]:
        result["note"] = (f"No answer from OpenAlex ({answer['error']}) and nothing saved for this exact "
                          "query. Queries that work offline: " + "; ".join(cached_topics()))
        return result
    data = answer["data"] or {}
    meta = data.get("meta", {})
    result["note"] = _cache_note(answer)
    result["total_found"] = meta.get("count")
    result["cost_usd"] = meta.get("cost_usd")
    remaining = answer["headers"].get("X-RateLimit-Remaining-USD") or answer["headers"].get("x-ratelimit-remaining-usd")
    result["budget_remaining"] = f"${remaining} of today's OpenAlex budget left" if remaining else None
    for work in data.get("results", []):              # keep whatever came back, even if fewer than n
        try:
            result["records"].append(_record(work))
        except Exception as err:                       # one odd record should not lose the others
            result["records"].append({"title": work.get("display_name"), "error": str(err)})
    return result


def lookup(doi: str) -> dict:
    """Get the OpenAlex record for one DOI you already have, for example from a
    PDF of your own. Same fields as a search() record, so it can go to verify()
    and bibtex(). Lookups by DOI are free (they do not use the search budget).
    Returns {"record": ... or None, "source", "note", "error"}."""
    clean = bare_doi(doi)
    if not clean:
        return {"record": None, "source": None, "note": "That is not a DOI.", "error": "not a DOI"}
    url = (f"{OPENALEX}/works/doi:{urllib.parse.quote(clean, safe='/')}?"
           + urllib.parse.urlencode({"select": FIELDS, "mailto": MAILTO}, safe=":,"))
    answer = get_json(url)
    if not answer["ok"]:
        return {"record": None, "source": None, "error": answer["error"],
                "note": f"No answer from OpenAlex ({answer['error']}) and nothing saved for this DOI."}
    if answer["status"] == 404:
        return {"record": None, "source": answer["source"], "error": None,
                "note": "OpenAlex has no work with this DOI. " + _cache_note(answer)}
    return {"record": _record(answer["data"]), "source": answer["source"], "error": None,
            "note": _cache_note(answer)}


def _record(work):
    """The fields we keep from one OpenAlex work."""
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    biblio = work.get("biblio") or {}
    first, last = biblio.get("first_page"), biblio.get("last_page")
    pages = f"{first}--{last}" if first and last and first != last else (first or None)
    authors = []
    for authorship in work.get("authorships") or []:
        name = ((authorship.get("author") or {}).get("display_name") or "").strip()
        if name:
            authors.append({"name": name, "family": name.split()[-1]})
    return {
        "title": re.sub(r"<[^>]+>", "", work.get("display_name") or "").strip(),
        "year": work.get("publication_year"),
        "doi": bare_doi(work.get("doi")),
        "authors": authors,
        "venue": source.get("display_name"),
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "pages": pages,
        "type": work.get("type"),
        "abstract": _abstract(work.get("abstract_inverted_index")),
        "openalex_id": work.get("id"),
        "oa_url": (work.get("open_access") or {}).get("oa_url"),
        "cited_by_count": work.get("cited_by_count"),
    }


def _abstract(inverted):
    """OpenAlex stores an abstract as {word: [positions]}; put the words back in
    order. Returns None when there is no abstract, which is common."""
    if not inverted:
        return None
    spots = [(i, word) for word, places in inverted.items() for i in places]
    return " ".join(word for _, word in sorted(spots))


def cached_topics():
    """The search queries that have a saved answer, so they work with no network."""
    topics = []
    for path in cache_files():
        try:
            url = json.loads(path.read_text())["url"]
        except (OSError, ValueError, KeyError):
            continue
        if url.startswith(OPENALEX + "/works?"):
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
            sort = next((name for name, field in SORTS.items() if field == params.get("sort")), params.get("sort"))
            topics.append(f'"{params.get("search", "")}" --n {params.get("per_page")} --sort {sort}')
    return topics


# ---------------------------------------------------------------- verify (Crossref)

def verify(doi: str, title: str | None = None, authors=None) -> dict:
    """Check one DOI against Crossref: does it exist, does it match, is it retracted.

    doi:     the DOI, with or without https://doi.org/ in front.
    title:   the title you expect. Compared after removing capitals, accents
             and punctuation, and a leading "RETRACTED:".
    authors: the authors you expect, either a list (of names, or of dicts with
             "family" or "name") or one string. Only the first author is
             compared, by family name.

    Returns a dict with:
      state       exactly one of:
                  "verified"    the DOI is in Crossref and both the title and the
                                first author's family name match what you passed
                  "mismatched"  the DOI is in Crossref but the title or the first
                                author does not match (reason says which), or you
                                did not pass one of them
                  "missing"     no DOI was given, or Crossref has no record of it
                  "unavailable" Crossref could not be reached and nothing was saved
      reason      one plain sentence explaining the state
      crossref    what Crossref holds: title, first_author, year, venue, type
      retraction  {"retracted": True/False/None, "line": one sentence, "notices": [...]}
                  The line reads "no retraction found in Crossref as of <date>"
                  when Crossref lists none; that is not a guarantee.
      source      "live" or "cache"; note says plainly when an answer is cached
    A match shows the DOI points at the paper you meant. It does not show the
    paper says what anyone cites it for."""
    clean = bare_doi(doi)
    out = {"doi": clean or doi, "state": "", "reason": "", "crossref": None, "compared": {},
           "retraction": {"retracted": None, "line": "retraction status unknown: no Crossref record", "notices": []},
           "source": None, "fetched_utc": None, "note": "", "url": None}
    if not clean:
        out.update(state="missing", reason="No DOI was given, so there was nothing to look up.")
        return out
    url = f"{CROSSREF}/works/{urllib.parse.quote(clean, safe='/')}?" + urllib.parse.urlencode({"mailto": MAILTO})
    answer = get_json(url)
    out.update(url=_without_mailto(url), source=answer["source"], fetched_utc=answer["fetched_utc"])
    if not answer["ok"]:
        out.update(state="unavailable", note=f"Crossref could not be reached ({answer['error']}).",
                   reason=f"Crossref could not be reached ({answer['error']}) and no answer was saved, "
                          "so nothing is known either way. Try again later.")
        out["retraction"]["line"] = "retraction status unknown: Crossref could not be reached"
        return out
    out["note"] = _cache_note(answer)
    if answer["status"] == 404:
        out.update(state="missing", reason=_why_missing(clean))
        out["retraction"]["line"] = "retraction status unknown: Crossref has no record of this DOI"
        return out
    work = answer["data"]["message"]
    out["crossref"] = _crossref_summary(work)
    out["retraction"] = _retraction(work, answer["fetched_utc"][:10], answer["source"])
    out["compared"] = _compare(work, title, authors)
    problems = [why for ok, why in out["compared"].values() if not ok]
    if problems:
        out.update(state="mismatched", reason="The DOI is in Crossref, but " + "; ".join(problems) + ".")
    else:
        out.update(state="verified", reason="The DOI is in Crossref and its title and first author match.")
    return out


def _why_missing(doi):
    """Why Crossref has no record of a DOI. Crossref can also say which agency
    registered a DOI: a DataCite DOI (Zenodo, arXiv, ResearchGate, most datasets)
    is real but cannot be checked here, while a DOI no agency knows is most
    likely mistyped or invented."""
    url = f"{CROSSREF}/works/{urllib.parse.quote(doi, safe='/')}/agency?" + urllib.parse.urlencode({"mailto": MAILTO})
    answer = get_json(url)
    agency = (((answer.get("data") or {}).get("message") or {}).get("agency") or {}).get("label")
    if answer["ok"] and agency and agency.lower() != "crossref":
        return (f"Crossref has no record of this DOI because it is registered with {agency}, not Crossref. "
                "The DOI exists, but its title and author were not checked here; open "
                f"https://doi.org/{doi} and compare them by hand.")
    if answer["ok"] and answer["status"] == 404:
        return ("No DOI agency knows this DOI, so it is most likely mistyped or invented. "
                f"Check it character by character, or search for the title instead.")
    return ("Crossref has no record of this DOI. Check it for typos, and see whether "
            f"https://doi.org/{doi} opens before concluding it is invented.")


def _crossref_summary(work):
    """The handful of Crossref fields a person needs to see."""
    first = _first_author(work)
    year = None
    for field in ("issued", "published", "published-print", "published-online"):
        parts = (work.get(field) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return {"title": _crossref_title(work), "first_author": first, "year": year,
            "venue": (work.get("container-title") or [None])[0], "type": work.get("type")}


def _crossref_title(work):
    """The record's title, with any subtitle after a colon."""
    title = re.sub(r"<[^>]+>", "", (work.get("title") or [""])[0]).strip()
    subtitle = re.sub(r"<[^>]+>", "", (work.get("subtitle") or [""])[0]).strip()
    return f"{title}: {subtitle}" if subtitle and norm(subtitle) not in norm(title) else title


def _first_author(work):
    """The first author's family name. Crossref marks the first author with
    sequence "first"; the list itself is not guaranteed to be in order."""
    people = work.get("author") or []
    first = next((a for a in people if a.get("sequence") == "first"), people[0] if people else {})
    return first.get("family") or first.get("name") or ""


def _strip_flag(title):
    """A title without a leading RETRACTED:, WITHDRAWN: or similar label, which
    some publishers add after the fact."""
    return re.sub(r"^\s*(retracted|withdrawn|retraction|expression of concern)\s*(article)?\s*[:.\-]\s*",
                  "", title or "", flags=re.I)


def _compare(work, title, authors):
    """{field: (matches?, reason if not)} for the title and the first author."""
    result = {}
    record_title = _crossref_title(work)
    if not title:
        result["title"] = (False, "no title was passed to compare, so it could not be checked")
    else:
        mine = norm(_strip_flag(title))
        candidates = [norm(_strip_flag(t)) for t in {record_title, (work.get("title") or [""])[0]}]
        ratio = max(difflib.SequenceMatcher(None, mine, c).ratio() for c in candidates)
        result["title"] = (ratio >= SAME_TITLE,
                           f'the title differs (Crossref has "{record_title}", similarity {ratio:.2f})')
    family = _first_author(work)
    given = _first_name_given(authors)
    if not given:
        result["first author"] = (False, "no author was passed to compare, so it could not be checked")
    elif not family:
        result["first author"] = (False, "Crossref lists no author for this DOI, so the author could not be checked")
    else:
        theirs, mine = norm(family).split(), norm(given).split()
        same = bool(theirs) and (set(theirs) <= set(mine) or (mine and mine[-1] in theirs))
        result["first author"] = (same, f'the first author differs (Crossref has "{family}", you gave "{given}")')
    return result


def _first_name_given(authors):
    """The first author from whatever was passed: a string, or a list of strings
    or dicts. "Watson, J. D." gives Watson; "James D. Watson" is kept whole and
    matched on its words."""
    if not authors:
        return ""
    first = authors[0] if isinstance(authors, (list, tuple)) else authors
    if isinstance(first, dict):
        first = first.get("family") or first.get("name") or ""
    first = str(first).strip()
    if isinstance(authors, str) and ";" in first:
        first = first.split(";")[0]
    if isinstance(authors, str) and " and " in first:
        first = first.split(" and ")[0]
    return first.split(",")[0] if "," in first else first


def _retraction(work, date, source):
    """What Crossref says about retractions and other updates to this work.

    Crossref carries Retraction Watch's data alongside publishers' own notices.
    On the paper's record, "updated-by" lists the notices that update it, each
    with type (retraction, correction, expression_of_concern, ...), the notice
    DOI, a date and a source ("publisher" or "retraction-watch"). On a notice's
    own record, "update-to" points back at the paper it updates."""
    notices = []
    for entry in work.get("updated-by") or []:
        when = ((entry.get("updated") or {}).get("date-parts") or [[None]])[0]
        notices.append({"type": entry.get("type"), "label": entry.get("label") or entry.get("type"),
                        "notice_doi": bare_doi(entry.get("DOI")), "source": entry.get("source"),
                        "date": "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(when) if p)})
    cached = " (cached answer)" if source == "cache" else ""
    serious = [n for n in notices if n["type"] in ("retraction", "withdrawal", "removal")]
    others = sorted({f"{n['label']} ({n['date']})" for n in notices if n not in serious})
    if serious:
        seen = {}
        for n in serious:
            seen.setdefault((n["label"], n["notice_doi"], n["date"]), set()).add(n["source"] or "unknown")
        parts = [f"{label} notice {doi} dated {day} (source: {', '.join(sorted(srcs))})"
                 for (label, doi, day), srcs in seen.items()]
        line = "RETRACTED according to Crossref: " + "; ".join(parts)
        retracted = True
    else:
        line = f"no retraction found in Crossref as of {date}{cached}"
        retracted = False
    if others:
        line += "; other notices: " + ", ".join(others)
    for entry in work.get("update-to") or []:          # this DOI is itself a notice about another work
        line += (f"; NOTE: this DOI is itself a {entry.get('label') or entry.get('type')} notice "
                 f"for {bare_doi(entry.get('DOI'))}, not a paper")
        break
    return {"retracted": retracted, "line": line, "notices": notices, "checked_utc": date}


# ---------------------------------------------------------------- bibtex (no model)

STOP = {"a", "an", "the"}
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def _escape(text):
    """Text made safe inside a BibTeX field: LaTeX's special characters escaped."""
    return "".join(SPECIAL.get(c, c) for c in " ".join(str(text).split()))


def _ascii_word(text):
    """Lowercase letters and digits only, accents dropped: safe in a citation key."""
    text = unicodedata.normalize("NFKD", text or "")
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in text if not unicodedata.combining(c)).lower())


def _bib_author(person):
    """One author as "Family, Given", the form BibTeX reads most reliably."""
    name = person.get("name", "") if isinstance(person, dict) else str(person)
    family = person.get("family") if isinstance(person, dict) else None
    family = family or (name.split()[-1] if name.split() else "")
    given = name[: len(name) - len(family)].strip() if name.endswith(family) else ""
    return f"{_escape(family)}, {_escape(given)}" if given else _escape(family or name)


def bibtex(records) -> str:
    """BibTeX text for a list of records from search(), built by rules, never by a model.

    The same records always give the same text. Each key is the first author's
    family name, the year and the first word of the title (skipping a, an, the),
    for example kladivko2016cover; a repeated key gets a, b, ... added. LaTeX's
    special characters (& % $ # _ { } ~ ^ \\) are escaped in every field except the
    DOI, which BibTeX tools read exactly as written. A comment line above each
    entry carries its verification state and retraction line when the record
    has them (BibTeX ignores text outside entries)."""
    out, used = [], {}
    for record in records:
        if not record.get("title"):
            continue
        authors = record.get("authors") or []
        family = authors[0].get("family", "") if authors and isinstance(authors[0], dict) else ""
        words = [w for w in (_ascii_word(w) for w in str(record["title"]).split()) if w]
        first_word = next((w for w in words if w not in STOP), words[0] if words else "untitled")
        key = f"{_ascii_word(family) or 'anon'}{record.get('year') or 'nd'}{first_word}"
        used[key] = used.get(key, 0) + 1
        if used[key] > 1:
            key += "abcdefghijklmnopqrstuvwxyz"[used[key] - 2]
        kind = "article" if record.get("type") in ("article", "review", "journal-article") else "misc"
        fields = [("author", " and ".join(_bib_author(a) for a in authors)),
                  ("title", "{" + _escape(record["title"]) + "}"),     # inner braces keep its capitals
                  ("journal" if kind == "article" else "howpublished", _escape(record.get("venue") or "")),
                  ("year", str(record.get("year") or "")),
                  ("volume", _escape(record.get("volume") or "")),
                  ("number", _escape(record.get("issue") or "")),
                  ("pages", _escape(record.get("pages") or "")),
                  ("doi", re.sub(r"[{}\s]", "", record.get("doi") or ""))]     # DOIs are read verbatim; never escape them
        check = record.get("verification")
        if check:
            out.append(f"% {key}: DOI {check['state']}; {check['retraction']['line']}")
        body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields if value)
        out.append(f"@{kind}{{{key},\n{body}\n}}\n")
    return "\n".join(out)


# ---------------------------------------------------------------- the command

def run(query, n=3, sort="relevance"):
    """Search, verify every DOI found, write results/refs.bib and
    results/lit-search.json, and return the search result with each record's
    verification attached. A failed check never drops a paper. A search that
    returns nothing writes nothing, so earlier results are not wiped out."""
    result = search(query, n=n, sort=sort)
    for record in result["records"]:
        if record.get("error"):
            continue
        record["verification"] = verify(record.get("doi"), record.get("title"), record.get("authors"))
    if not result["records"]:
        return result                                  # nothing came back: keep any earlier results as they are
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "lit-search.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    header = (f"% Written by 03_lit/lit.py from the metadata below, not by a model.\n"
              f"% OpenAlex query: {result['query']}\n% Sorted by: {result['sort_field']}\n"
              f"% Searched: {result['date_utc']} ({result['note']})\n\n")
    (RESULTS / "refs.bib").write_text(header + bibtex(result["records"]))
    return result


def show(result):
    """Print a search result as a short table, one paper per block."""
    print(f'Query: "{result["query"]}"   sorted by {result["sort_field"]}   {result["date_utc"]}')
    print(result["note"])
    if result.get("budget_remaining"):
        print(result["budget_remaining"])
    if not result["records"]:
        print("No papers came back, so results/ was not changed.")
        return
    print()
    for i, record in enumerate(result["records"], 1):
        check = record.get("verification") or {}
        title = record.get("title") or "(no title)"
        print(f"{i}. {title[:90]}{'...' if len(title) > 90 else ''}")
        print(f"   {record.get('year') or '?'}   DOI {record.get('doi') or '(none)'}   "
              f"{check.get('state', 'not checked')}"
              + ("   (cached)" if check.get("source") == "cache" else ""))
        if check.get("state") and check["state"] != "verified":
            print(f"   why: {check['reason']}")
        print(f"   retraction: {(check.get('retraction') or {}).get('line', 'not checked')}")
        if record.get("abstract") is None and not record.get("error"):
            print("   no abstract in OpenAlex")
    print(f"\nWrote {RESULTS.relative_to(LABS)}/refs.bib and {RESULTS.relative_to(LABS)}/lit-search.json")


def main(argv=None):
    global OFFLINE
    parser = argparse.ArgumentParser(description="Search OpenAlex, verify DOIs in Crossref, write BibTeX.")
    parser.add_argument("query", nargs="?", help='what to search for, in quotes')
    parser.add_argument("--n", type=int, default=3, help="how many papers (default 3)")
    parser.add_argument("--sort", choices=sorted(SORTS), default="relevance", help="order (default relevance)")
    parser.add_argument("--offline", action="store_true", help="use only saved answers in 03_lit/cache/")
    parser.add_argument("--topics", action="store_true", help="list the queries that work offline")
    args = parser.parse_args(argv)
    if args.topics or not args.query:
        print("Queries with saved answers (they work offline):")
        for topic in cached_topics():
            print("  " + topic)
        if not args.query:
            print('\nUsage: python 03_lit/lit.py "your query"   [--n 3] [--sort relevance|cited|date] [--offline]')
        return 0
    OFFLINE = args.offline
    result = run(args.query, n=args.n, sort=args.sort)
    show(result)
    return 0 if result["records"] else 1


if __name__ == "__main__":
    sys.exit(main())
