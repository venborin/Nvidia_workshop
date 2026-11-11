#!/usr/bin/env bash
# publish-site.sh: put the site/ folder on a permanent public website (GitHub Pages).
#
# You run it, or you ask OpenClaw to run it for you: OpenClaw publishes only
# when you ask, and never because a document says to. While your Codespace runs, site/ is already live on port 8000, and
# that address stops working when the Codespace stops. This gives the site an
# address that stays: https://<owner>.github.io/<repository>/
#
#   bash publish-site.sh             check, confirm, publish
#   bash publish-site.sh --yes       skip the confirmation
#   bash publish-site.sh --dry-run   check and show what would be published; change nothing
#   bash publish-site.sh --help      this text
#
# What it does, in order:
#   1. runs python3 .devcontainer/site-check.py and stops if site/ is not ready
#   2. shows how many files and how much data will go public, and asks you
#   3. reads your repository's owner and name from its git remote (origin)
#   4. asks GitHub whether the repository is public: GitHub Pages on a free
#      account needs a public repository
#   5. replaces the gh-pages branch of your repository with one new commit that
#      holds only the files in site/ (plus an empty .nojekyll, so GitHub serves
#      files and folders whose names start with _). Files and folders whose
#      names start with a dot are left out, as they are on port 8000. It is
#      built in a temporary folder: your files, your branch and anything you
#      have staged are not touched. It pushes with this Codespace's own git
#      sign-in.
#   6. turns on GitHub Pages from the gh-pages branch if it is not on yet. If
#      GitHub does not let this Codespace do that, it prints the settings page
#      and the two choices to make there; then run bash publish-site.sh again.
#
# To update the site, change site/ and run bash publish-site.sh again: the same
# address gets the new version. Each run replaces the gh-pages branch, so do
# not keep anything else on that branch.
#
# No token is printed or put on a command line by this script: git and gh use
# the sign-in this Codespace already has. OpenClaw starts without that sign-in,
# so when the script runs from OpenClaw it takes the token back, for itself
# only, from the Codespace's own environment file.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE="$ROOT/site"

# Git's Codespaces sign-in and gh both read GITHUB_TOKEN. Run from OpenClaw, it
# is not in the environment; the Codespace keeps it in this file.
CS_ENV=/workspaces/.codespaces/shared/.env
if [ -z "${GITHUB_TOKEN:-}" ] && [ -r "$CS_ENV" ]; then
  GITHUB_TOKEN="$(sed -n 's/^GITHUB_TOKEN=//p' "$CS_ENV" | tail -1 | tr -d "\"'\r")"
  if [ -n "$GITHUB_TOKEN" ]; then export GITHUB_TOKEN; else unset GITHUB_TOKEN; fi
fi
CHECK="$ROOT/.devcontainer/site-check.py"
BRANCH="gh-pages"
TMP=""

ASSUME_YES=0
DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y)  ASSUME_YES=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,36p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1   (try: bash publish-site.sh --help)"; exit 2 ;;
  esac
  shift
done

on_exit() { if [ -n "$TMP" ]; then rm -rf "$TMP"; fi; }
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

die() {   # $1 = what went wrong, $2 = what to do
  echo
  echo "❌ $1"
  [ -z "${2:-}" ] || echo "   $2"
  exit 1
}

have_tty() { { : </dev/tty; } 2>/dev/null; }

# One line of an error message from git or gh, safe to show: any user:password@
# part of an address is cut out, and it is kept short.
tidy() { tr -d '\r' | grep -v '^[[:space:]]*$' | tail -1 | sed -E 's#//[^/@[:space:]]*@#//#g; s/^gh: //' | cut -c1-200; }
# The same for git, which puts the useful line (fatal:, error:, remote:) first.
git_tidy() {
  local all line
  all="$(tr -d '\r')"
  line="$(printf '%s\n' "$all" | grep -E '^(fatal|error|remote|ERROR):' | head -1)"
  printf '%s\n' "${line:-$all}" | tidy
}

# ------------------------------------------------------------ 1. check site/
[ -d "$SITE" ] || die "There is no site/ folder yet." \
  "Ask OpenClaw to build your website in site/, then run bash publish-site.sh again."
[ -n "$(find "$SITE" -type f 2>/dev/null | head -1)" ] || die "site/ is empty." \
  "Ask OpenClaw to build your website in site/, then run bash publish-site.sh again."
