#!/usr/bin/env bash
# osu-llm-workshop setup: connects this Codespace to the workshop model.
#
# In a new Codespace this starts BY ITSELF in the first terminal (see
# .devcontainer/autostart.sh) and keeps doing so in new terminals until it has
# succeeded once. If a terminal only shows a line ending in $, type:
#
#   bash setup.sh                   set up (or repair) the connection
#   bash setup.sh --reset-key       forget the saved key and ask for a new one
#   bash setup.sh --base-url URL    point the labs at a different endpoint
#   bash setup.sh --model NAME      pick a model by name
#   bash setup.sh --choose-model    with an OpenRouter key, pick from the list of models again
#                                   (or: bash 00_setup/choose_model.sh)
#   bash setup.sh --openclaw        connect OpenClaw to the same model and open it
#
# Everything the labs need is two values, written to .env in this folder:
#   LLM_BASE_URL   the endpoint, an OpenAI-compatible URL ending in /v1
#   LLM_API_KEY    the key for that endpoint
#   LLM_MODEL      optional; the model to use when the endpoint serves more than one
#
# The key decides the endpoint. Paste any of these at the prompt:
#   the OSU workshop key   (given on the day)     goes to the OSU workshop endpoint
#   an OpenRouter key      (starts with sk-or-)   goes to OpenRouter, and you pick
#                                                 a model from 00_setup/models.txt (Enter: Nemotron Ultra)
#   an NVIDIA key          (starts with nvapi-)   goes to NVIDIA's hosted endpoint
# A key is only ever sent to the endpoint it belongs to. --base-url, or a
# Codespaces secret LLM_BASE_URL, overrides this and uses that endpoint instead.
#
# Where each value comes from, first match wins:
#   1. a Codespaces secret of the same name (nothing to type)
#   2. the value saved by an earlier run, in .env (the key is skipped by --reset-key)
#   3. the terminal asks you for the workshop word or a key.
#      Press Enter without a key to finish the pre-work: the Codespace is ready
#      and the endpoint check waits for the key.
#
# After a key is accepted, setup connects OpenClaw, a complete agent program
# already installed in this Codespace, to the same endpoint and model as the
# labs, opens the first exercise's page in the editor, and opens OpenClaw's chat,
# where the first exercise builds a small tutorial website in site/. With no
# terminal attached it connects OpenClaw without opening it.
#
# In a Codespace, site/ is served on port 8000 and the port is made public
# (.devcontainer/site-public.sh); the READY box shows the address.
#
# Switches for test harnesses:
#   WORKSHOP_FORCE=1     run even though setup is already running in another terminal
#   WORKSHOP_NO_PROMPT=1 never ask anything (no key prompt; OpenClaw is connected, not opened)
#   WORKSHOP_NO_CHAT=1   with --openclaw, configure OpenClaw but do not open it
#   WORKSHOP_SWITCHING=1 set by 00_setup/switch_backend.sh: reconnect OpenClaw, open nothing
#
# Adapted from jhassell/asee9 (CC BY 4.0): the run-once lock, the key
# prompt (shown here, since what is typed is a word) and the key check are the same design; the provider is different.
set -uo pipefail

# The three endpoints a pasted key can belong to. The OSU one comes from
# workshop-endpoint.txt in this folder, which the instructor fills in when the
# workshop endpoint exists. A copy made from the template before that has an
# empty file, so setup then reads the current file from the instructor's public
# repository (a plain download; no key is sent). Until the address exists
# anywhere, a workshop key is refused with a plain message, never sent.
OSU_BASE_URL=""                                   # leave empty; set workshop-endpoint.txt instead
OSU_MODEL=""
OSU_KEY_URL=""                                    # where the workshop word is looked up; also from workshop-endpoint.txt
OSU_CONTEXT=""                                    # the OSU endpoint's context window, from workshop-endpoint.txt
OSU_LOADED=0
WORKSHOP_ENDPOINT_URL="https://raw.githubusercontent.com/jhassell/osu-llm-workshop/main/workshop-endpoint.txt"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
# The room's model, chosen 2026-11-06 as the most capable Nemotron: Ultra replayed
# every old module (7 of 7) and the website exercise for less than Super, because
# its providers bill the cached prompt OpenClaw resends at a fifth of the price.
OPENROUTER_MODEL="nvidia/nemotron-3-ultra-550b-a55b"
# The models offered when someone pastes an OpenRouter key, used only when
# 00_setup/models.txt is missing (that file is the list): id|what the person
# sees. The first is the default (Enter). Each was run through Module 3's
# extraction and Module 4's tool-calling agent on 2026-10-31 and passed both
# (Gemini 3.8 Flash replaced 3.7 Flash the same evening, after the same test).
# OpenRouter prices then, per million input/output tokens: Nemotron 0.30/2.40,
# Claude Haiku 5.5 0.10/0.50, GPT-6 Luna 0.10/0.50, Gemini 3.8 Flash 0.825/4.125,
# DeepSeek V4.1 Flash 0.045/0.50. Check https://openrouter.ai/models before a
# workshop: models are renamed and retired.
OPENROUTER_CHOICES=(
  "nvidia/nemotron-3-ultra-550b-a55b|NVIDIA Nemotron 3 Ultra: open model, the most capable Nemotron, the workshop's model"
  "nvidia/nemotron-3-super-120b-a12b|NVIDIA Nemotron 3 Super: open model, smaller and faster"
  "deepseek/deepseek-v4.1-flash|DeepSeek V4.1 Flash: open model, lowest cost, most consistent in testing"
  "anthropic/claude-haiku-5.5|Anthropic Claude Haiku 5.5: fast, low cost"
  "openai/gpt-6-luna|OpenAI GPT-6 Luna: fast, low cost"
  "google/gemini-3.8-flash|Google Gemini 3.8 Flash: fast, costs the most of these"
)
NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1"
# NVIDIA opens only some hosted models to a personal account: on 2026-10-28 a fresh
# account got 404 from nvidia/nemotron-3-super-120b-a12b and 200 from this one.
NVIDIA_MODEL="nvidia/nemotron-3-ultra-550b-a55b"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT/.env"
# The offered list lives in 00_setup/models.txt, shared with 00_setup/choose_model.sh;
# the array above is the fallback when that file is missing. Its first line must
# be the workshop model, since Enter picks it.
if [ -f "$ROOT/00_setup/models.txt" ]; then
  MODELS_FROM_FILE=()
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    MODELS_FROM_FILE+=("$line")
  done <"$ROOT/00_setup/models.txt"
  if [ ${#MODELS_FROM_FILE[@]} -gt 0 ] && [ "${MODELS_FROM_FILE[0]%%|*}" = "$OPENROUTER_MODEL" ]; then
    OPENROUTER_CHOICES=("${MODELS_FROM_FILE[@]}")
  fi
  unset MODELS_FROM_FILE line
fi

# Everything the exit trap touches is defined here, before anything can fail,
# so `set -u` can never trip inside the trap.
TMP=""
DOTS_PID=""
DOTS_MSG=""
READING=0
STOPPED=0                                     # 1 after Ctrl+C, a closed terminal, or a kill
READY_DONE=0                                  # 1 once READY is reached
LOCK="$HOME/.osu-llm-workshop-setup.lock"     # run-once lock shared with autostart.sh
MARKER="$HOME/.osu-llm-workshop-ready"        # written at READY; autostart.sh then stays quiet
SITE_URL_FILE="$HOME/.osu-llm-workshop-site-url"   # the public address of site/, from site-public.sh
AUTOSTART_TAG="# osu-llm-workshop-autostart"
# Anything this script starts must never re-trigger the autostart hook.
export WORKSHOP_NO_AUTOSTART=1

RESET_KEY=0
BASE_ARG=""
MODEL_ARG=""
OPENCLAW_ARG=0
CHOOSE_MODEL=0
KEY_FROM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --reset-key) RESET_KEY=1 ;;
    --base-url) shift; BASE_ARG="${1:-}" ;;
    --model) shift; MODEL_ARG="${1:-}" ;;
    --openclaw) OPENCLAW_ARG=1 ;;
    --choose-model) CHOOSE_MODEL=1 ;;
    -h|--help) sed -n '2,/^# Adapted from/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1   (try: bash setup.sh --help)"; exit 2 ;;
  esac
  shift
