#!/usr/bin/env bash
# Pick which OpenRouter model the labs and OpenClaw use.
#
#   bash 00_setup/choose_model.sh            show the list and ask (Enter: Nemotron)
#   bash 00_setup/choose_model.sh 3          pick number 3 without asking
#   bash 00_setup/choose_model.sh <id>       pick by OpenRouter id, if it is on the list
#   bash 00_setup/choose_model.sh --list     show the list and the current model, change nothing
#
# The list is 00_setup/models.txt: NVIDIA Nemotron first, then the most capable
# agentic models that stay under $3 a person for the whole day. The choice is
# checked with a one-token request, saved in .env as LLM_MODEL, and OpenClaw is
# reconnected to it. The labs read .env each time they run, so the next python
# command uses the new model; an OpenClaw chat that is already open keeps the
# old one until you close it (/exit) and type: openclaw chat
#
# Stop 4 reads images with its own model (Nemotron VL) whatever is chosen here.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"
LIST="$ROOT/00_setup/models.txt"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

env_value() { [ -f "$ENV_FILE" ] && sed -n "s/^$1=//p" "$ENV_FILE" | tail -1 | tr -d '[:space:]"'"'" || true; }

[ -f "$LIST" ] || { echo "The model list $LIST is missing. Restore it with:  git checkout HEAD -- 00_setup/models.txt   (or get the latest with:  git pull)"; exit 1; }
IDS=(); LABELS=()
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|'#'*) continue ;; esac
  IDS+=("${line%%|*}"); LABELS+=("${line#*|}")
done <"$LIST"
N=${#IDS[@]}
[ "$N" -gt 0 ] || { echo "The model list $LIST is empty."; exit 1; }

CURRENT="$(env_value LLM_MODEL)"
show_list() {
  local i mark
  for ((i = 0; i < N; i++)); do
    mark=""; [ "${IDS[$i]}" = "$CURRENT" ] && mark="   (current)"
    printf '  %d  %s\n     %s%s\n' "$((i + 1))" "${LABELS[$i]}" "${IDS[$i]}" "$mark"
  done
}

if [ "${1:-}" = --list ]; then
  echo "Models on the list (OpenRouter):"
  show_list
  exit 0
fi
case "${1:-}" in -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;; esac

# The list is OpenRouter's; on another endpoint (Cimarron, NVIDIA) it means nothing.
BASE="$(env_value LLM_BASE_URL)"; BASE="${BASE%/}"
if [ -z "$(env_value LLM_API_KEY)" ]; then
  echo "This Codespace is not connected to a model yet. First type:   bash setup.sh"
  exit 1
fi
if [ "$BASE" != "$OPENROUTER_BASE_URL" ]; then
  echo "You are on $BASE, not OpenRouter, so there is nothing to choose here."
  echo "To move back to OpenRouter first:   bash 00_setup/switch_backend.sh openrouter"
  exit 1
fi

pick="${1:-}"
if [ -z "$pick" ]; then
  echo "Which model? The labs and OpenClaw will both use it."
  show_list
  while :; do
    printf "Type a number, or press Enter for 1: "
    pick=""
    IFS= read -r pick </dev/tty || pick=""
    pick="${pick//[[:space:]]/}"
    [ -n "$pick" ] || pick=1
    if [[ "$pick" =~ ^[0-9]+$ ]] && [ "$pick" -ge 1 ] && [ "$pick" -le "$N" ]; then break; fi
    echo "That is not one of the numbers 1 to $N."
  done
fi

ID=""
if [[ "$pick" =~ ^[0-9]+$ ]]; then
  [ "$pick" -ge 1 ] && [ "$pick" -le "$N" ] && ID="${IDS[$((pick - 1))]}"
else
  for i in "${IDS[@]}"; do [ "$i" = "$pick" ] && ID="$i"; done
fi
if [ -z "$ID" ]; then
  echo "\"$pick\" is not on the list. The choices are:"
  show_list
  exit 2
fi
if [ "$ID" = "$CURRENT" ]; then
  echo "Already using $ID. Nothing changed."
  exit 0
fi

# setup.sh does the rest with the saved key: it asks the model for one token,
# writes .env only if that works, and reconnects OpenClaw without opening it.
echo "Switching to $ID..."
WORKSHOP_SWITCHING=1 exec bash "$ROOT/setup.sh" --model "$ID"
