#!/usr/bin/env bash
# Runs as the devcontainer's onCreateCommand: once while the Codespace is
# created (or inside a Codespaces prebuild, if one is enabled).
#
# Deliberately NO blanket `set -e`: one failed install must not take the others
# down with it. Every step runs, reports, and leaves a log; setup.sh re-checks
# and repairs. This script never asks for or reads a key.
#
# Adapted from jhassell/asee9 (CC BY 4.0).

LOG=/tmp/osu-llm-workshop-postcreate.log
exec > >(tee -a "$LOG") 2>&1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing the Python libraries the labs use (pinned in requirements.txt)..."
if pip install --user --quiet -r "$ROOT/requirements.txt"; then
  echo "Python libraries installed."
else
  echo "Python libraries did not all install here; setup.sh will try again."
fi

# AUTOSTART. One guarded line in ~/.bashrc sources .devcontainer/autostart.sh,
# which starts setup.sh by itself in the first terminal you open. It does
# nothing here: there is no interactive VS Code terminal yet. Idempotent, and it
# never fails this script. setup.sh writes the identical line and tag.
install_autostart_line() {
  local hook rc="$HOME/.bashrc" tag="# osu-llm-workshop-autostart" line
  hook="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/autostart.sh"
  [ -f "$hook" ] || echo "WARNING: $hook is missing; setup will NOT start by itself. Is it committed?"
  line="$(printf 'if [ -f %q ]; then . %q; fi  %s' "$hook" "$hook" "$tag")"
  touch "$rc" 2>/dev/null || return 0
  grep -qxF "$line" "$rc" && return 0
  if grep -qF "$tag" "$rc"; then
    grep -vF "$tag" "$rc" >"$rc.ac.$$" && cat "$rc.ac.$$" >"$rc"
    rm -f "$rc.ac.$$"
  fi
  printf '\n%s\n' "$line" >>"$rc"
}
if install_autostart_line; then
  echo "Autostart line present in ~/.bashrc."
else
  echo "Could not add the autostart line to ~/.bashrc (setup.sh will add it)."
fi

# GATE. A prebuild must not be marked ready without the libraries in it. Check
# the real thing, not a log line, and fail the lifecycle command if anything is
# missing. (Without a prebuild, a failure here is repaired by setup.sh.)
if MPLBACKEND=Agg python3 -c 'import openai, pydantic, pypdf, docx, pandas, matplotlib.pyplot, scipy, statsmodels.api, seaborn' 2>/dev/null; then
  echo "GATE PASSED: the workshop libraries import (openai, pydantic, pypdf, python-docx, the data stack)."
else
  echo "GATE FAILED: a Python library does not import. In the Codespace, bash setup.sh repairs it."
  exit 1
fi
# OpenClaw comes in the image. Report it, but do not fail on it: nothing in the
# labs needs it, and setup.sh --openclaw installs it if it is ever missing.
if openclaw --version 2>/dev/null | grep -qF "2026.9.2"; then
  echo "OpenClaw 2026.9.2 present."
else
  echo "NOTE: OpenClaw 2026.9.2 is not in this container; bash setup.sh --openclaw will install it."
fi

echo ""
echo "=============================================="
echo " Container ready."
echo " Next step: open a terminal. Setup starts by itself and asks for the"
echo " workshop key (or uses your Codespaces secret LLM_API_KEY)."
echo " If it only shows a line ending in \$, type:  bash setup.sh"
echo "=============================================="