done

# The key lives in shell variables only. A Codespaces secret arrives exported;
# take it and un-export it at once, so no tool this script runs inherits it. It
# goes to curl through a config file on stdin, never on a command line.
SECRET_KEY="${LLM_API_KEY:-}"
SECRET_KEY="${SECRET_KEY//[[:space:]]/}"
unset LLM_API_KEY
SECRET_BASE="${LLM_BASE_URL:-}"
SECRET_BASE="${SECRET_BASE//[[:space:]]/}"
unset LLM_BASE_URL
SECRET_MODEL="${LLM_MODEL:-}"
SECRET_MODEL="${SECRET_MODEL//[[:space:]]/}"
unset LLM_MODEL
MODEL=""
KEY=""
BASE=""

hr() { echo "=============================================="; }

# ------------------------------------------------------------ moving dots
dots_tty() {
  [ -t 1 ] && { : >/dev/tty; } 2>/dev/null
}
dots_start() {   # $1 = message, without trailing dots
  dots_stop fail
  DOTS_MSG="$1"
  if dots_tty; then
    (
      while kill -0 $$ 2>/dev/null; do
        for d in "." ".." "..."; do
          printf '\r\033[K%s%s' "$DOTS_MSG" "$d" >/dev/tty 2>/dev/null || exit 0
          sleep 0.4
        done
      done
    ) &
    DOTS_PID=$!
  else
    echo "${DOTS_MSG}..."
  fi
}
dots_stop() {    # $1 = ok | fail
  [ -n "$DOTS_MSG" ] || return 0
  local mark="✅"
  [ "${1:-ok}" = "ok" ] || mark="❌"
  if [ -n "$DOTS_PID" ]; then
    kill "$DOTS_PID" 2>/dev/null
    wait "$DOTS_PID" 2>/dev/null
    DOTS_PID=""
    printf '\r\033[K' >/dev/tty 2>/dev/null
  fi
  echo "${DOTS_MSG}... ${mark}" 2>/dev/null
  DOTS_MSG=""
}

# ------------------------------------------------------ run-once lock
# autostart.sh takes the lock (a directory holding a PID) before it starts this
# script, so a second terminal stays quiet while setup runs. We own the lock if
# it names us, our parent (the terminal that autostart ran in), no one, or a
# process that no longer exists.
lock_owner() {
  local pid="" start=""
  { read -r pid; read -r start; } 2>/dev/null <"$LOCK/pid"
  printf '%s %s' "$pid" "$start"
}
proc_start() {
  ps -o lstart= -p "$1" 2>/dev/null | awk '{$1=$1; print}'
}
lock_write() {
  printf '%s\n%s\n' "$$" "$(proc_start $$)" >"$LOCK/pid" 2>/dev/null
}
mutex_take() {
  mkdir "$1" 2>/dev/null && return 0
  [ -n "$(find "$1" -maxdepth 0 -mmin +1 2>/dev/null)" ] || return 1
  mv "$1" "$1.old.$$" 2>/dev/null || return 1
  rm -rf "$1.old.$$"
  mkdir "$1" 2>/dev/null
}
lock_held_by_other() {
  local pid start now
  read -r pid start <<<"$(lock_owner)"
  if [ -z "$pid" ]; then
    [ -z "$(find "$LOCK" -maxdepth 0 -mmin +1 2>/dev/null)" ]
    return
  fi
  [ "$pid" != "$$" ] && [ "$pid" != "$PPID" ] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  now="$(proc_start "$pid")"
  [ -z "$start" ] || [ -z "$now" ] || [ "$start" = "$now" ]
}
lock_claim() {
  local pid start
  if mkdir "$LOCK" 2>/dev/null; then lock_write; return 0; fi
  read -r pid start <<<"$(lock_owner)"
  if [ -n "$pid" ] && { [ "$pid" = "$$" ] || [ "$pid" = "$PPID" ]; }; then
    lock_write; return 0
  fi
  if lock_held_by_other; then
    if [ -t 0 ] && [ -z "${WORKSHOP_FORCE:-}" ]; then
      echo
      echo "⚠️  Setup has already started in another terminal."
      echo "   Switch to it: the list of terminals at the right edge of this panel."
      echo "   Pick the first one. If it asks for your key, paste it there."
      exit 0
    fi
    return 0
  fi
  mutex_take "$LOCK.takeover" || return 0
  if lock_held_by_other; then rmdir "$LOCK.takeover" 2>/dev/null; return 0; fi
  rm -rf "$LOCK"
  if mkdir "$LOCK" 2>/dev/null; then lock_write; fi
  rmdir "$LOCK.takeover" 2>/dev/null
  return 0
}
lock_release() {
  [ -d "$LOCK" ] || return 0
  local pid start
  read -r pid start <<<"$(lock_owner)"
  if [ -z "$pid" ] || [ "$pid" = "$$" ]; then
    rm -rf "$LOCK"
  fi
}

# ------------------------------------------------ autostart line in ~/.bashrc
install_autostart_line() {
  [ "${CODESPACES:-}" = "true" ] || return 0
  local hook="$ROOT/.devcontainer/autostart.sh" rc="$HOME/.bashrc" line
  [ -f "$hook" ] || return 0
  line="$(printf 'if [ -f %q ]; then . %q; fi  %s' "$hook" "$hook" "$AUTOSTART_TAG")"
  touch "$rc" 2>/dev/null || return 0
  grep -qxF "$line" "$rc" && return 0
  if grep -qF "$AUTOSTART_TAG" "$rc"; then
    grep -vF "$AUTOSTART_TAG" "$rc" >"$rc.ac.$$" && cat "$rc.ac.$$" >"$rc"
    rm -f "$rc.ac.$$"
  fi
  printf '\n%s\n' "$line" >>"$rc"
}

