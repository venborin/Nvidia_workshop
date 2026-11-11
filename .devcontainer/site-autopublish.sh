#!/usr/bin/env bash
# Publishes site/ to GitHub Pages by itself whenever it changes, so a site
# OpenClaw builds reaches its permanent public address with no further request.
#
# Started detached by .devcontainer/site-public.sh (which autostart.sh and
# setup.sh start). One copy runs per Codespace. Every few seconds it looks at
# site/. When the files have changed since the last publish, have stopped
# changing for about a minute (QUIET_CHECKS x 5 s), and are no longer the
# placeholder page, it runs bash publish-site.sh --yes, which checks the site
# first. A minute of quiet usually means the agent has finished, but a slow
# model can leave a minute between two of its steps, so a half-built site can
# be published; the next change is published the same way and replaces it. A failed check
# or a refused publish is tried again when site/ changes, or after five minutes.
#
# The result of the last attempt is in ~/.osu-llm-workshop-pages-status, the
# details in ~/.osu-llm-workshop-site.log. To stop publishing automatically:
#   touch ~/.osu-llm-workshop-no-autopublish
# Prints nothing and never fails. Outside a Codespace it does nothing.
log="$HOME/.osu-llm-workshop-site.log"
status_file="$HOME/.osu-llm-workshop-pages-status"
lock="$HOME/.osu-llm-workshop-autopublish.lock"
off="$HOME/.osu-llm-workshop-no-autopublish"
exec >>"$log" 2>&1 </dev/null
say() { printf '%s autopublish: %s\n' "$(date -u +%H:%M:%S)" "$*"; }
[ -n "${CODESPACE_NAME:-}" ] || exit 0

here="$(cd "$(dirname "$0")" && pwd)" || exit 0
root="$(cd "$here/.." && pwd)" || exit 0
site="$root/site"
publish="$root/publish-site.sh"
[ -f "$publish" ] || { say "publish-site.sh missing; not running"; exit 0; }

# One copy only: a lock directory holding the PID of the copy that runs.
if ! mkdir "$lock" 2>/dev/null; then
  pid="$(cat "$lock/pid" 2>/dev/null)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then exit 0; fi
  rm -rf "$lock"; mkdir "$lock" 2>/dev/null || exit 0
fi
echo $$ >"$lock/pid"
trap 'rm -rf "$lock"' EXIT
say "watching $site"

fingerprint() {   # changes whenever any file in site/ is added, removed or changed
  [ -d "$site" ] || { echo none; return; }
  python3 - "$site" <<'PYEOF' 2>/dev/null || echo none
import hashlib, os, sys
top = sys.argv[1]
h = hashlib.sha256()
for d, dirs, files in os.walk(top):
    dirs[:] = sorted(x for x in dirs if not x.startswith("."))
    for f in sorted(files):
        if f.startswith("."):
            continue
        p = os.path.join(d, f)
        st = os.lstat(p)
        h.update(f"{os.path.relpath(p, top)} {st.st_size} {st.st_mtime_ns}\n".encode())
print(h.hexdigest())
PYEOF
}
is_placeholder() {
  grep -q 'This site is empty for now' "$site/index.html" 2>/dev/null
}

QUIET_CHECKS=12   # 12 checks 5 seconds apart: about a minute without changes
done_fp=""        # what was last attempted
done_at=0
last_fp=""
same=0
while :; do
  sleep 5
  [ -e "$off" ] && continue
  fp="$(fingerprint)"
  if [ "$fp" = "$last_fp" ]; then same=$((same + 1)); else same=0; last_fp="$fp"; fi
  [ "$same" -ge "$QUIET_CHECKS" ] || continue         # unchanged for about a minute
  [ "$fp" != none ] && [ -f "$site/index.html" ] || continue
  is_placeholder && continue
  now="$(date +%s)"
  if [ "$fp" = "$done_fp" ]; then
    # Already published, or tried: try again only if that try failed and five minutes have passed.
    [ "$(head -1 "$status_file" 2>/dev/null)" != PUBLISHED ] && [ $((now - done_at)) -ge 300 ] || continue
  fi
  done_fp="$fp"; done_at="$now"
  say "site/ changed; publishing"
  out="$(bash "$publish" --yes 2>&1)"; rc=$?
  printf '%s\n' "$out" | tail -15
  if [ "$rc" -eq 0 ]; then
    addr="$(printf '%s\n' "$out" | sed -n 's/^ *Address: *//p' | tail -1)"
    printf 'PUBLISHED\n%s\n' "$addr" >"$status_file"
    say "published: $addr"
  elif printf '%s' "$out" | grep -q 'ONE STEP LEFT'; then
    link="$(printf '%s\n' "$out" | sed -n 's/^ *Open: *//p' | tail -1)"
    printf 'ONE STEP LEFT\n%s\n' "$link" >"$status_file"
    say "needs the one-time Pages setting: $link"
  else
    printf 'NOT PUBLISHED\nsee ~/.osu-llm-workshop-site.log\n' >"$status_file"
    say "publish failed (exit $rc)"
  fi
done
