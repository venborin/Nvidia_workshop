"""A reader for BibTeX files, in one common layout. A tested starting point: run it, then change it.

    python 06_project/starters/bibtex_tool.py

What it accepts: entries laid out the way most reference managers export them,

    @article{key,
      title  = {Title in braces},
      author = {Last, First and Last, First},
      year   = {2023}
    }

one field per line, every value in braces. It does not handle quoted values
("..."), bare numbers (year = 2023), or a whole entry on one line. Instead of
guessing, it reads what it can and says how many entries or fields it skipped,
so "no entry matches" is never said about an entry it could not read.
"""
import re
from pathlib import Path

BIB = Path(__file__).resolve().parent / "sample.bib"      # or yours: Path(__file__).resolve().parents[4] / "mine" / "your_file.bib"
FIELD = re.compile(r"^\s*(\w+)\s*=\s*\{(.*)\}\s*,?\s*$")


def read_bib():
    """([(key, fields)], problems), or an error string."""
    if not BIB.exists():
        return f"error: no file at {BIB}"
    entries, problems = [], []
    for chunk in re.split(r"(?m)^(?=\s*@)", BIB.read_text()):
        chunk = chunk.strip()
        if not chunk.startswith("@"):
            continue
        head = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,\s*\n(.*)\n\s*\}\s*$", chunk, flags=re.S)
        if not head:
            problems.append(chunk.splitlines()[0][:40])
            continue
        fields, unread = {}, 0
        for line in head.group(3).splitlines():
            if "=" not in line:
                continue
            m = FIELD.match(line)
            if m:
                fields[m.group(1).lower()] = m.group(2)
            else:
                unread += 1
        if unread:
            problems.append(f"{head.group(2)} ({unread} field(s) not in braces)")
        entries.append((head.group(2), fields))
    if not entries and not problems:
        return "error: no '@type{key,' entries found; this does not look like BibTeX"
    return entries, problems


def find_references(query: str) -> str:
    """Search a BibTeX reference list by any word in the title, author or year.
    Returns one line per matching entry: key, every author, year, title. Use
    'all' to list every entry. Ends with a note if some entries or fields
    could not be read, so a missing match is not taken as proof of absence."""
    want = query.strip().lower()
    read = read_bib()
    if isinstance(read, str):
        return read
    entries, problems = read
    lines = []
    for key, fields in entries:
        hay = " ".join(fields.values()).lower() + " " + key.lower()
        if want in ("all", "", "*") or want in hay:
            # Every author, not only the first: a tool's output has to show why it matched.
            authors = "; ".join(a.strip() for a in fields.get("author", "?").split(" and "))
            lines.append(f"{key}: {authors} ({fields.get('year', '?')}). {fields.get('title', '?')}")
    if not lines:
        lines.append(f"no entry matches {query!r} among the {len(entries)} entries read")
    if problems:
        lines.append(f"note: could not fully read {len(problems)} entr{'y' if len(problems) == 1 else 'ies'}: "
                     f"{'; '.join(problems)}. This reader expects one field per line, values in braces.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(find_references("all"))
    print()
    print(find_references("okafor"))
    print()
    print(find_references("unobtainium"))