# ------------------------------------------------- the pasted-command catch
# Setup starts by itself, so people sometimes type "bash setup.sh" at the key
# prompt, and with hidden input they cannot see that they did.
entry_is_command() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    *setup.sh*|*"bash "*|*python*) return 0 ;;
  esac
  return 1
}

# ------------------------------------------------------------ exit paths
on_exit() {
  dots_stop fail
  if [ "$READING" -eq 1 ]; then
    stty echo </dev/tty 2>/dev/null
    echo
  fi
  if [ -n "$TMP" ]; then rm -rf "$TMP"; fi
  lock_release
  if [ "$STOPPED" -eq 1 ] && [ "$READY_DONE" -eq 0 ]; then
    echo "Setup stopped. To start again, type: bash setup.sh" 2>/dev/null
  fi
}
trap on_exit EXIT
trap 'STOPPED=1; exit 130' INT
trap 'STOPPED=1; exit 143' TERM
trap 'STOPPED=1; exit 129' HUP

die() {
  dots_stop fail
  echo
  echo "❌ $1"
  echo
  echo "   $2"
  echo "   Still stuck? See the Troubleshooting table in README.md."
  exit 1
}

lock_claim

hr; echo " osu-llm-workshop: setup"; hr
echo "Repository version: $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
if [ -n "${WORKSHOP_AUTOSTARTED:-}" ]; then
  echo "Setup started by itself."
fi

install_autostart_line 2>/dev/null || true

# The site on port 8000. autostart.sh starts it too (there is no
# postAttachCommand: after Trust it opens a new terminal that takes focus); this
# covers a terminal where autostart did not run. Started here, early, so the
# address is usually known by READY. Detached, idempotent, Codespaces only.
if [ -n "${CODESPACE_NAME:-}" ] && [ -f "$ROOT/.devcontainer/site-public.sh" ] \
   && [ ! -s "$SITE_URL_FILE" ]; then
  ( setsid nohup bash "$ROOT/.devcontainer/site-public.sh" >/dev/null 2>&1 </dev/null & ) 2>/dev/null
fi
site_address() {   # the public address of site/, or where to find it
  if [ -s "$SITE_URL_FILE" ]; then head -1 "$SITE_URL_FILE"; else echo "the Ports tab, port 8000"; fi
}

# ------------------------------------------------------------- 1. tooling
# Everything that does not need your key happens first, so a container problem
# surfaces before you are asked for a key.
if ! python3 -c 'import openai, pydantic, pypdf, docx, pandas, numpy, matplotlib, scipy, statsmodels, seaborn' 2>/dev/null; then
  echo "Installing Python libraries (this only happens once)..."
  pip install --user --quiet -r "$ROOT/requirements.txt" >/tmp/python-install.log 2>&1 || true
  python3 -c 'import openai, pydantic, pypdf, docx, pandas, numpy, matplotlib, scipy, statsmodels, seaborn' 2>/dev/null \
    || die "The Python libraries could not be installed." \
           "Read the last lines of /tmp/python-install.log. Then stop and start the Codespace, or rebuild it (Ctrl+Shift+P, Codespaces: Rebuild Container); both keep your files."
fi
echo "✅ Python libraries present."

TMP="$(mktemp -d)"   # private to this user (mode 700); removed on every exit

# ------------------------------------------------------------- 2. saved values
env_value() {   # $1 = name; prints the value saved in .env, or nothing
  [ -f "$ENV_FILE" ] || return 0
  sed -n "s/^$1=//p" "$ENV_FILE" | tail -1 | tr -d '[:space:]"'"'"
}
write_env() {   # $1 = base url, $2 = key (may be empty), $3 = model (may be empty)
  ( umask 077
    {
      echo "# Written by setup.sh. Two values are all the labs need."
      if [ -n "$1" ]; then echo "LLM_BASE_URL=$1"; else echo "# LLM_BASE_URL=   (bash setup.sh fills this in from the key you paste)"; fi
      if [ -n "$2" ]; then echo "LLM_API_KEY=$2"; else echo "# LLM_API_KEY=   (paste the workshop key here, or run: bash setup.sh)"; fi
      if [ -n "$3" ]; then echo "LLM_MODEL=$3"; fi
      # Keep any other setting already saved (an OpenAlex key, for example).
      if [ -f "$ENV_FILE" ]; then grep -vE '^[[:space:]]*(#|$)|^[[:space:]]*(LLM_BASE_URL|LLM_API_KEY|LLM_MODEL)=' "$ENV_FILE" || true; fi
    } >"$ENV_FILE.new" ) && mv -f "$ENV_FILE.new" "$ENV_FILE" && chmod 600 "$ENV_FILE"
}

# ------------------------------------------------------------- 3. the endpoint
# BASE_SOURCE says who chose the endpoint: arg or secret (fixed: every key goes
# there), saved (the pair saved by an earlier run), or key (chosen below from
# the key itself, and chosen again if a different key is pasted).
BASE_SOURCE="key"
if [ -n "$BASE_ARG" ]; then
  BASE="$BASE_ARG"; BASE_SOURCE="arg"; echo "Endpoint from --base-url: $BASE"
elif [ -n "$SECRET_BASE" ]; then
  BASE="$SECRET_BASE"; BASE_SOURCE="secret"; echo "Endpoint from your Codespaces secret LLM_BASE_URL: $BASE"
elif [ "$RESET_KEY" -eq 0 ] && [ -z "$SECRET_KEY" ] && [ -n "$(env_value LLM_API_KEY)" ] && BASE="$(env_value LLM_BASE_URL)" && [ -n "$BASE" ]; then
  BASE_SOURCE="saved"; echo "Endpoint saved in .env: $BASE"
else
  BASE=""
fi
check_url() {
  case "$BASE" in
    http://*|https://*) BASE="${BASE%/}" ;;
    *) die "The endpoint \"$BASE\" is not a URL." "It should look like https://host/v1. Run: bash setup.sh --base-url https://host/v1" ;;
  esac
}
[ -z "$BASE" ] || check_url

# The model. Named with --model or a secret, it is used as is. Otherwise each
# endpoint has a default (above), and where that is empty the check below picks
# a Nemotron chat model from the models the endpoint lists.
MODEL_SOURCE=""
if [ -n "$MODEL_ARG" ]; then MODEL="$MODEL_ARG"; MODEL_SOURCE="named"; echo "Model from --model: $MODEL"
elif [ -n "$SECRET_MODEL" ]; then MODEL="$SECRET_MODEL"; MODEL_SOURCE="named"; echo "Model from your Codespaces secret LLM_MODEL: $MODEL"
elif [ "$BASE_SOURCE" = "saved" ] && MODEL="$(env_value LLM_MODEL)" && [ -n "$MODEL" ]; then MODEL_SOURCE="saved"; echo "Model saved in .env: $MODEL"
else MODEL=""; fi

