#!/usr/bin/env bash
# gallery.sh: post a card to the workshop's show-and-tell wall. Optional.
#
#   bash gallery.sh          answer a few questions, check the card, post it
#   bash gallery.sh --help   this text
#
# The card says what your site is about and one thing the agent got wrong
# that you caught and corrected. After lunch you can add your question, the
# tool you built, and one result someone could check.
#
# How it gets posted: this script prints a link to a new GitHub issue on
# github.com/jhassell/osu-llm-workshop with your card already filled in. You
# open the link in your own browser, where you are already signed in, and
# click Submit new issue. Nothing is sent until you click it. The issue is
# public and shows your GitHub account, even if you leave the name blank.
#
# It reads only your two site addresses, from ~/.osu-llm-workshop-site-url
# and ~/.osu-llm-workshop-pages-url. It never reads .env or any key.
#
# To change your card later, run it again: the wall shows your newest card.
set -uo pipefail

REPO="jhassell/osu-llm-workshop"
NEW_ISSUE="https://github.com/$REPO/issues/new"
SITE_URL_FILE="$HOME/.osu-llm-workshop-site-url"
PAGES_URL_FILE="$HOME/.osu-llm-workshop-pages-url"

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1   (try: bash gallery.sh --help)"; exit 2 ;;
  esac
  shift
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "This needs python3, which every workshop Codespace has."
  exit 1
fi
if ! { : </dev/tty; } 2>/dev/null; then
  echo "Run this in a terminal, where it can ask you questions:   bash gallery.sh"
  exit 1
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/gallery.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT

hr() { echo "=============================================="; }
cancelled() { echo; echo "Nothing was posted."; exit 0; }

# ask VAR "prompt": one line from the keyboard into VAR. Ctrl-D cancels.
ask() {
  local line
  printf '%s' "$2"
  IFS= read -r line </dev/tty || cancelled
  eval "$1=\$line"
}
# ask_required VAR "prompt": ask until the answer is not blank.
ask_required() {
  local v=""
  while :; do
    ask v "$2"
    case "$v" in *[![:space:]]*) break ;; esac
    echo "   This one is needed. Type an answer, or press Ctrl-C to stop."
  done
  eval "$1=\$v"
}

first_line() { [ -s "$1" ] && head -1 "$1" | tr -d '\r'; }

hr; echo " Show-and-tell card"; hr
echo "Optional. Your card becomes a public GitHub issue on $REPO,"
echo "under your GitHub account. You see it in full before anything is posted."
echo "Press Enter to skip any question marked (optional)."
echo

ask          NAME    "Name to show (optional, blank means anonymous): "
ask_required TOPIC   "Topic of your tutorial site: "
echo "What did the agent get wrong, and what did you correct?"
ask_required CAUGHT  "One or two sentences: "
echo
echo "The next three are for after lunch. Press Enter to skip them."
ask          QUESTION "Your research question (optional): "
ask          TOOL     "The tool you built (optional): "
ask          RESULT   "One result someone could check (optional): "
ask          PRESENT  "Willing to present at show and tell (4:00)? (y/N): "
case "$PRESENT" in [Yy]*) PRESENT=yes ;; *) PRESENT=no ;; esac

LIVE="$(first_line "$SITE_URL_FILE")"
PERM="$(first_line "$PAGES_URL_FILE")"

# Python builds the title, the body and the link. The answers go to it in its
# environment, never on a command line, and come back as files in $TMP.
GALLERY_NAME="$NAME" GALLERY_TOPIC="$TOPIC" GALLERY_CAUGHT="$CAUGHT" \
GALLERY_QUESTION="$QUESTION" GALLERY_TOOL="$TOOL" GALLERY_RESULT="$RESULT" \
GALLERY_PRESENT="$PRESENT" GALLERY_LIVE="$LIVE" GALLERY_PERM="$PERM" \
GALLERY_OUT="$TMP" GALLERY_NEW_ISSUE="$NEW_ISSUE" \
python3 - <<'PY' || { echo "Could not build the card. Nothing was posted."; exit 1; }
import os, unicodedata, urllib.parse