[ -f "$CHECK" ] || die "The site check (.devcontainer/site-check.py) is missing, so nothing was published." \
  "Copy .devcontainer/site-check.py again from the workshop template (github.com/jhassell/osu-llm-workshop), or ask the instructor."

echo "Checking site/ before it goes public..."
# The check reads only files; it gets no GitHub sign-in in its environment.
env -u GITHUB_TOKEN -u GH_TOKEN python3 "$CHECK" "$SITE" \
  || die "site/ did not pass the check, so nothing was published." \
         "Fix the problems listed above (or ask OpenClaw to), then run bash publish-site.sh again."

TMP="$(mktemp -d)" || die "Could not make a temporary folder." ""

# site_files summary | list | copy <dest>: one walk of site/, regular files only.
# Symlinks (site-check already refuses them) and every file or folder whose name
# starts with a dot (.git, .env, notes) are skipped. site-server.py refuses the
# same names, so the published site holds exactly what port 8000 showed.
site_files() {
  python3 - "$SITE" "$@" <<'PYEOF'
import os, shutil, sys
site, mode = sys.argv[1], sys.argv[2]
files, skipped = [], 0
for d, dirs, names in os.walk(site, followlinks=False):
    for n in list(dirs):
        if n.startswith(".") or os.path.islink(os.path.join(d, n)):
            dirs.remove(n); skipped += 1
    for n in names:
        p = os.path.join(d, n)
        if n.startswith(".") or os.path.islink(p) or not os.path.isfile(p):
            skipped += 1; continue
        files.append(p)
files.sort()
rel = [os.path.relpath(p, site).replace(os.sep, "/") for p in files]
if mode == "summary":
    size = sum(os.path.getsize(p) for p in files)
    for unit in ("bytes", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            break
        size /= 1024.0
    shown = ("%d %s" % (size, unit)) if unit == "bytes" else ("%.1f %s" % (size, unit))
    print("%d file(s), %s" % (len(files), shown))
    if skipped:
        print("SKIPPED %d hidden file(s) or folder(s) (names starting with a dot), symlink(s) or special file(s)" % skipped)
elif mode == "list":
    for r in rel:
        print(r)
else:
    dest = sys.argv[3]
    for p, r in zip(files, rel):
        out = os.path.join(dest, *r.split("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(p, out)
    open(os.path.join(dest, ".nojekyll"), "a").close()
PYEOF
}

SUMMARY="$(site_files summary)" || die "Could not read site/." ""
COUNT_LINE="$(printf '%s\n' "$SUMMARY" | head -1)"

# ------------------------------------------------------------ 3. which repository
# The owner and name come from origin's address as written in .git/config.
# Codespaces writes https://github.com/OWNER/REPO; the ssh forms work too.
RAW_URL="$(git -C "$ROOT" config --get remote.origin.url 2>/dev/null)"
[ -n "$RAW_URL" ] || die "This folder has no git remote called origin, so there is nowhere to publish." \
  "Run this in your Codespace, in the copy of the workshop repository you made from the template."
U="${RAW_URL%/}"; U="${U%.git}"
OWNER=""; REPO=""
if [[ "$U" =~ ^(https?|ssh|git)://([^@/]*@)?[Gg][Ii][Tt][Hh][Uu][Bb]\.[Cc][Oo][Mm](:[0-9]+)?/([^/]+)/([^/]+)$ ]]; then
  OWNER="${BASH_REMATCH[4]}"; REPO="${BASH_REMATCH[5]}"
elif [[ "$U" =~ ^([^@/:]+@)?[Gg][Ii][Tt][Hh][Uu][Bb]\.[Cc][Oo][Mm]:/?([^/]+)/([^/]+)$ ]]; then
  OWNER="${BASH_REMATCH[2]}"; REPO="${BASH_REMATCH[3]}"
fi
U=""; RAW_URL=""
if ! [[ "$OWNER" =~ ^[A-Za-z0-9-]+$ ]] || ! [[ "$REPO" =~ ^[A-Za-z0-9._-]+$ ]]; then
  die "This repository's git remote (origin) is not a GitHub repository, so it cannot use GitHub Pages." \
      "Run this in your Codespace, in the copy of the workshop repository you made from the template."
fi
# Where git itself would push origin (it may rewrite the address). Handed to
# git only through its environment; never printed or put on a command line.
PUSH_URL="$(git -C "$ROOT" remote get-url --push origin 2>/dev/null)"
[ -n "$PUSH_URL" ] || die "Could not read where origin pushes to." ""

OWNER_LC="$(printf '%s' "$OWNER" | tr '[:upper:]' '[:lower:]')"
REPO_LC="$(printf '%s' "$REPO" | tr '[:upper:]' '[:lower:]')"
if [ "$REPO_LC" = "$OWNER_LC.github.io" ]; then
  ADDRESS="https://$OWNER_LC.github.io/"
else
  ADDRESS="https://$OWNER_LC.github.io/$REPO/"
fi

# ------------------------------------------------------------ 2. show and confirm
echo
echo "About to publish site/: $COUNT_LINE, plus an empty .nojekyll file."
if printf '%s\n' "$SUMMARY" | grep -q '^SKIPPED'; then
  echo "   $(printf '%s\n' "$SUMMARY" | sed -n 's/^SKIPPED \(.*\)/\1 will NOT be published./p')"
fi
echo "   Repository: $OWNER/$REPO, branch $BRANCH (replaced each time)"
echo "   Address:    $ADDRESS"

if [ "$DRY_RUN" -eq 1 ]; then
  echo
  echo "Dry run: these files would be published:"
  site_files list | head -40 | sed 's/^/     /'
  N="$(site_files list | wc -l | tr -d ' ')"
  [ "$N" -le 40 ] || echo "     ... and $((N - 40)) more"
  echo "     .nojekyll"
  echo
  echo "A real run would then:"
  echo "  1. ask GitHub whether $OWNER/$REPO is public (GitHub Pages on a free account needs that)"
  echo "  2. replace the $BRANCH branch of $OWNER/$REPO with one new commit holding only these files"
  echo "  3. turn on GitHub Pages from the $BRANCH branch, if it is not on already"
  echo
  echo "Nothing was sent to GitHub and nothing was changed."
  exit 0
fi

CONFIRM_TEXT="Publish site/ to a permanent public website at $ADDRESS? Anyone with the link can see it. [y/N]"
if [ "$ASSUME_YES" -eq 1 ]; then
  echo "$CONFIRM_TEXT yes (--yes)"
else
  have_tty || die "No terminal to confirm in." "Run bash publish-site.sh in a terminal, or add --yes."
  printf '%s ' "$CONFIRM_TEXT"
  ANSWER=""
  IFS= read -r ANSWER </dev/tty || true
  ANSWER="$(printf '%s' "$ANSWER" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  case "$ANSWER" in
    y|yes) ;;
    *) echo "Not published. Nothing was sent."; exit 0 ;;
  esac
fi

# ------------------------------------------------------------ talking to GitHub
command -v gh >/dev/null 2>&1 || die "The GitHub command-line tool (gh) is not installed here, so nothing was published." \
  "Run bash publish-site.sh in your Codespace, where gh is already installed and signed in."

# gh_call OUTFILE gh-api-arguments...: runs gh api, sets HTTP to the status
# GitHub gave (200 on success, "auth" when gh is not signed in, 000 when there
# was no answer at all) and ERR to the first line of gh's own message.
gh_call() {
  local out="$1" rc; shift
  if gh api "$@" >"$out" 2>"$TMP/gh.err"; then
    HTTP=200; ERR=""
    return 0
  else
    rc=$?
  fi
  HTTP="$(grep -o 'HTTP [0-9][0-9][0-9]' "$TMP/gh.err" | tail -1 | cut -c6-8)"
  if [ -z "$HTTP" ]; then
    # gh exits 4 and asks for "gh auth login" when it has no sign-in at all.
    if [ "$rc" -eq 4 ] || grep -q 'gh auth login' "$TMP/gh.err"; then HTTP="auth"; else HTTP="000"; fi
  fi
  ERR="$(tr -d '\r' <"$TMP/gh.err" | grep -v '^[[:space:]]*$' | head -1 | tidy)"
  return 1
}

gh_fail() {   # $1 = what we were doing
  [ -z "$ERR" ] || echo "   gh says: $ERR"
  case "$HTTP" in
    401|auth)
         die "gh is not signed in to GitHub while $1. Nothing was published." \
             "In a Codespace, open a new terminal (or restart the Codespace) and run bash publish-site.sh there. Elsewhere, run: gh auth login" ;;
    403) die "GitHub refused (HTTP 403) while $1. Nothing was published." \
             "Check that you are signed in as the owner of $OWNER/$REPO, or wait a minute and run bash publish-site.sh again." ;;
    404) die "GitHub cannot find $OWNER/$REPO for this sign-in (HTTP 404). Nothing was published." \
             "Check that this Codespace was made from your own copy of the workshop repository." ;;
    000) die "Could not reach GitHub while $1. Nothing was published." \
             "Check the connection, then run bash publish-site.sh again." ;;
    *)   die "Unexpected answer from GitHub (HTTP $HTTP) while $1. Nothing was published." \
             "Wait a minute, then run bash publish-site.sh again." ;;
  esac
}