# Which endpoint a key belongs to, from its shape.
provider_of() {
  case "$1" in
    sk-or-*) echo openrouter ;;
    nvapi-*) echo nvidia ;;
    *)       echo osu ;;
  esac
}
# load_osu_endpoint: fill OSU_BASE_URL and OSU_MODEL from workshop-endpoint.txt
# here, or, if that has no address, from the instructor's current copy online.
load_osu_endpoint() {
  [ "$OSU_LOADED" -eq 0 ] || return 0
  OSU_LOADED=1
  local txt=""
  [ -f "$ROOT/workshop-endpoint.txt" ] && txt="$(cat "$ROOT/workshop-endpoint.txt")"
  if ! printf '%s\n' "$txt" | grep -qE '^OSU_(BASE|KEY)_URL=https://'; then
    txt="$(curl -fsS -m 10 "$WORKSHOP_ENDPOINT_URL" 2>/dev/null)" || txt=""
  fi
  [ -n "$OSU_BASE_URL" ] || OSU_BASE_URL="$(printf '%s\n' "$txt" | sed -n 's/^OSU_BASE_URL=//p' | tail -1 | tr -d '[:space:]')"
  [ -n "$OSU_MODEL" ] || OSU_MODEL="$(printf '%s\n' "$txt" | sed -n 's/^OSU_MODEL=//p' | tail -1 | tr -d '[:space:]')"
  [ -n "$OSU_KEY_URL" ] || OSU_KEY_URL="$(printf '%s\n' "$txt" | sed -n 's/^OSU_KEY_URL=//p' | tail -1 | tr -d '[:space:]')"
  [ -n "$OSU_CONTEXT" ] || OSU_CONTEXT="$(printf '%s\n' "$txt" | sed -n 's/^OSU_CONTEXT=//p' | tail -1 | tr -d '[:space:]')"
  case "$OSU_CONTEXT" in ''|*[!0-9]*) OSU_CONTEXT=65536 ;; esac
  case "$OSU_BASE_URL" in https://*) ;; *) OSU_BASE_URL=""; OSU_MODEL="" ;; esac   # HTTPS only: the key travels there
  case "$OSU_KEY_URL" in https://*) OSU_KEY_URL="${OSU_KEY_URL%/}" ;; *) OSU_KEY_URL="" ;; esac
}

# exchange_word: the workshop gives out a word instead of a key. The word, in any
# letter case, is looked up at OSU_KEY_URL/<word in lower case>; when the reply
# is an OpenRouter key, that key replaces the word and the labs run on
# OpenRouter with the workshop model. A word nobody published is refused here,
# with a message, unless the room has its own endpoint (OSU_BASE_URL), where the
# word may be that endpoint's own secret and is passed on untouched. The word
# itself goes to the lookup address and nowhere else.
exchange_word() {
  [ "$(provider_of "$KEY")" = osu ] || return 0
  [ "$BASE_SOURCE" = key ] || [ "${BASE%/}" = "$OPENROUTER_BASE_URL" ] || return 0
  load_osu_endpoint
  [ -n "$OSU_KEY_URL" ] || return 0
  local word got=""
  word="$(printf '%s' "$KEY" | tr '[:upper:]' '[:lower:]')"
  case "$word" in *[!a-z0-9-]*) return 0 ;; esac          # only a plain word is looked up
  got="$(curl -fsS -m 15 "$OSU_KEY_URL/$word" 2>/dev/null | tr -d '[:space:]' | head -c 200)" || got=""
  case "$got" in
    sk-or-*) KEY="$got"; KEY_FROM=word
             echo "That is the workshop word: using the workshop's own OpenRouter key."
             return 0 ;;
  esac
  [ -z "$OSU_BASE_URL" ] || return 0
  if [ "$word" = "$WORKSHOP_WORD" ]; then
    # The right word, but no key came back: the lookup is down, or the day is over.
    echo "That is the workshop word, but its key could not be fetched."
    echo "During the workshop: tell a helper. After 5:00 on Wednesday, November 11, the workshop key is gone:"
    echo "paste your own OpenRouter key (sk-or-..., from openrouter.ai/keys) or NVIDIA key (nvapi-...)."
    return 1
  fi
  echo "That word is not the workshop word. Check the spelling (letter case does not matter),"
  echo "or paste your own OpenRouter key (sk-or-...) or NVIDIA key (nvapi-...)."
  return 1
}

# word_expired: the workshop word was for the workshop day only, Wednesday,
# November 11, 2026. From Thursday on (Oklahoma time, UTC-6 in November, which
# needs no time zone files) setup does not look it up:
# it says the word has ended and how to go on with a key of your own, and the
# prompt asks again. WORKSHOP_TODAY=YYYY-MM-DD stands in for today's date in tests.
WORKSHOP_WORD="openingdaytoken"
WORKSHOP_WORD_LAST_DAY=20261111
after_workshop_day() {
  local today="${WORKSHOP_TODAY:-$(TZ=CST6 date +%Y-%m-%d)}"
  today="${today//-/}"
  case "$today" in ''|*[!0-9]*) return 1 ;; esac
  [ "$today" -gt "$WORKSHOP_WORD_LAST_DAY" ]
}
word_expired() {
  local word
  word="$(printf '%s' "$KEY" | tr '[:upper:]' '[:lower:]')"
  [ "$word" = "$WORKSHOP_WORD" ] || return 1
  after_workshop_day || return 1
  hr
  echo " OpeningDayToken was only for the OSU workshop on Wednesday, November 11, 2026."
  echo " It no longer works. Every exercise still works with a key of your own:"
  echo
  echo " Your own OpenRouter key. Make one at https://openrouter.ai/keys, add a few"
  echo "   dollars of credit and set a limit on the key. It starts with sk-or-."
  echo "   Paste it at the prompt below. At the list of models, press Enter for"
  echo "   Nemotron 3 Ultra, the workshop's model."
  echo " Cimarron, OSU's cluster, if it is available to you. Ask the HPCC about access"
  echo "   and a key (https://hpcc.okstate.edu). Then run, with the address they give you:"
  echo "     bash setup.sh --reset-key --base-url <address>"
  echo "   and paste their key."
  echo
  echo " No key yet? Press Enter. When you have one, run: bash setup.sh --reset-key"
  echo " More in followon/continue.md."
  hr
  return 0
}

