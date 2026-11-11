#!/usr/bin/env bash
# Move every lab, and OpenClaw, to another model endpoint, between stops.
#
#   bash 00_setup/switch_backend.sh cimarron      OSU's Cimarron cluster (Nemotron on campus GPUs)
#   bash 00_setup/switch_backend.sh openrouter    back to the workshop's default
#   bash 00_setup/switch_backend.sh               say which one you are on now
#   bash 00_setup/switch_backend.sh https://host/v1 [model]   any other endpoint
#
# The first move to an endpoint asks for the workshop word. After that each
# endpoint's settings are kept in a file of their own (.env.cimarron,
# .env.openrouter, never committed), so moving back and forth asks for nothing.
# Cimarron's address comes from workshop-endpoint.txt, filled in by the
# instructor; if it is empty, the switch says so and changes nothing.
#
# The labs read .env each time they run, so the next python command already
# uses the new endpoint. OpenClaw is reconnected too, but a chat that is already
# open keeps the old endpoint until you close it (/exit) and type: openclaw chat
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
ENDPOINT_TXT_URL="https://raw.githubusercontent.com/jhassell/osu-llm-workshop/main/workshop-endpoint.txt"

env_value() { [ -f "$1" ] && sed -n "s/^$2=//p" "$1" | tail -1 | tr -d '[:space:]"'"'" || true; }

# Cimarron's address and model: this copy's workshop-endpoint.txt, or the
# instructor's current one online when this copy's is empty.
cimarron_endpoint() {
  local txt=""
  [ -f "$ROOT/workshop-endpoint.txt" ] && txt="$(cat "$ROOT/workshop-endpoint.txt")"
  if ! printf '%s\n' "$txt" | grep -q '^OSU_BASE_URL=https://'; then
    txt="$(curl -fsS -m 10 "$ENDPOINT_TXT_URL" 2>/dev/null)" || txt=""
  fi
  CIM_URL="$(printf '%s\n' "$txt" | sed -n 's/^OSU_BASE_URL=//p' | tail -1 | tr -d '[:space:]')"
  CIM_MODEL="$(printf '%s\n' "$txt" | sed -n 's/^OSU_MODEL=//p' | tail -1 | tr -d '[:space:]')"
  case "$CIM_URL" in https://*) CIM_URL="${CIM_URL%/}" ;; *) CIM_URL="" ;; esac
}

# Which named endpoint a .env points at: openrouter, cimarron or other.
backend_of() {
  local base; base="$(env_value "$1" LLM_BASE_URL)"; base="${base%/}"
  if [ -z "$base" ]; then echo none
  elif [ "$base" = "$OPENROUTER_BASE_URL" ]; then echo openrouter
  elif [ -n "$CIM_URL" ] && [ "$base" = "$CIM_URL" ]; then echo cimarron
  else echo other; fi
}

cimarron_endpoint
CURRENT="$(backend_of "$ENV_FILE")"
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
  case "$CURRENT" in
    none) echo "No endpoint yet. Run: bash setup.sh" ;;
    other) echo "Now on: $(env_value "$ENV_FILE" LLM_BASE_URL)  model $(env_value "$ENV_FILE" LLM_MODEL)" ;;
    *) echo "Now on: $CURRENT ($(env_value "$ENV_FILE" LLM_BASE_URL), model $(env_value "$ENV_FILE" LLM_MODEL))" ;;
  esac
  echo "To move: bash 00_setup/switch_backend.sh cimarron   or   bash 00_setup/switch_backend.sh openrouter"
  exit 0
fi

case "$TARGET" in
  http://*|https://*)   # any endpoint, as before: setup asks for its key
    if [ -n "${2:-}" ]; then exec bash "$ROOT/setup.sh" --reset-key --base-url "$TARGET" --model "$2"; fi
    exec bash "$ROOT/setup.sh" --reset-key --base-url "$TARGET" ;;
  cimarron|openrouter) ;;
  *) echo "usage: bash 00_setup/switch_backend.sh cimarron | openrouter | https://host/v1 [model]"; exit 2 ;;
esac

if [ "$TARGET" = cimarron ] && [ -z "$CIM_URL" ]; then
  echo "Cimarron is not connected for this workshop yet (no address in workshop-endpoint.txt)."
  echo "Nothing changed: you are still on ${CURRENT}."
  exit 1
fi
if [ "$TARGET" = "$CURRENT" ]; then
  echo "Already on $TARGET. Nothing changed."
  exit 0
fi

# Keep the settings of the endpoint being left, so coming back asks for nothing.
if [ "$CURRENT" = openrouter ] || [ "$CURRENT" = cimarron ]; then
  ( umask 077; cp -p "$ENV_FILE" "$ROOT/.env.$CURRENT" ) && chmod 600 "$ROOT/.env.$CURRENT"
fi

echo "Moving from $CURRENT to $TARGET..."
# The endpoint and model asked for are passed to setup explicitly, and any
# Codespaces secrets (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL) are left out of its
# environment, so neither a failed saved key nor a secret can land the switch
# anywhere but the target.
if [ "$TARGET" = openrouter ]; then
  T_URL="$OPENROUTER_BASE_URL"
  T_MODEL="$(sed -n '/^[^#[:space:]]/{s/|.*//p;q;}' "$ROOT/00_setup/models.txt" 2>/dev/null)"
else
  T_URL="$CIM_URL"; T_MODEL="$CIM_MODEL"
fi
SAVED="$ROOT/.env.$TARGET"
ARGS=(--base-url "$T_URL")
if [ -f "$SAVED" ] && [ -n "$(env_value "$SAVED" LLM_API_KEY)" ]; then
  # Settings kept from an earlier visit. setup checks the key still works; if it
  # does not, setup asks for the word again, for this same endpoint.
  ( umask 077; cp -p "$SAVED" "$ENV_FILE" ) && chmod 600 "$ENV_FILE"
  M="$(env_value "$SAVED" LLM_MODEL)"; M="${M:-$T_MODEL}"
  [ -z "$M" ] || ARGS+=(--model "$M")
else
  echo "Type the workshop word when asked."
  ARGS=(--reset-key "${ARGS[@]}")
  [ -z "$T_MODEL" ] || ARGS+=(--model "$T_MODEL")
fi
WORKSHOP_SWITCHING=1 exec env -u LLM_API_KEY -u LLM_BASE_URL -u LLM_MODEL bash "$ROOT/setup.sh" "${ARGS[@]}"