# ------------------------------------------------------------ 4. public or private
echo "Asking GitHub whether $OWNER/$REPO is public..."
gh_call "$TMP/repo.txt" "repos/$OWNER/$REPO" --jq '.private' || gh_fail "looking up the repository"
case "$(tr -d '[:space:]' <"$TMP/repo.txt")" in
  false) ;;
  true)
    echo
    echo "❌ $OWNER/$REPO is a private repository, so nothing was published."
    echo "   GitHub Pages on a free account works only for a public repository. Two choices:"
    echo "   - Make the repository public: https://github.com/$OWNER/$REPO/settings"
    echo "     (at the bottom: Danger Zone, Change visibility), then run bash publish-site.sh again."
    echo "     Everything committed in it becomes public, not just site/. Your .env, mine/ and"
    echo "     site/ are never committed, so they stay in your Codespace."
    echo "   - Or keep it private and share the live Codespace address (the Ports tab, port 8000),"
    echo "     which works while your Codespace runs."
    exit 1 ;;
  *) die "GitHub's answer about $OWNER/$REPO did not say public or private. Nothing was published." \
         "Wait a minute, then run bash publish-site.sh again." ;;
esac

# ------------------------------------------------------------ 5. build and push gh-pages
# A throwaway repository in $TMP holds one commit with no parent: only site/.
# Your repository's files, branch and staged changes are never touched.
WORK="$TMP/pages"
mkdir -p "$WORK" && site_files copy "$WORK" 2>"$TMP/copy.err" \
  || die "Could not copy site/ for publishing." "Details: $(tidy <"$TMP/copy.err")"

