#!/usr/bin/env python3
"""Check site/ before calling the website done.

site/ is served publicly on port 8000 while the Codespace runs (see
site-public.sh), and bash publish-site.sh can put a copy of it on GitHub Pages
for good. Both publish only the real files inside site/.

Every readable text file is scanned, whatever it is called: a key in .env,
notes.txt or a file with no extension is as public as one in index.html. Files
that look binary (images, PDFs, fonts) are skipped.

Fails (exit 1) on:
  - anything that looks like a secret: an OpenRouter, NVIDIA or GitHub key, a
    private key block, a line that sets LLM_API_KEY, or the actual key saved in
    .env or in ~/.openclaw/openclaw.json, whatever its shape
  - a symlink anywhere in site/, or site/ itself being one
  - a root-absolute link (href="/...", src="/...", url(/...) in HTML or CSS:
    the permanent site lives under /<repository name>/, where those break.
    A link that starts with // is a full address and is fine.
  - no site/index.html (or no site/ folder at all)

Warns (exit 0) on things a person should look at:
  - a script loaded from another website
  - a local link to a missing file, or to a file outside site/
  - a file larger than 5 MB
  - email addresses at a .edu domain, numbers shaped like student IDs, and
    64-character hex strings

It prints only file names, line numbers and short labels, never the matched
text, so its output is safe to paste anywhere.

Usage: python3 .devcontainer/site-check.py [path/to/site]
Adapted from jhassell/asee9 (CC BY 4.0).
"""
import json
import os
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML_SUFFIXES = (".html", ".htm")
CSS_SUFFIXES = (".css",)
READ_LIMIT = 8 * 1024 * 1024   # links and personal data: this much of one file
CHUNK = 4 * 1024 * 1024        # keys: the whole file, this much at a time
OVERLAP = 4096                 # carried between chunks, so a key on a boundary is still seen
HEAD_BYTES = 8192              # this much decides text or binary
BIG_FILE = 5 * 1024 * 1024

