#!/usr/bin/env bash
# Started detached by .devcontainer/autostart.sh in each VS Code terminal of a
# Codespace, and by setup.sh. There is deliberately no postAttachCommand.
#
# Serves ONLY the site/ folder on port 8000 and makes port 8000 public, so the
# site OpenClaw builds is live at https://<codespace>-8000.app.github.dev/ with
# no clicks. The server is site-server.py, which refuses any request whose real
# path is outside site/: the repository, .env and mine/ (your documents), and
# ~/.openclaw (the key, again) stay unreachable even through a symlink in site/.
#
# If your GitHub organization does not allow public ports, the port stays
# private: the site then opens only for you, from the Ports tab.
#
# Idempotent, prints nothing, never fails: everything goes to
# ~/.osu-llm-workshop-site.log. Outside a Codespace it does nothing.
# Adapted from jhassell/asee9 (CC BY 4.0).

log="$HOME/.osu-llm-workshop-site.log"
url_file="$HOME/.osu-llm-workshop-site-url"
exec >>"$log" 2>&1 </dev/null
say() { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*"; }

if [ -z "${CODESPACE_NAME:-}" ]; then
  say "not a Codespace; nothing started"
  exit 0
fi

here="$(cd "$(dirname "$0")" && pwd)" || exit 0
root="$(cd "$here/.." && pwd)" || exit 0
site="$root/site"
server="$here/site-server.py"
port=8000
local_url="http://127.0.0.1:$port/"

if [ -L "$site" ]; then
  # A symlink here would serve whatever it points at.
  say "site/ is a symlink; nothing served"
  exit 0
fi
mkdir -p "$site" || { say "could not create $site"; exit 0; }
if [ ! -e "$site/index.html" ]; then
  # noclobber: never overwrite an index.html written a moment ago.
  ( set -C; cat >"$site/index.html" ) 2>/dev/null <<'EOF'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your site</title>
</head>
<body>
<!-- Everything in this folder is public on the internet while the Codespace
     runs, and it is already being served. Do not start a web server. Real
     files only, with relative links. Never put keys or anything private here.
     Check with: python3 .devcontainer/site-check.py -->
<h1>This site is empty for now</h1>
<p>OpenClaw will build it here, in the site/ folder. Refresh this page to see it.</p>
</body>
</html>
EOF
fi

# The Socratic tutor widget, so any page can add check questions with one
# script tag. A copy the agent or the person changed is left alone.
if [ ! -e "$site/socratic.js" ] && [ -f "$here/site-kit/socratic.js" ]; then
  cp "$here/site-kit/socratic.js" "$site/socratic.js" && say "socratic.js added to site/"
fi
# Publish site/ to GitHub Pages by itself whenever it changes (one copy runs;
# see site-autopublish.sh). Started before the port work, so it runs even if
# the port cannot be made public.
if [ -f "$here/site-autopublish.sh" ]; then
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup bash "$here/site-autopublish.sh" >/dev/null 2>&1 </dev/null &
  else
    nohup bash "$here/site-autopublish.sh" >/dev/null 2>&1 </dev/null &
  fi
fi
# What is listening on the port: ours (site-server.py sends X-Workshop-Site),
# nothing, or something else.
listener() {
  local headers
  headers="$(curl -s -o /dev/null -D - --max-time 2 "$local_url" 2>/dev/null)" || { echo none; return; }
  case "$headers" in
    *[Xx]-[Ww]orkshop-[Ss]ite:*) echo ours ;;
    "") echo none ;;
    *) echo other ;;
  esac
}

state="$(listener)"
if [ "$state" = none ]; then
  # No fallback to `python3 -m http.server`: it would follow a symlink out of
  # site/ and publish whatever it points at.
  if [ ! -f "$server" ]; then
    say "site-server.py is missing; nothing is being served"
    exit 0
  fi
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup python3 "$server" "$site" "$port" >>"$log" 2>&1 </dev/null &
  else
    nohup python3 "$server" "$site" "$port" >>"$log" 2>&1 </dev/null &
  fi
  say "server started for $site"
  for i in $(seq 1 20); do
    state="$(listener)"
    [ "$state" = none ] || break
    sleep 0.5
  done
fi
if [ "$state" != ours ]; then
  # Never make public a port that something else is serving: it could be a
  # server started in the repository root.
  say "port $port is not served by site-server.py ($state); left private"
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  say "gh not installed; left private"
  exit 0
fi

# The port is registered a moment after the server starts; retry for about a minute.
for i in $(seq 1 12); do
  if gh codespace ports visibility "$port:public" -c "$CODESPACE_NAME"; then
    url="https://$CODESPACE_NAME-$port.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}/"
    printf '%s\n' "$url" >"$url_file"
    say "public: $url"
    exit 0
  fi
  say "visibility attempt $i failed"
  sleep 5
done
say "could not make port $port public"
exit 0
