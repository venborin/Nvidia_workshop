"""The only two calls the morning needs.

    from llm import ask, ask_json
    ask("Summarize this in two sentences: ...")          -> str
    ask_json("Fill in the record for ...", Record)       -> Record

Both talk to one OpenAI-compatible endpoint named by two values in .env:
LLM_BASE_URL and LLM_API_KEY. Nothing in this file is specific to a vendor.
Optional: LLM_MODEL picks a model; otherwise the first one the endpoint lists.

Every call records what it cost, so the day's numbers are honest:
    import llm; llm.ask("..."); print(llm.LAST, llm.TOTAL)
LAST is the latest call (model, request id, tokens, cost in dollars when the
endpoint reports it); TOTAL adds up every call this program made.

On OpenRouter, ask(prompt, web=True) lets the model search the web first; the
pages it used are in llm.LAST["sources"].
"""
import json
import os
import re
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parent


def _load_env():
    """Read .env next to this file into the environment. Its values win over
    anything already set: setup.sh writes .env after weighing any Codespaces
    secret, the saved values and the key you pasted, so .env is the answer."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


_load_env()
BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
API_KEY = os.environ.get("LLM_API_KEY", "")
MODEL = os.environ.get("LLM_MODEL", "")

if not BASE_URL or not API_KEY:
    raise SystemExit(
        "No endpoint or key yet. Run:  bash setup.sh   (it writes LLM_BASE_URL and LLM_API_KEY to .env)"
    )

# A stalled request must not hold a terminal for long: the client's defaults are a
# 600-second timeout and two retries, half an hour in the worst case. The slowest
# call measured on November 6 took about a minute; three minutes, one retry.
client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=180, max_retries=1)
ON_OPENROUTER = BASE_URL.startswith("https://openrouter.ai/")

LAST = {}
TOTAL = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}


def model_name() -> str:
    """The model every call uses. Asked of the endpoint once, then remembered."""
    global MODEL
    if not MODEL:
        MODEL = client.models.list().data[0].id
    return MODEL


def chat(messages, tools=None, max_tokens=3000, temperature=0.2, web=False):
    """One round trip. Returns the assistant message object (content, tool_calls).
    max_tokens is generous because some models think before they answer, and
    the thinking counts against it (a Nemotron answer can spend 1,000 tokens
    thinking). Tokens not used cost nothing."""
    kwargs = dict(model=model_name(), messages=messages, max_tokens=max_tokens, temperature=temperature)
    if tools:
        kwargs["tools"] = tools
    if ON_OPENROUTER:
        extra = {"usage": {"include": True}}
        if web:
            # OpenRouter's web search, with the engine named so the price is
            # known (Exa: about $0.004 per search of five results, plus tokens).
            extra["plugins"] = [{"id": "web", "engine": "exa", "max_results": 5}]
        kwargs["extra_body"] = extra
    elif web:
        raise SystemExit("Web search needs OpenRouter. Switch with: bash 00_setup/switch_backend.sh openrouter")
    choice = _complete(kwargs)
    if choice.finish_reason == "length" or (not choice.message.tool_calls
                                            and not (choice.message.content or "").strip()):
        # A thinking model's thinking counts against max_tokens, so now and then
        # it runs out of room mid-answer or mid tool request, or finishes thinking
        # and says nothing. One more try, with room to spare.
        kwargs["max_tokens"] = max_tokens * 2
        choice = _complete(kwargs)
        if choice.finish_reason == "length":
            # Still out of room: say so, rather than pass off half an answer or
            # half a tool request. A tool request whose arguments are complete
            # JSON is kept; one cut off mid-arguments is replaced by a plain
            # message, so the agent stops instead of running a broken request.
            if choice.message.tool_calls and not _arguments_complete(choice.message.tool_calls):
                choice.message.tool_calls = None
                choice.message.content = "[cut off: the model ran out of room while asking for a tool. Run it again.]"
            elif not choice.message.tool_calls:
                choice.message.content = ((choice.message.content or "").rstrip()
                                          + "\n[cut off: the model ran out of room. Ask for a shorter answer.]")
    return choice.message


def _arguments_complete(tool_calls):
    """True when every requested tool call carries arguments that parse as a JSON
    object. Called only after a length cut-off, where empty arguments mean the
    request stopped before they began (every tool in these labs takes one)."""
    for tc in tool_calls:
        args = (tc.function.arguments or "").strip()
        if not args:
            return False
        try:
            if not isinstance(json.loads(args), dict):
                return False
        except ValueError:
            return False
    return True


def _complete(kwargs):
    """One request. Returns the first choice, with any inline thinking removed."""
    response = client.chat.completions.create(**kwargs)
    _record(response)
    choice = response.choices[0]
    if choice.message.content and "<think>" in choice.message.content:
        # Some servers return a model's thinking inline. It is not the answer.
        # An unclosed block (thinking cut off by the length limit) goes too.
        choice.message.content = re.sub(r"<think>.*?(</think>\s*|$)", "", choice.message.content, flags=re.S)
    return choice


def _record(response):
    """Note what one request cost in LAST, and add it to TOTAL."""
    usage = getattr(response, "usage", None)
    extra = getattr(usage, "model_extra", None) or {}
    cost = extra.get("cost")
    message = response.choices[0].message if response.choices else None
    sources = [a.get("url_citation", {}).get("url") for a in (getattr(message, "annotations", None) or [])
               if isinstance(a, dict)] if message is not None else []
    if message is not None and not sources:
        sources = [getattr(getattr(a, "url_citation", None), "url", None)
                   for a in (getattr(message, "annotations", None) or [])]
    LAST.clear()
    LAST.update({"model": response.model, "id": response.id,
                 "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                 "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                 "cost": cost, "sources": [s for s in sources if s]})
    TOTAL["calls"] += 1
    TOTAL["prompt_tokens"] += LAST["prompt_tokens"]
    TOTAL["completion_tokens"] += LAST["completion_tokens"]
    if isinstance(cost, (int, float)):
        TOTAL["cost"] += cost


def ask(prompt: str, system: str | None = None, web: bool = False) -> str:
    """Send one prompt, get the text back. web=True lets the model search the
    web first (OpenRouter only); the pages it used are in LAST["sources"]."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return (chat(messages, web=web).content or "").strip()


def _json_text(text: str) -> str:
    """The first {...} block in a reply, with any code fence removed."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in the reply")
    return text[start : end + 1]


def ask_json(prompt: str, Model: type[BaseModel], system: str | None = None):
    """Send one prompt, get back an instance of Model.

    The model is shown the JSON schema and asked for one object. If the reply
    does not fit the schema, the error is sent back once and the model gets one
    more try. After that the error is raised, so a bad record is never silently
    accepted."""
    schema = json.dumps(Model.model_json_schema(), indent=1)
    rules = (
        "Reply with exactly one JSON object and nothing else: no prose, no code fence. "
        "It must match this JSON schema:\n" + schema
    )
    messages = [{"role": "system", "content": (system + "\n\n" if system else "") + rules},
                {"role": "user", "content": prompt}]
    text = chat(messages).content or ""
    try:
        return Model.model_validate_json(_json_text(text))
    except (ValidationError, ValueError) as err:
        messages += [
            {"role": "assistant", "content": text},
            {"role": "user", "content": f"That did not fit the schema. The error was:\n{err}\n"
                                        "Reply again with exactly one JSON object and nothing else."},
        ]
        text = chat(messages).content or ""
        return Model.model_validate_json(_json_text(text))
