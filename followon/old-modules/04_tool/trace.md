# One trace, annotated

A trace is the saved conversation: every message the program and the model sent each other, in order, in `04_tool/trace.json`. Each message has a role, which says who it is from: `system` (the program's standing instructions), `user` (the question), `assistant` (the model), or `tool` (a function's result).

This is the exchange behind `python 04_tool/starter.py`, recorded on November 1 against a Nemotron model, with a note on each message. Your own trace has the same shape; the model's wording will differ. Read it with three questions in mind: what did the model ask for, what did Python run, what evidence came back.

## Message 1, from the program (system)

```
"role": "system",
"content": "You are a careful research assistant. Use the tools to find evidence before answering. Cite the doc_id of every record you rely on. If a search finds nothing, try one different query, then stop searching and say plainly that the evidence does not establish an answer."
```

The program wrote this: `SYSTEM` in `04_tool/starter.py`, the same text `agent.py` uses by default. Alongside the messages, but not saved in the trace, the program sends a description of each tool: its name, its docstring, and its one string parameter, `query`. `describe()` in `agent.py` reads that description off the function in `04_tool/tools.py`. It is all the model ever knows about the tool.

## Message 2, from the person (user)

```
"role": "user",
"content": "Which studies in the table tested pizza, and did they agree about its effect? Cite doc ids."
```

## Message 3, from the model (assistant): a request, not an answer

```
"role": "assistant",
"content": "",
"tool_calls": [{"id": "chatcmpl-tool-a70c814bc8fc19d1", "type": "function",
                "function": {"name": "search_records", "arguments": "{\"query\": \"pizza\"}"}}]
```

The content is empty: there is no answer here, only a request to run a function named `search_records` with an argument the model chose. The model has not seen the table and cannot run anything. On screen this is the line `[turn 1] model asks for search_records(query='pizza')`.

## Message 4, from the tool

```
"role": "tool",
"tool_call_id": "chatcmpl-tool-a70c814bc8fc19d1",
"content": "{"doc_id": "doc_001", "title": "Free Pizza Increases Office Hours Attendance in Introductory Statistics", "year": "2021", "method": "experimental", "sample_size": "236 students", "main_claim": "Free pizza increased office hours attendance by 85 percent.", "matched": ["pizza"]}
            {"doc_id": "doc_002", ...}
            ..."
```

Python ran `search_records` with that argument. It is a plain word search: it keeps every row that contains any of the query's words, ignoring capitals and common words, puts rows matching more words first, and adds a `matched` list to each row. It is generous on purpose, so the question is what the model does with what comes back. It searched `03_table/records.jsonl` if you built it in Module 3, or the saved `corpus/records.jsonl` if not. Each matching row came back as one line of text (in `trace.json` the inner quotes are escaped as `\"`). The program put that text into a message with the role `tool` and the same id as the request it answers, then sent the whole conversation back to the model and asked again.

## Message 5, from the model (assistant): the answer

```
"role": "assistant",
"content": "The studies that tested pizza in the table are **doc_001**, **doc_002**, **doc_003**, and **doc_004**.

They did **not** agree about its effect:
- **doc_001** (experimental, 236 students) found that free pizza increased office‑hours attendance by 85 percent.
...
Because some studies show a positive effect, one shows no effect, and another shows an effect only under certain conditions (dose‑dependent), the evidence on pizza’s effect is inconsistent. ..."
```

Text this time, no tool request, so the loop in `agent.py` stops and prints it under `[answer]`. Whether the answer is grounded is something you check, not something the tool guarantees: compare each doc id and number in it with message 4, and each row with its source file in `corpus/`.

## Two other things you may see in your own trace

A `user` message you did not write, beginning "That tool keeps returning nothing for this." `agent.py` adds it after two turns in a row where every search came back empty. It is a nudge, not a stop: the model may answer next, or search again. If your trace has no such message, the model answered before two empty turns in a row.

The answer "Stopped: the turn limit was reached before the model answered." That is the only forced stop. After eight turns of requests, `agent.py` ends the loop whatever the model wants.

Without the tool, `python 04_tool/starter.py --no-tool` sends message 1 and message 2 with no tool description, so the model can only answer from memory. Nothing is saved; the reply is printed.
