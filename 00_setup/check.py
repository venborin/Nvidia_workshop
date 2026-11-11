"""Module 0: does this Codespace reach the model?

    python 00_setup/check.py

Without a key it says "Codespace ready; endpoint check pending." and stops,
and that is the pre-work's success signal. With a key it prints three lines: the
model the labs will use, the model's reply (joined onto one line), and whether
OpenClaw is connected to the same endpoint and model. All three must be good
before the green note goes up. An empty reply is tried once more with a larger token budget
(a model that thinks before it answers can spend the first budget thinking); if
it is still empty the check says so and exits non-zero. Standard library only,
so it works before anything is installed.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")  # .env wins, as in llm.py


load_env()
BASE = os.environ.get("LLM_BASE_URL", "").rstrip("/")
KEY = os.environ.get("LLM_API_KEY", "")

if not BASE or not KEY:
    print("Codespace ready; endpoint check pending.")
    print("When you have the workshop key, type:  bash setup.sh")
    sys.exit(0)

HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def get(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


try:
    models = get(f"{BASE}/models", timeout=20)
    model = os.environ.get("LLM_MODEL") or models["data"][0]["id"]
    print(f"reachable; serving {model}")
    text = ""
    for budget in (200, 1000):   # one retry with room to think, then give up
        body = json.dumps({
            "model": model,
            "max_tokens": budget,
            "messages": [{"role": "user", "content": "Reply with the single word: ready"}],
        }).encode()
        reply = get(f"{BASE}/chat/completions", data=body)
        text = " ".join((reply["choices"][0]["message"].get("content") or "").split())
        if text:
            break
    if not text:
        print("completion: (empty reply, twice) The endpoint answered but the model sent no text.")
        print("Run the check again. If it stays empty, tell a helper.")
        sys.exit(1)
    print(f"completion: {text}")
except urllib.error.HTTPError as err:
    print(f"not reachable: HTTP {err.code} from {err.url}")
    if err.code in (401, 403):
        print("The key was not accepted. Run:  bash setup.sh --reset-key")
    sys.exit(1)
except Exception as err:  # network, DNS, timeout
    print(f"not reachable: {err}")
    sys.exit(1)


def openclaw_line():
    """Is OpenClaw set up for this endpoint and model? Reads its config; no request is made."""
    path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        cfg = json.loads(path.read_text())
    except (OSError, ValueError):
        return False, "openclaw: not connected. Type:  bash setup.sh --openclaw"
    provider = ((cfg.get("models") or {}).get("providers") or {}).get("workshop") or {}
    primary = (((cfg.get("agents") or {}).get("defaults") or {}).get("model") or {}).get("primary", "")
    want = os.environ.get("LLM_MODEL") or model
    if provider.get("baseUrl", "").rstrip("/") != BASE or primary != f"workshop/{want}":
        return False, f"openclaw: connected to a different endpoint or model ({primary or 'none'}). Type:  bash setup.sh --openclaw"
    return True, f"openclaw: connected to {want}"


ok, line = openclaw_line()
print(line)
sys.exit(0 if ok else 1)