# endpoint_for_key: when the key decides (BASE_SOURCE=key), set BASE and the
# default MODEL for the provider the key belongs to. Returns 1, with a message,
# when that provider's endpoint is not configured.
endpoint_for_key() {
  [ "$BASE_SOURCE" = "key" ] || return 0
  local p name model
  p="$(provider_of "$KEY")"
  case "$p" in
    openrouter) BASE="$OPENROUTER_BASE_URL"; model="$OPENROUTER_MODEL"; name="an OpenRouter key" ;;
    nvidia)     BASE="$NVIDIA_BASE_URL";     model="$NVIDIA_MODEL";     name="an NVIDIA key" ;;
    osu)        load_osu_endpoint
                BASE="$OSU_BASE_URL";        model="$OSU_MODEL";        name="the OSU workshop key" ;;
  esac
  if [ -z "$BASE" ]; then
    echo "That looks like the OSU workshop key, but the workshop endpoint is not set up yet."
    echo "Use an OpenRouter key (starts with sk-or-) or an NVIDIA key (starts with nvapi-) for now,"
    echo "or press Enter to finish without a key."
    return 1
  fi
  check_url
  if [ "$MODEL_SOURCE" != "named" ]; then MODEL="$model"; fi
  echo "That is ${name}: using $BASE"
}

# ------------------------------------------------------------- 4. the key
# check_key: two requests. First GET $BASE/models, which shows the endpoint is
# there and which models it serves. Some hosted endpoints (OpenRouter, NVIDIA)
# answer that without looking at the key, so the second request asks the chosen
# model for one token: that needs a real key, and it proves the model name works.
# It costs a fraction of a cent. The key goes to curl as a config file on stdin
# (printf is a shell builtin, so it is never on any command line). Sets HTTP to
# the status of the last request, 000 on a network failure.
check_key() {
  HTTP="$(printf 'header = "Authorization: Bearer %s"\n' "$KEY" \
    | curl -s -m 20 -K - -o "$TMP/models.json" -w '%{http_code}' "$BASE/models")"
  HTTP="${HTTP:0:3}"; HTTP="${HTTP:-000}"
  [ "$HTTP" = "200" ] || return 0
  [ -n "$MODEL" ] || MODEL="$(pick_model)"
  python3 - "$MODEL" "$TMP/probe.json" <<'PYEOF' 2>/dev/null
import json, sys
body = {"messages": [{"role": "user", "content": "Reply with one word: ready"}], "max_tokens": 1}
if sys.argv[1]:
    body["model"] = sys.argv[1]
json.dump(body, open(sys.argv[2], "w"))
PYEOF
  HTTP="$(printf 'header = "Authorization: Bearer %s"\n' "$KEY" \
    | curl -s -m 60 -K - -H 'Content-Type: application/json' -d @"$TMP/probe.json" \
        -o "$TMP/probe.out" -w '%{http_code}' "$BASE/chat/completions")"
  HTTP="${HTTP:0:3}"; HTTP="${HTTP:-000}"
}
# The same wording for a 400 or 404 everywhere: a wrong endpoint address or
# model name. The endpoint's own explanation is shown when it gives one: an
# OpenAI-style {"error": ...}, NVIDIA's {"title", "detail"}, or a plain-text
# body such as "404 page not found".
not_found() {
  local why hint
  why="$(python3 - "$TMP/probe.out" "$TMP/models.json" <<'PYEOF' 2>/dev/null
import json, sys
for path in sys.argv[1:]:
    try:
        text = open(path, errors="replace").read()
    except Exception:
        continue
    msg = ""
    try:
        body = json.loads(text)
        if isinstance(body, dict):
            e = body.get("error")
            if isinstance(e, dict):
                msg = e.get("message") or ""
            elif e:
                msg = str(e)
            else:
                msg = " ".join(str(body[k]) for k in ("title", "detail", "message") if body.get(k))
    except Exception:
        msg = text if "<" not in text else ""
    msg = " ".join(msg.split())
    if msg:
        print(msg[:200])
        break
PYEOF
)"
  hint="Check the endpoint and model, for example: bash setup.sh --reset-key --model <name>"
  if [ "$(provider_of "$KEY")" = "nvidia" ] && [ "$HTTP" = "404" ]; then
    hint="NVIDIA opens only some hosted models to a personal account; the key itself was accepted.
   Ask help@build.nvidia.com to enable Public API Endpoints for your account, or try another model:"
    if [ "$MODEL" = "$NVIDIA_MODEL" ]; then
      hint="$hint bash setup.sh --reset-key --model <name>"
    else
      hint="$hint bash setup.sh --reset-key --model $NVIDIA_MODEL"
    fi
  fi
  die "The endpoint refused the request (HTTP $HTTP): it does not know that address or model${MODEL:+ ($MODEL)}.${why:+ It said: $why}" \
      "$hint"
}

# pick_model: from the saved /models reply, a Nemotron chat model if there is
# one (a "super" one first, then the newer nvidia/nemotron-* names), skipping
# embedding, reward, safety, retrieval and vision models; otherwise the first
# chat model; otherwise the first model. An endpoint serving one model gets it.
pick_model() {
  python3 - "$TMP/models.json" <<'PYEOF' 2>/dev/null
import json, sys
try:
    ids = [m["id"] for m in (json.load(open(sys.argv[1])).get("data") or []) if m.get("id")]
except Exception:
    ids = []
skip = ("embed", "reward", "guard", "safety", "rerank", "retriev", "parse", "ocr", "-vl", "vlm",
        "vision", "audio", "speech", "asr", "tts", "clip", "translate")
chat = [i for i in ids if not any(s in i.lower() for s in skip)]
nemo = [i for i in chat if "nemotron" in i.lower()]
nemo.sort(key=lambda i: ("super" not in i.lower(), not i.lower().startswith("nvidia/nemotron")))
for group in (nemo, chat, ids):
    if group:
        print(group[0])
        break
PYEOF
}
key_looks_right() {
  [ "${#KEY}" -ge 8 ] && [[ "$KEY" != *[[:space:]]* ]]
}

if [ "$RESET_KEY" -eq 1 ]; then
  rm -f "$MARKER"
  echo "Forgot the saved key."
  if [ -n "$SECRET_KEY" ]; then
    echo "Your Codespaces secret LLM_API_KEY is not used this time: --reset-key asks for the key instead."
    SECRET_KEY=""
  fi
fi

if [ -n "$SECRET_KEY" ]; then
  echo "Using your Codespaces secret LLM_API_KEY"
  KEY="$SECRET_KEY"
  KEY_FROM=secret
  endpoint_for_key || die "The key in your Codespaces secret LLM_API_KEY has no endpoint yet." \
    "Add a Codespaces secret LLM_BASE_URL with the endpoint, or use an OpenRouter or NVIDIA key."
  dots_start "Checking the key against the endpoint"
  check_key
  case "$HTTP" in
    200) dots_stop ok ;;
    401|403) dots_stop fail
      die "The endpoint did not accept the key in your Codespaces secret LLM_API_KEY (HTTP $HTTP)." \
          "Fix the secret at https://github.com/settings/codespaces, then stop and restart this Codespace." ;;
    400|404) not_found ;;
    000) die "Could not reach $BASE (network)." "Check your connection, then run bash setup.sh again." ;;
    *) die "Unexpected reply from the endpoint (HTTP $HTTP)." "Wait a minute, then run bash setup.sh again." ;;
  esac