# Each pattern starts at a word edge, so "task-based-learning" is not "sk-...".
EDGE = r"(?<![A-Za-z0-9_-])"
SECRETS = [
    (re.compile(EDGE + r"sk-or-[A-Za-z0-9_-]{10,}"), "an OpenRouter key"),
    (re.compile(EDGE + r"nvapi-[A-Za-z0-9_-]{10,}"), "an NVIDIA key"),
    (re.compile(EDGE + r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"), "a GitHub token"),
    (re.compile(EDGE + r"sk-[A-Za-z0-9_-]{30,}"), "an API key (sk-...)"),
    (re.compile(EDGE + r"AKIA[0-9A-Z]{16}"), "an AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"^\s*(?:export\s+)?LLM_API_KEY\s*=", re.MULTILINE), "a line that sets LLM_API_KEY"),
]
EDU_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+edu\b", re.IGNORECASE)
# 7 to 10 digits standing alone: the shape of most student ID numbers. Years,
# page numbers and prices are shorter; phone numbers with separators do not match.
ID_LIKE = re.compile(r"(?<![\w.,/-])\d{7,10}(?![\w.,/-])")
HEX64 = re.compile(r"(?<![0-9A-Za-z])[0-9a-f]{64}(?![0-9A-Za-z])")
# CSS: url(/x) and @import "/x", but not url(//host/x).
CSS_ROOT_ABS = re.compile(r"""(?:url\(\s*['"]?|@import\s+['"])/(?!/)""", re.IGNORECASE)
LINK_ATTRS = ("href", "src", "action", "poster", "data", "formaction")
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def real_keys():
    """The keys this Codespace actually uses, to find them whatever their shape."""
    keys = set()
    try:
        for line in (ROOT / ".env").read_text(errors="ignore").splitlines():
            m = re.match(r"\s*(?:export\s+)?LLM_API_KEY\s*=\s*(.*)$", line)
            if m:
                keys.add(m.group(1).strip().strip("'\""))
    except OSError:
        pass
    try:
        cfg = json.loads(pathlib.Path.home().joinpath(".openclaw", "openclaw.json").read_text())
        for p in ((cfg.get("models") or {}).get("providers") or {}).values():
            if isinstance(p, dict) and isinstance(p.get("apiKey"), str):
                keys.add(p["apiKey"].strip())
    except (OSError, ValueError, AttributeError):
        pass
    for name in ("LLM_API_KEY", "GITHUB_TOKEN", "GH_TOKEN"):
        keys.add(os.environ.get(name, "").strip())
    return [k for k in keys if len(k) >= 8]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []      # (line, attribute value)
        self.scripts = []    # line of each <script src> from another site
        self.styles = []     # (line, inline CSS)
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        for k, v in attrs:
            if not v:
                continue
            if k in LINK_ATTRS:
                self.links.append((line, v.strip()))
            elif k in ("srcset", "imagesrcset"):
                for part in v.split(","):
                    if part.strip():
                        self.links.append((line, part.strip().split()[0]))
            elif k == "style":
                self.styles.append((line, v))
        if tag == "script":
            src = dict(attrs).get("src") or ""
            if EXTERNAL.match(src.strip()):
                self.scripts.append(line)
        self._in_style = tag == "style"

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.styles.append((self.getpos()[0], data))


def read_text(path):
    """The file's text, or None if it is binary or cannot be read."""
    try:
        with open(path, "rb") as fh:
            data = fh.read(READ_LIMIT)
    except OSError:
        return None
    head = data[:HEAD_BYTES]
    if b"\x00" in head:
        return None
    if head:
        odd = sum(1 for b in head if (b < 32 and b not in (8, 9, 10, 12, 13)) or b == 127)
        if odd / len(head) > 0.15:
            return None
    return data.decode("utf-8", "ignore")


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def scan_secrets(path, keys):
    """[(line, label)] for the first key-shaped string and the first real key in
    the whole file, read in chunks so a large file is checked to its end."""
    found = {}
    start_line = 1          # line number where `text` begins
    tail = ""
    try:
        fh = open(path, "rb")
    except OSError:
        return []
    with fh:
        while len(found) < 2:
            data = fh.read(CHUNK)
            if not data:
                break
            text = tail + data.decode("utf-8", "ignore")
            if "pattern" not in found:
                for rx, what in SECRETS:
                    m = rx.search(text)
                    if m:
                        found["pattern"] = (start_line + text.count("\n", 0, m.start()), f"looks like {what}")
                        break
            if "key" not in found:
                for k in keys:
                    i = text.find(k)
                    if i >= 0:
                        found["key"] = (start_line + text.count("\n", 0, i), "contains the key this Codespace uses")
                        break
            keep = text[-OVERLAP:] if len(text) > OVERLAP else text
            start_line += text[: len(text) - len(keep)].count("\n")
            tail = keep
    return [found[k] for k in ("pattern", "key") if k in found]


def check(site):
    """Returns (files, problems, warnings); files is None if there is no folder."""
    problems, warnings = [], []
    label = site.name + "/"
    if site.is_symlink():
        problems.append(f"{label} is a symlink. It must be a real folder.")
        return [], problems, warnings
    if not site.is_dir():
        return None, problems, warnings
    site_real = site.resolve()

    def rel(p):
        return f"{label}{p.relative_to(site).as_posix()}"

    files = []
    for dirpath, dirnames, filenames in os.walk(site, followlinks=False):
        d = pathlib.Path(dirpath)
        for name in sorted(dirnames + filenames):
            p = d / name
            if p.is_symlink():
                problems.append(f"{rel(p)}: is a symlink. site/ must hold real files.")
            elif name in filenames and p.is_file():
                files.append(p)
        dirnames[:] = [n for n in dirnames if not (d / n).is_symlink()]
    files.sort()

    keys = real_keys()
    for f in files:
        name = rel(f)
        try:
            if f.stat().st_size > BIG_FILE:
                warnings.append(f"{name}: larger than 5 MB. Is it needed on the site?")
        except OSError:
            pass
        raw = read_text(f)
        if raw is None:
            continue           # binary or unreadable: nothing to scan
        # Keys: the whole file. One of each kind is enough to stop; the person looks at the file.
        for line, what in scan_secrets(f, keys):
            problems.append(f"{name} line {line}: {what}")
        try:
            if f.stat().st_size > READ_LIMIT:
                warnings.append(f"{name}: over 8 MB. It was checked for keys to the end, "
                                "but only its first 8 MB for links and personal data.")
        except OSError:
            pass

        css = []
        suffix = f.suffix.lower()
        if suffix in CSS_SUFFIXES:
            css.append((1, raw))
        if suffix in HTML_SUFFIXES:
            parser = Links()
            try:
                parser.feed(raw)
                parser.close()
            except Exception:
                warnings.append(f"{name}: could not be read as HTML")
            css.extend(parser.styles)
            for line in parser.scripts:
                warnings.append(f"{name} line {line}: loads a script from another website")
            for line, link in parser.links:
                if link.startswith("/") and not link.startswith("//"):
                    problems.append(
                        f"{name} line {line}: root-absolute link (starts with /). "
                        "Use a relative link, such as lesson2.html")
                    continue
                if EXTERNAL.match(link) or link.startswith("#"):
                    continue
                path = link.split("#")[0].split("?")[0]
                if not path:
                    continue
                target = f.parent / path
                try:
                    real = target.resolve()
                except (OSError, RuntimeError):
                    real = None
                if real is None or (real != site_real and site_real not in real.parents):
                    warnings.append(f"{name} line {line}: local link points outside site/; it will be missing")
                elif not real.exists():
                    warnings.append(f"{name} line {line}: local link to a missing file")
        for start, block in css:
            for m in CSS_ROOT_ABS.finditer(block):
                problems.append(
                    f"{name} line {start + line_of(block, m.start()) - 1}: root-absolute url(/...) in CSS. "
                    "Use a relative path")

        n = len(EDU_EMAIL.findall(raw))
        if n:
            warnings.append(f"{name}: {n} .edu email address(es). Are they meant to be public?")
        n = len(ID_LIKE.findall(raw))
        if n:
            warnings.append(f"{name}: {n} number(s) shaped like student IDs (7-10 digits). Check them.")
        n = len(HEX64.findall(raw))
        if n:
            warnings.append(f"{name}: {n} 64-character hex string(s). A checksum is fine; an access token is not.")
    if not (site / "index.html").is_file():
        problems.append(f"{label}index.html is missing (it is the page the address opens)")
    return files, problems, warnings


def main():
    site = pathlib.Path(sys.argv[1]).absolute() if len(sys.argv) > 1 else ROOT / "site"
    files, problems, warnings = check(site)
    if files is None:
        print(f"NOT READY: there is no {site.name}/ folder yet.")
        return 1
    print(f"Checked {len(files)} file(s) in {site.name}/.")
    for w in warnings:
        print("  WARNING: " + w)
    if problems:
        print("NOT READY TO BE PUBLIC:")
        for p in problems:
            print("  - " + p)
        return 1
    print("OK: no key-like strings, no symlinks, no root-absolute links, index.html present.")
    if warnings:
        print("Look at the warnings above before sharing the address.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