LIMIT = 6000          # GitHub refuses links much past 8000 characters
TITLE_MAX = 80
BIDI = set("\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")   # text-direction overrides

shortened = []

def field(name, cap, label=None):
    raw = os.environb.get(("GALLERY_" + name).encode(), b"").decode("utf-8", "replace")
    # One line, no control characters: a pasted escape code, tab, line break
    # or text-direction override would otherwise end up in a public issue.
    text = "".join(" " if unicodedata.category(c) in ("Cc", "Zl", "Zp") or c in BIDI else c
                   for c in raw).strip()
    if len(text) <= cap:
        return text
    if label:
        shortened.append(label)
    return text[:cap].rstrip() + "..."

name = field("NAME", 60, "name")
topic = field("TOPIC", 120, "topic")
fields = [
    ("Name", name or "anonymous"),
    ("Topic", topic),
    ("Permanent site", field("PERM", 300)),
    ("Live site", field("LIVE", 300)),
    ("Caught and corrected", field("CAUGHT", 1000, "what you corrected")),
    ("Question", field("QUESTION", 1000, "question")),
    ("Tool", field("TOOL", 1000, "tool")),
    ("Checkable result", field("RESULT", 1000, "checkable result")),
    ("Present", field("PRESENT", 3)),
]
title = "Gallery: " + (topic if len(topic) <= TITLE_MAX else topic[:TITLE_MAX].rstrip() + "...")

def body_of(fs):
    return "\n".join("%s: %s" % (k, v) for k, v in fs if v) + "\n"

def url_of(fs):
    q = urllib.parse.quote
    return "%s?title=%s&body=%s" % (os.environ["GALLERY_NEW_ISSUE"], q(title, safe=""), q(body_of(fs), safe=""))

notes = []
if shortened:
    notes.append("Shortened to keep the card readable: %s." % ", ".join(shortened))
dropped = []
for key in ("Checkable result", "Tool", "Question"):
    if len(url_of(fields)) <= LIMIT:
        break
    i = [k for k, _ in fields].index(key)
    if fields[i][1]:
        dropped.append(key.lower())
        fields[i] = (key, "")
if dropped:
    notes.append("The card was too long for one link, so these were left out: %s." % ", ".join(dropped))
i = [k for k, _ in fields].index("Caught and corrected")
if len(url_of(fields)) > LIMIT:
    text = fields[i][1]
    while len(text) > 20 and len(url_of(fields[:i] + [(fields[i][0], text + "...")] + fields[i + 1:])) > LIMIT:
        text = text[:max(20, len(text) - max(1, len(text) // 10))].rstrip()
    fields[i] = (fields[i][0], text + "...")
    notes.append("Your answer about what you corrected was shortened to fit in one link.")

out = os.environ["GALLERY_OUT"]
for fname, text in (("title", title), ("body", body_of(fields)), ("url", url_of(fields)),
                    ("notes", "".join(n + "\n" for n in notes))):
    with open(os.path.join(out, fname), "w", encoding="utf-8") as f:
        f.write(text)
PY

echo
hr; echo " This is exactly what will be public"; hr
echo "Title: $(cat "$TMP/title")"
echo
sed 's/^/  /' "$TMP/body"
hr
if [ -s "$TMP/notes" ]; then cat "$TMP/notes"; fi
echo "It becomes a public GitHub issue on $REPO, under your GitHub account."
ask GO "Continue? (y/N): "
case "$GO" in [Yy]*) ;; *) cancelled ;; esac

URL="$(cat "$TMP/url")"
echo
echo "Your card's link:"
echo
echo "$URL"
echo
if [ -n "${BROWSER:-}" ]; then
  nohup "$BROWSER" "$URL" >/dev/null 2>&1 </dev/null &
  echo "It should open in a new browser tab. If it does not, Cmd-click the link above (Ctrl-click on Windows)."
else
  echo "Cmd-click the link above to open it (Ctrl-click on Windows)."
fi
echo "Click Submit new issue on that page to post your card."