elif [ "$RESET_KEY" -eq 0 ] && KEY="$(env_value LLM_API_KEY)" && [ -n "$KEY" ]; then
  echo "Using the key saved in .env (to change it: bash setup.sh --reset-key)"
  endpoint_for_key || KEY=""
  if [ -n "$KEY" ]; then
    dots_start "Checking the key against the endpoint"
    check_key
    case "$HTTP" in
      200) dots_stop ok ;;
      401|403) dots_stop fail; echo "   The saved key no longer works. Forgetting it."; KEY=""
        # The next key pasted chooses its own endpoint and model again.
        if [ "$BASE_SOURCE" = "saved" ]; then BASE_SOURCE="key"; fi
        if [ "$MODEL_SOURCE" = "saved" ]; then MODEL=""; MODEL_SOURCE=""; fi ;;
      400|404) not_found ;;
      000) die "Could not reach $BASE (network)." "Check your connection, then run bash setup.sh again." ;;
      *) die "Unexpected reply from the endpoint (HTTP $HTTP)." "Wait a minute, then run bash setup.sh again." ;;
    esac
  fi
else
  KEY=""
fi

if [ -z "$KEY" ] && [ -z "${WORKSHOP_NO_PROMPT:-}" ] && { : </dev/tty; } 2>/dev/null; then
  ATTEMPT=0
  while [ "$ATTEMPT" -lt 3 ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo
    if after_workshop_day; then
      echo "Paste your key: your own OpenRouter key (sk-or-...) or NVIDIA key (nvapi-...)."
      echo "Then press Enter."
    else
      echo "Paste your key: the workshop word, or your own OpenRouter key"
      echo "(sk-or-...) or NVIDIA key (nvapi-...). Then press Enter."
    fi
    echo "No key yet? Just press Enter: the Codespace is ready and the check waits for the key."
    printf "> "
    ENTRY=""
    READING=1
    IFS= read -r ENTRY </dev/tty || true
    READING=0
    echo
    if entry_is_command "$ENTRY"; then
      echo "Setup is already running. Paste only the key, or press Enter."
      ATTEMPT=$((ATTEMPT - 1))
      continue
    fi
    KEY="${ENTRY//[[:space:]]/}"
    KEY_FROM=prompt
    ENTRY=""
    [ -n "$KEY" ] || break
    echo "Received ${#KEY} characters."
    if ! key_looks_right; then
      echo "That does not look like a key: it should be at least eight characters with no spaces."
      KEY=""; continue
    fi
    if word_expired; then KEY=""; continue; fi
    exchange_word || { KEY=""; continue; }
    endpoint_for_key || { KEY=""; continue; }
    dots_start "Checking the key against the endpoint"
    check_key
    case "$HTTP" in
      200) dots_stop ok; break ;;
      401|403) dots_stop fail
        if [ "$KEY_FROM" = word ]; then echo "The workshop key behind that word was not accepted (HTTP $HTTP). Tell the instructor."
        else echo "That key was not accepted (HTTP $HTTP). Copy the whole key and try again."; fi
        KEY="" ;;
      400|404) not_found ;;
      000) die "Could not reach $BASE (network)." "Check your connection, then run bash setup.sh again." ;;
      *) die "Unexpected reply from the endpoint (HTTP $HTTP)." "Wait a minute, then run bash setup.sh again." ;;
    esac
  done
fi

