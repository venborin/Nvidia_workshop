"""Print a saved trace as a short list you can read in a minute. No model call.

    python 05_agent/show_trace.py                                       your last run
    python 05_agent/show_trace.py 05_agent/trace-planted.json           a copy you kept
    python 05_agent/show_trace.py 05_agent/failures/stopped-early.json  a saved failure

Each line is one message in the exchange: the question, each tool the model
asked for, a one-line summary of what came back, and the answer. The last
lines count what the agent found and what it read, so you can judge its
choices without scrolling through whole documents. A read counts only when the
document came back; a cut-off read is listed separately.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def short(text, n=110):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n] + " ..."


def parse_args(raw):
    """The arguments of one tool call as a dict, or None if they are not a JSON object."""
    try:
        args = json.loads(raw or "{}")
    except (json.JSONDecodeError, TypeError):
        return None
    return args if isinstance(args, dict) else None


def add(seq, item):
    if item not in seq:
        seq.append(item)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "trace.json"
    if not path.exists():
        raise SystemExit(f"No trace at {path}. Run  python 05_agent/starter.py  first.")
    try:
        messages = json.loads(path.read_text())
    except json.JSONDecodeError as err:
        raise SystemExit(f"{path} is not a saved trace: {err}")

    searches, found = [], []
    reads = {"read": [], "cut off": [], "failed": []}
    pending = []                 # (call id, name, args) in the order the model asked
    questions = 0
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            continue
        role, content = m.get("role"), str(m.get("content") or "").strip()
        if role == "system":
            print(f"{i:2}  system      {short(content, 90)}")
        elif role == "user":
            questions += 1
            label = "question" if questions == 1 else "program"   # later user messages come from the loop
            print(f"{i:2}  {label:<11} {short(content, 200)}")
        elif role == "assistant" and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                fn = tc.get("function") or {}
                name = fn.get("name", "?")
                args = parse_args(fn.get("arguments"))
                pending.append((tc.get("id"), name, args))
                if args is None:
                    print(f"{i:2}  model asks  {name} with arguments that are not a JSON object: {short(fn.get('arguments'), 60)}")
                    continue
                print(f"{i:2}  model asks  {name}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
                if name == "search_records":
                    searches.append(str(args.get("query", "")))
        elif role == "tool":
            # Match the result to its request by call id; fall back to the oldest open request.
            idx = next((k for k, p in enumerate(pending) if p[0] == m.get("tool_call_id")), 0 if pending else None)
            name, args = (pending.pop(idx)[1:] if idx is not None else ("tool", None))
            doc_id = str((args or {}).get("doc_id", "")).strip()
            ids = re.findall(r'"doc_id":\s*"([^"]+)"', content)
            if name == "search_records" and ids:
                for d in ids:
                    add(found, d)
                summary = f"{len(ids)} record{'s' if len(ids) != 1 else ''}: {', '.join(ids)}"
            elif name == "read_document":
                if content.startswith("error"):
                    add(reads["failed"], doc_id or "?")
                    summary = short(content, 90)
                else:
                    cut = "[truncated" in content
                    add(reads["cut off" if cut else "read"], doc_id or "?")
                    summary = f"{content.splitlines()[0] if content else '(empty)'} ({len(content.split())} words{', cut off' if cut else ''})"
            else:
                summary = short(content, 90)
            print(f"{i:2}    returned  {summary}")
        elif role == "assistant":
            print(f"{i:2}  answer\n\n{content}\n")
        else:
            print(f"{i:2}  {str(role):<11} {short(content, 200)}")

    print(f"searches:            {len(searches)}  {searches}")
    print(f"found by a search:   {', '.join(found) or 'none'}")
    print(f"read in full:        {', '.join(reads['read']) or 'none'}")
    if reads["cut off"]:
        print(f"read, but cut off:   {', '.join(reads['cut off'])}")
    if reads["failed"]:
        print(f"read failed:         {', '.join(reads['failed'])}")
    opened = reads["read"] + reads["cut off"]
    print(f"found but not read:  {', '.join(d for d in found if d not in opened) or 'none'}")


if __name__ == "__main__":
    main()
