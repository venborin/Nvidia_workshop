"""The tool-calling loop. Supplied, about forty lines of real work; read it, do
not rewrite it. Module 4 explains the sequence of what happens and who decides
each step.

    from agent import run
    run("Which studies tested pizza?", tools=[search_records])

A tool is an ordinary Python function that takes strings and returns a string,
with a docstring. The adapter below turns its name, parameters and docstring
into the description the model sees. The model never runs anything: it asks
for a tool by name with arguments, this program runs the function, and the
result goes back to the model as a message from the tool. The loop stops when
the model answers in words or when the turn limit is reached.
"""
import inspect
import json

from llm import chat

MAX_TURNS = 8


def describe(fn):
    """What the model sees for one tool: name, docstring, string parameters."""
    params = inspect.signature(fn).parameters
    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": inspect.getdoc(fn) or fn.__name__,
            "parameters": {
                "type": "object",
                "properties": {p: {"type": "string"} for p in params},
                "required": list(params),
            },
        },
    }


def run(question, tools, system=None, show=True, max_turns=MAX_TURNS):
    """Ask the question, let the model use the tools, return the final answer.
    The whole exchange is returned as well, so a trace can be saved."""
    by_name = {fn.__name__: fn for fn in tools}
    messages = [{"role": "system", "content": system or (
        "You are a careful research assistant. Use the tools to find evidence before answering. "
        "Cite the doc_id of every record you rely on. If a search finds nothing, try one different "
        "query, then stop searching and say plainly that the evidence does not establish an answer.")},
        {"role": "user", "content": question}]

    rut = 0
    for turn in range(max_turns):
        reply = chat(messages, tools=[describe(fn) for fn in tools])

        if not reply.tool_calls:                       # the model answered in words
            answer = (reply.content or "").strip()
            if not answer:                             # some models think and then say nothing
                messages.append({"role": "user", "content": "Answer now, in words, from the evidence so far."})
                answer = (chat(messages).content or "").strip() or "(the model returned no text)"
            messages.append({"role": "assistant", "content": answer})
            if show:
                print(f"\n[answer]\n{answer}")
            return answer, messages

        # The model asked for one or more tools. Record the request exactly as
        # the API expects it back, run each function here, and send every
        # result back as a tool message.
        messages.append({"role": "assistant", "content": reply.content or "", "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
            for tc in reply.tool_calls]})
        empty_results = 0
        for tc in reply.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if show:
                print(f"[turn {turn + 1}] model asks for {name}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
            if name in by_name:
                try:
                    result = str(by_name[name](**args))
                except Exception as err:               # the tool failed; the model is told, not crashed
                    result = f"error from {name}: {err}"
            else:
                result = f"error: no tool named {name}"
            if show:
                preview = result if len(result) <= 300 else result[:300] + " ..."
                print(f"[turn {turn + 1}] {name} returned: {preview}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            if result.startswith(("no matches", "no ", "error")):
                empty_results += 1

        # The program, not the model, notices a rut: two turns in a row where
        # every tool came back empty, and the model is told to change approach.
        rut = rut + 1 if empty_results == len(reply.tool_calls) else 0
        if rut >= 2:
            messages.append({"role": "user", "content":
                             "That tool keeps returning nothing for this. Use a different tool if one fits, "
                             "or answer now and say what the evidence does not establish."})
            rut = 0

    answer = "Stopped: the turn limit was reached before the model answered."
    messages.append({"role": "assistant", "content": answer})
    if show:
        print(f"\n[answer]\n{answer}")
    return answer, messages


def save_trace(messages, path):
    """Write the exchange as readable JSON, one message per entry."""
    with open(path, "w") as f:
        json.dump(messages, f, indent=1)
    print(f"trace saved to {path}")