# ------------------------------------------------------------- 5. write and report
# OpenRouter serves hundreds of models. When an OpenRouter key was just pasted
# (or --choose-model was given) and no model was named, offer the short tested
# list. Enter keeps the first. A choice is checked with one token before it is
# saved; if it fails, the default stays.
choose_openrouter_model() {
  local i n=${#OPENROUTER_CHOICES[@]} pick id current="$MODEL"
  echo
  echo "Which model? OpenRouter offers many; these $n are the workshop's short list."
  for ((i = 0; i < n; i++)); do
    id="${OPENROUTER_CHOICES[$i]%%|*}"
    printf '  %d  %s\n     %s%s\n' "$((i + 1))" "${OPENROUTER_CHOICES[$i]#*|}" "$id" \
      "$([ "$id" = "$current" ] && echo "   (current)")"
  done
  while :; do
    printf "Type a number, or press Enter for 1: "
    pick=""
    IFS= read -r pick </dev/tty || pick=""
    pick="${pick//[[:space:]]/}"
    [ -n "$pick" ] || pick=1
    if [[ "$pick" =~ ^[0-9]+$ ]] && [ "$pick" -ge 1 ] && [ "$pick" -le "$n" ]; then break; fi
    echo "That is not one of the numbers 1 to $n."
  done
  id="${OPENROUTER_CHOICES[$((pick - 1))]%%|*}"
  [ "$id" != "$current" ] || { echo "Model: $id"; return 0; }
  MODEL="$id"
  dots_start "Checking $MODEL"
  check_key
  if [ "$HTTP" = "200" ]; then
    dots_stop ok
  else
    dots_stop fail
    echo "   $MODEL did not answer (HTTP $HTTP). Keeping $current; to try another: bash setup.sh --choose-model"
    MODEL="$current"
  fi
}
if [ -n "$KEY" ] && [ "$(provider_of "$KEY")" = openrouter ] && [ "${BASE%/}" = "$OPENROUTER_BASE_URL" ] \
   && [ "$MODEL_SOURCE" != named ] && { [ "$KEY_FROM" = prompt ] || [ "$CHOOSE_MODEL" -eq 1 ]; } \
   && [ -t 0 ] && [ -z "${WORKSHOP_NO_PROMPT:-}" ] && { : </dev/tty; } 2>/dev/null; then
  [ -n "$MODEL" ] || MODEL="$OPENROUTER_MODEL"
  choose_openrouter_model
fi
# With an accepted key and no model named, choose one from what the endpoint lists.
if [ -n "$KEY" ] && [ -z "$MODEL" ]; then MODEL="$(pick_model)"; fi
if [ -z "$KEY" ] && [ "$BASE_SOURCE" = "key" ]; then BASE="$OSU_BASE_URL"; MODEL=""; fi
write_env "$BASE" "$KEY" "$MODEL" || die "Could not write $ENV_FILE." "Check that this folder is writable, then run bash setup.sh again."
READY_DONE=1
: >"$MARKER"
hr
if [ -n "$KEY" ]; then
  echo " READY. Endpoint: $BASE"
  [ -n "$MODEL" ] && echo " Model: $MODEL"
  [ -z "${CODESPACE_NAME:-}" ] || echo " Your site (files in site/): $(site_address)"
  echo " The key is saved in .env (never committed)."
else
  echo " Codespace ready; endpoint check pending."
  if after_workshop_day; then echo " When you have a key, type:   bash setup.sh"
  else echo " When you have the workshop key, type:   bash setup.sh"; fi
  hr
  exit 0
fi
hr

# ------------------------------------------------------------- 6. what next
# OpenClaw is a complete agent program (Node), installed in the container image.
# openclaw_configure points it at the same endpoint, key and model as .env:
# a custom OpenAI-compatible provider named "workshop" in ~/.openclaw/openclaw.json
# (mode 600, folder 700). The key reaches python through that one command's
# environment, never a command line. The agent works inside this repository,
# with rules that keep it away from .env and the OpenClaw folder.
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
OPENCLAW_LOG="$HOME/.osu-llm-workshop-openclaw.log"   # why configuration failed; never a key

# openclaw_context: how much conversation OpenClaw may keep before it compacts.
# OpenRouter's Nemotron providers serve at least 200,000 tokens, and a long
# analysis session needs it; the OSU endpoint states its own (the NIM recipe
# caps it at 65,536); anything else gets 65,536.
openclaw_context() {
  if [ "${BASE%/}" = "$OPENROUTER_BASE_URL" ]; then echo 200000; return; fi
  load_osu_endpoint
  if [ -n "$OSU_BASE_URL" ] && [ "${BASE%/}" = "${OSU_BASE_URL%/}" ]; then echo "$OSU_CONTEXT"; return; fi
  echo 65536
}

openclaw_configure() {
  if ! command -v openclaw >/dev/null 2>&1; then
    # Install it only in a Codespace: elsewhere this would be a global npm
    # install on someone's own computer (solutions/00_setup/perform.sh runs
    # setup on John's Mac).
    if [ "${CODESPACES:-}" != true ]; then
      echo "OpenClaw is not installed here; it comes with the workshop Codespace."
      return 1
    fi
    echo "OpenClaw is not installed in this Codespace; installing it (about a minute)..."
    bash "$ROOT/followon/openclaw/install.sh" >/dev/null 2>&1
    command -v openclaw >/dev/null 2>&1 || {
      echo "❌ OpenClaw could not be installed. See /tmp/openclaw-install.log."
      return 1
    }
  fi
  [ -n "$MODEL" ] || MODEL="$(pick_model)"
  if [ -z "$MODEL" ]; then
    echo "❌ OpenClaw needs a model name, and the endpoint did not list one. Run: bash setup.sh --model <name> --openclaw"
    return 1
  fi
  dots_start "Connecting OpenClaw to $MODEL"
  ( umask 077; : >"$OPENCLAW_LOG" ) 2>/dev/null
  if ! WS_KEY="$KEY" WS_BASE="$BASE" WS_ROOT="$ROOT" WS_CTX="$(openclaw_context)" python3 - "$MODEL" >/dev/null 2>>"$OPENCLAW_LOG" <<'PYEOF'
import json, os, sys
model = sys.argv[1]
path = os.path.expanduser("~/.openclaw/openclaw.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
os.chmod(os.path.dirname(path), 0o700)
cfg = {}
if os.path.exists(path):
    try:
        cfg = json.load(open(path))
    except Exception:
        cfg = {}
providers = cfg.setdefault("models", {}).setdefault("providers", {})
providers["workshop"] = {
    "baseUrl": os.environ["WS_BASE"],
    "apiKey": os.environ["WS_KEY"],
    "api": "openai-completions",
    "models": [{"id": model, "name": model, "input": ["text"],
                "contextWindow": int(os.environ["WS_CTX"]), "maxTokens": 16384}],
}
d = cfg.setdefault("agents", {}).setdefault("defaults", {})
d.setdefault("model", {})["primary"] = "workshop/" + model
d.setdefault("modelPolicy", {})["allow"] = ["workshop/*"]
d.pop("models", None)
d["cwd"] = os.environ["WS_ROOT"]       # files it writes land where the editor shows them
d["verboseDefault"] = "on"             # show each tool call, so the loop is visible
d["skipBootstrap"] = True
# OpenClaw keeps its own default tools and skills: no limits from the workshop
# (John, 2026-10-31). Measured cost: about 40,600 input tokens per model call,
# against about 7,000 with skills off and four tools. To limit it again, add:
#   d["skills"] = []; cfg["tools"] = {"allow": ["read", "write", "edit", "exec"]}
d.pop("skills", None)
# Commands run without asking: OpenClaw's exec security "full" and ask "off",
# so the chat never stops for an approval prompt.
cfg["tools"] = {"exec": {"security": "full", "ask": "off"}}
cfg.setdefault("memory", {}).setdefault("search", {})["enabled"] = False
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    json.dump(cfg, f, indent=2)
os.chmod(path, 0o600)
PYEOF
  then
    dots_stop fail
    echo "   Could not write the OpenClaw configuration (details: $OPENCLAW_LOG)."
    return 1
  fi
  openclaw doctor --fix >/dev/null 2>&1 || true
  # A fixed identity and the rules of this room. Without it, OpenClaw's first-run
  # ritual (BOOTSTRAP.md, "introduce yourself and pick a name") takes over the
  # first prompt.
  local ws="$HOME/.openclaw/workspace"
  mkdir -p "$ws"
  rm -f "$ws/BOOTSTRAP.md"
  cat >"$ws/IDENTITY.md" <<'IDEOF'
# IDENTITY.md - Who Am I?

- **Name:** Workshop Agent
- **Creature:** research assistant agent
- **Vibe:** plain, careful, shows its work

## About this Codespace

- You are working in the person's own copy of the workshop repository. Its documents are in corpus/ and mine/.
- site/ is the person's website. It is already served on port 8000 and is public while this Codespace runs, so there is no need to start a web server.
- Use relative links in site/ (href="lesson2.html", not href="/lesson2.html"): the permanent copy on GitHub Pages lives under /<repository name>/.
- python3 .devcontainer/site-check.py checks site/ before it goes public.
- To publish site/ to GitHub Pages: bash publish-site.sh --yes  (it runs the site check first).

## Socratic tutor questions on the pages

The site can ask students questions and have this workshop's model judge each answer, Socratically: it says what is right and asks one guiding question, and never gives the answer away. Build it like this whenever the person asks for a tutor, check questions, practice questions or a Socratic site:

1. In a page, put each question in a block with a short id (letters, digits, - or _), and keep the question text visible:
   <div class="socratic" data-question="buffer-1"><p>Why does a buffer resist a change in pH?</p></div>
2. Before </body> on that page add <script src="socratic.js" defer></script> (from a page in a subfolder: ../socratic.js). If site/socratic.js is missing, copy .devcontainer/site-kit/socratic.js there.
3. Also write the answer key to site/.tutor/questions.json, one entry per id. It is optional (without it the tutor judges from the question and the page) but it makes the judging match the instructor's intent, so write it every time:
   {"brief": "who the students are and what to stress", "questions": {"buffer-1": {"question": "the same question text", "answer": "a complete model answer with the key points", "misconceptions": ["a common wrong idea", "another"]}}}
   The folder starts with a dot, so it is never served or published: students cannot read the key. Never put the answer in the page itself.
4. Good questions ask students to explain, predict or apply, not to recall a word. One or two per page is plenty.
5. The checking works on the live address only. On the permanent GitHub Pages copy each question shows with a note that answers are checked on the live site.

## When the person asks for a website

1. Write the whole site they asked for into site/: index.html as the front page, every page linked from it, relative links only.
2. Run python3 .devcontainer/site-check.py and fix anything it lists under NOT READY.
3. Stop there. Do not start a server and do not run publish-site.sh: the site is already live, and it is published to its permanent address automatically within a minute of your last change.
4. End your reply with the two addresses from the section below, exactly as given:
   Live now: the live address
   Permanent (once published, a minute or more): the permanent address
IDEOF
  # The site's real addresses, so OpenClaw never has to guess one. In a test on
  # 2026-10-31 it was asked for the address and invented one that did not
  # exist. The live address can appear a few seconds after setup (site-public.sh
  # runs in the background), so the rule also says where to read it. The
  # permanent one follows from the repository: https://<owner>.github.io/<repo>/.
  local remote owner repo pages=""
  remote="$(git -C "$ROOT" remote get-url origin 2>/dev/null)"
  case "$remote" in
    *github.com[:/]*/*)
      repo="${remote##*/}"; repo="${repo%.git}"
      owner="${remote%/*}"; owner="${owner##*[:/]}"; owner="$(printf '%s' "$owner" | tr '[:upper:]' '[:lower:]')"
      if [ "$(printf '%s' "$repo" | tr '[:upper:]' '[:lower:]')" = "$owner.github.io" ]; then
        pages="https://$owner.github.io/"
      else
        pages="https://$owner.github.io/$repo/"
      fi ;;
  esac
  [ -z "$pages" ] || printf '%s\n' "$pages" >"$HOME/.osu-llm-workshop-pages-url"
  {
    echo
    echo "## The site's addresses"
    echo
    if [ -s "$SITE_URL_FILE" ]; then
      echo "- Live address (works now, while this Codespace runs): $(head -1 "$SITE_URL_FILE")"
    fi
    echo "- The live address is also the one line in $SITE_URL_FILE. If that file is empty or missing, say: open the Ports tab, port 8000, and click the globe icon."
    if [ -n "$pages" ]; then
      echo "- Permanent address (GitHub Pages, updated automatically a minute after site/ changes): $pages"
    fi
    echo "- Whether the last automatic publish worked is in $HOME/.osu-llm-workshop-pages-status: PUBLISHED, or ONE STEP LEFT with a link the person must open once and set Source: Deploy from a branch, Branch: gh-pages, / (root). Read it when the person asks whether the site is published."
    echo "- Never guess or construct a site address."
  } >>"$ws/IDENTITY.md"
  if ! openclaw config validate >>"$OPENCLAW_LOG" 2>&1; then
    dots_stop fail
    echo "   OpenClaw did not accept its configuration (details: $OPENCLAW_LOG)."
    return 1
  fi
  chmod 700 "$HOME/.openclaw" 2>/dev/null
  chmod 600 "$HOME/.openclaw"/openclaw.json* 2>/dev/null
  dots_stop ok
  echo "✅ OpenClaw is connected to $MODEL."
  return 0
}

openclaw_open() {
  if [ -n "${WORKSHOP_NO_CHAT:-}" ] || [ ! -t 0 ]; then
    echo "OpenClaw is connected. To open it, type:   openclaw chat"
    return 0
  fi
  if command -v pgrep >/dev/null 2>&1 && pgrep -f 'openclaw[^[:space:]]*[- ]chat' >/dev/null 2>&1; then
    echo "OpenClaw is already open in another terminal: the list at the right edge of this panel."
    return 0
  fi
  echo
  echo "Opening OpenClaw. Type a request and press Enter; /exit or Ctrl+C closes it."
  [ -z "${CODESPACE_NAME:-}" ] || echo "Your site, live now:    $(site_address)"
  [ -s "$HOME/.osu-llm-workshop-pages-url" ] && echo "Permanent address:      $(head -1 "$HOME/.osu-llm-workshop-pages-url")  (after the first build)"
  echo "Try:  Create a three-page website teaching <a topic you teach> to <your students>."
  echo
  # Setup is finished: let another terminal run setup again, and give Ctrl+C to
  # OpenClaw. Only setup's own switches are taken out of its environment; it
  # keeps the Codespace's GitHub sign-in, so it can push and use gh.
  KEY=""
  lock_release
  trap - INT TERM
  env -u WORKSHOP_AUTOSTARTED -u WORKSHOP_FORCE -u WORKSHOP_NO_PROMPT openclaw chat
  echo
  echo "OpenClaw has closed. To open it again:   openclaw chat"
  echo "The first exercise:                      00_website/README.md"
  [ -z "${CODESPACE_NAME:-}" ] || echo "Your site:                               $(site_address)"
  echo "After the website, Stop 2:                02_data/README.md"
}

# exercise_show: open the first exercise in the editor and say what comes next.
# $1 = 1 when OpenClaw could not be connected, to say how to try again.
exercise_readme() {   # open the exercise's page in the editor when there is one
  local readme="$ROOT/00_website/README.md"
  if [ -f "$readme" ] && command -v code >/dev/null 2>&1 \
     && { [ "${TERM_PROGRAM:-}" = vscode ] || [ "${TERM_PROGRAM:-}" = codespaces ]; }; then
    code -r "$readme" >/dev/null 2>&1 || true
    echo "The first exercise is open in the editor: 00_website/README.md"
  else
    echo "The first exercise: 00_website/README.md"
  fi
}
exercise_show() {
  exercise_readme
  echo
  echo " The first exercise:        openclaw chat"
  [ -z "${CODESPACE_NAME:-}" ] || echo " Your site:                 $(site_address)"
  echo " After the website, Stop 2:  02_data/README.md"
  if [ "${1:-0}" = 1 ]; then
    echo
    echo " OpenClaw is not connected yet. To try again:   bash setup.sh --openclaw"
  fi
}

# Choice 1, and the answer when there is no one to ask: connect OpenClaw (quick,
# needs no input) without opening it, then show the first exercise.
exercise_open() {
  if openclaw_configure; then exercise_show 0; else exercise_show 1; fi
}

if [ -n "${WORKSHOP_SWITCHING:-}" ]; then
  # From 00_setup/switch_backend.sh, between stops: reconnect OpenClaw to the
  # new endpoint, and open nothing.
  if openclaw_configure; then
    echo "OpenClaw now uses this endpoint too. A chat that was already open keeps the old one:"
    echo "close it (/exit) and type:   openclaw chat"
  else
    echo "OpenClaw is not connected to the new endpoint. To try again:   bash setup.sh --openclaw"
  fi
elif [ "$OPENCLAW_ARG" -eq 1 ]; then
  openclaw_configure && openclaw_open
elif [ -t 0 ] && [ -z "${WORKSHOP_NO_PROMPT:-}" ] && { : </dev/tty; } 2>/dev/null; then
  # No question: straight into the first exercise, in OpenClaw's chat.
  if openclaw_configure; then
    exercise_readme
    openclaw_open
  else
    exercise_show 1
  fi
else
  exercise_open
fi
exit 0