NAME="$(git -C "$ROOT" config --get user.name 2>/dev/null)"
EMAIL="$(git -C "$ROOT" config --get user.email 2>/dev/null)"
[ -n "$NAME" ] || NAME="$OWNER"
[ -n "$EMAIL" ] || EMAIL="$OWNER@users.noreply.github.com"

# Settings that would change what is published or stop to ask something are
# turned off for this one repository: ignore files (yours or ones inside site/),
# hooks, commit signing, line-ending conversion.
g() {
  git -C "$WORK" -c core.hooksPath=/dev/null -c core.excludesFile=/dev/null \
      -c commit.gpgsign=false -c core.autocrlf=false -c core.safecrlf=false \
      -c user.name="$NAME" -c user.email="$EMAIL" "$@"
}
{ g init -q \
  && g add -A -f . \
  && g commit -q --no-verify -m "Publish site/ with publish-site.sh"; } >"$TMP/git.err" 2>&1 \
  || die "Could not prepare the $BRANCH commit. Nothing was published." "Details: $(git_tidy <"$TMP/git.err")"
PUBLISHED="$(g ls-files | wc -l | tr -d ' ')"

echo "Pushing site/ to the $BRANCH branch of $OWNER/$REPO..."
# The address goes to git through its environment as a remote named pub, not
# on the command line, where ps would show any sign-in written into it.
if ! GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never \
     GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.pub.url GIT_CONFIG_VALUE_0="$PUSH_URL" \
     g push --force --quiet --no-verify pub "HEAD:refs/heads/$BRANCH" </dev/null >"$TMP/push.err" 2>&1; then
  echo "   git says: $(git_tidy <"$TMP/push.err")"
  die "The push to GitHub failed, so nothing was published. Your files and branch are unchanged." \
      "Check the connection and that this Codespace can push to $OWNER/$REPO (try: git push), then run bash publish-site.sh again."
fi
echo "✅ Pushed $PUBLISHED file(s) to $BRANCH."

