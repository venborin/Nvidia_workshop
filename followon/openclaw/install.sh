#!/usr/bin/env bash
# OpenClaw, pinned. The workshop image already has it; this reinstalls it if it
# is missing. Optional; nothing in the labs needs it.
# Pinned together with Node 22.23.2, which the workshop container already has,
# as verified in jhassell/asee9. Later OpenClaw releases need Node 24. If the
# pinned OpenClaw is already installed, this says so and changes nothing.
set -uo pipefail
OPENCLAW_VERSION="2026.9.2"
command -v npm >/dev/null 2>&1 || { echo "npm is not installed here; this is meant for the Codespace."; exit 1; }
if openclaw --version 2>/dev/null | grep -qF "$OPENCLAW_VERSION"; then
  echo "OpenClaw ${OPENCLAW_VERSION} is already installed."
else
  echo "Installing OpenClaw ${OPENCLAW_VERSION} (about a minute)..."
  for attempt in 1 2 3; do
    npm install -g "openclaw@${OPENCLAW_VERSION}" >/tmp/openclaw-install.log 2>&1 && break
    echo "attempt ${attempt} failed; retrying in 5 s"; sleep 5
  done
  command -v openclaw >/dev/null 2>&1 || { echo "Install failed. See /tmp/openclaw-install.log"; exit 1; }
  echo "Installed: $(openclaw --version 2>/dev/null | head -1)"
fi
echo
echo "To connect it to the workshop model and open it:   bash setup.sh --openclaw"