# ------------------------------------------------------------ 6. GitHub Pages on
SETTINGS="https://github.com/$OWNER/$REPO/settings/pages"
# The request body goes in a file: gh_call must not run in a pipeline, or the
# status it sets would be lost in a subshell.
printf '%s' '{"build_type":"legacy","source":{"branch":"gh-pages","path":"/"}}' >"$TMP/pages.json"
PAGES_OK=0
REASON=""

# What Pages does now: off, on from gh-pages, or on from something else.
if gh_call "$TMP/pages.txt" "repos/$OWNER/$REPO/pages" \
     --jq '[(.build_type // "-"), (.source.branch // "-"), (.source.path // "-"), (.html_url // "-")] | @tsv'; then
  IFS=$'\t' read -r P_TYPE P_BRANCH P_PATH P_URL <"$TMP/pages.txt" || true
  # Every field is "-" when GitHub left it out, so an empty one cannot shift the rest.
  if [ "${P_TYPE:--}" != "workflow" ] && [ "${P_BRANCH:--}" = "$BRANCH" ] && [ "${P_PATH:--}" = "/" ]; then
    PAGES_OK=1
  elif gh_call "$TMP/put.txt" -X PUT "repos/$OWNER/$REPO/pages" --input "$TMP/pages.json"; then
    PAGES_OK=1
  else
    REASON="GitHub Pages is on for $OWNER/$REPO, but it publishes something other than the $BRANCH branch."
  fi
  case "${P_URL:--}" in https://*) ADDRESS="$P_URL" ;; esac
else
  # Not on yet (404), or this sign-in may not look: try once to turn it on.
  if gh_call "$TMP/post.txt" -X POST "repos/$OWNER/$REPO/pages" --jq '.html_url // ""' --input "$TMP/pages.json"; then
    PAGES_OK=1
    P_URL="$(tr -d '[:space:]' <"$TMP/post.txt")"
    case "$P_URL" in https://*) ADDRESS="$P_URL" ;; esac
  elif [ "$HTTP" = "409" ]; then
    PAGES_OK=1        # already on
  else
    # GitHub may turn Pages on by itself once a gh-pages branch exists. Look
    # again a few times before asking for the one-time click.
    for wait in 5 10 15; do
      sleep "$wait"
      if gh_call "$TMP/pages.txt" "repos/$OWNER/$REPO/pages" \
           --jq '[.build_type // "", .source.branch // "", .source.path // "", .html_url // ""] | @tsv'; then
        IFS=$'\t' read -r P_TYPE P_BRANCH P_PATH P_URL <"$TMP/pages.txt" || true
        if [ "$P_BRANCH" = "$BRANCH" ]; then
          PAGES_OK=1
          case "${P_URL:--}" in https://*) ADDRESS="$P_URL" ;; esac
          break
        fi
      fi
    done
  fi
  if [ "$PAGES_OK" -ne 1 ] && [ -z "${REASON:-}" ]; then
    case "$HTTP" in
      401|403|404|auth)
           REASON="This Codespace is not allowed to turn on GitHub Pages. That is normal; you do it once by hand." ;;
      000) REASON="GitHub could not be reached to turn on GitHub Pages. Run bash publish-site.sh again in a minute, or do it once by hand." ;;
      *)   REASON="GitHub did not turn on GitHub Pages (HTTP $HTTP). Run bash publish-site.sh again in a minute, or do it once by hand." ;;
    esac
  fi
fi
case "$ADDRESS" in */) ;; *) ADDRESS="$ADDRESS/" ;; esac

if [ "$PAGES_OK" -ne 1 ]; then
  echo
  echo "=============================================="
  echo "  ONE STEP LEFT. site/ is on the $BRANCH branch, but not on the web yet."
  echo
  echo "  $REASON"
  echo "  Open:  $SETTINGS"
  echo "  Under Build and deployment choose:"
  echo "    Source:  Deploy from a branch"
  echo "    Branch:  gh-pages    folder:  / (root)    then Save"
  echo
  echo "  Then run bash publish-site.sh again."
  echo "=============================================="
  exit 1
fi

echo "=============================================="
echo "  PUBLISHED."
echo
echo "  Address:  $ADDRESS"
echo
echo "  The first time, GitHub takes a minute or two before the address works."
echo "  Anyone with the link can see it. To update it, change site/ and run"
echo "  bash publish-site.sh again: the same address gets the new version."
echo "=============================================="
