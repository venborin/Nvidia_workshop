# Module 4: Giving the model a tool

This morning the model wrote a table from your documents. Now it gets to search that table before it answers, so an answer can point to the rows it came from instead of to the model's memory. You will watch one exchange step by step, then ask your own question with the tool and without it and compare.

About 50 minutes. Folder: `04_tool/`. Behind? `bash catchup.sh m4`

## You will be able to

1. Say what happens, in order, when the model uses a tool: what the model asked for, what Python ran, and what evidence came back.
2. Compare one question asked with the tool and without it, and check which claims in each reply you can trace to a row of the table. An honest "I cannot see the table" is a valid result.
3. Show a question the table cannot answer, and say from the trace whether the model said so or filled the gap.

## The idea

A tool is an ordinary Python function that the model is allowed to ask for. Yours is `search_records(query)` in `04_tool/tools.py`. It does a plain word search: it keeps every row of the table that contains any of the words you give it, ignoring capitals and common words such as "the" or "which", puts the rows that match more of the words first, and says which words each row matched. That is deliberately generous. The search finds candidates; deciding which of them actually answer the question is the model's job, and that is what you are judging. Its docstring (the text in triple quotes under the `def` line) tells the model what it does and when to use it. `describe()` in `agent.py` turns the name, the parameter and the docstring into a short description that travels with the question.

The model never runs anything. It cannot see the table and cannot execute code. What it can do is reply with a request instead of an answer: call this function, with this argument. Your program runs the function, puts the result in a message from the tool, and sends the whole conversation back. When the model replies in words, the loop stops. The loop is `run()` in `agent.py`, supplied. Read the sequence; you do not need every line.

The program saves the conversation as a trace, `04_tool/trace.json`. Each message in it has a role, meaning who it is from: `system`, `user`, `assistant` (the model) or `tool`. A request looks like this, shortened:

```
"role": "assistant",
"content": "",
"tool_calls": [{"function": {"name": "search_records", "arguments": "{\"query\": \"pizza\"}"}}]
```

The empty content is the point: no answer yet, only a request.

So every trace can be read with three questions. What did the model ask for? What did Python run? What evidence came back? The tool makes an answer checkable, not automatically right: you still compare its doc ids and numbers with what came back.

## Predict first

The model will be asked the same question about the table twice, with the same instructions, once with a search tool and once without. Will the evidence improve the answer, and how will you tell? Write it down.

## Do it

1. Test the tool on its own, before the model ever sees it. It searches your Module 3 table, `03_table/records.jsonl`, when that has usable rows, and the saved table `corpus/records.jsonl` when it does not, with a one-line note saying so.

    ```bash
    python 04_tool/tools.py
    ```

    You should see the rows that contain "pizza", one per line, each ending with the words it matched. For example:

    ```
    {"doc_id": "doc_001", "title": "Free Pizza Increases Office Hours Attendance in Introductory Statistics", "year": "2021", "method": "experimental", "sample_size": "236 students", "main_claim": "Free pizza increased office hours attendance by 85 percent.", "matched": ["pizza"]}
    {"doc_id": "doc_002", "title": "Pooled Reanalysis of Pizza Incentive Studies in Office Hours Attendance", ...}
    ```

    No model was involved. This is plain Python. If your Module 3 table came from your own documents, it has no pizza, so run the demo on the saved table instead; `--saved` searches it and leaves your table untouched:

    ```bash
    python 04_tool/tools.py --saved
    ```

2. Run the starter with the demo question. Add `--saved` if you used it in step 1.

    ```bash
    python 04_tool/starter.py
    ```

    The program prints each step as it happens: the request, what the function returned, then the answer. For example:

    ```
    [turn 1] model asks for search_records(query='pizza')
    [turn 1] search_records returned: {"doc_id": "doc_001", "title": "Free Pizza Increases Office Hours Attendance in Introductory Statistics", ...

    [answer]
    The studies that tested pizza in the table are **doc_001**, **doc_002**, **doc_003**, and **doc_004**.

    They did **not** agree about its effect:
    ...
    trace saved to /workspaces/.../04_tool/trace.json
    ```

3. Open the trace from the file tree, or with this command:

    ```bash
    code 04_tool/trace.json
    ```

    It is a list of messages. For example, the first lines:

    ```
    [
     {
      "role": "system",
      "content": "You are a careful research assistant. Use the tools to find evidence before answering. ...
    ```

    Open `04_tool/trace.md` beside it. That is the same exchange from an earlier run, annotated message by message.

## Checkpoint

In your own `trace.json`, point your pair to the message where the model asked for a tool and the `tool` message that answered it. Say the three answers out loud: what it asked for, what Python ran, what came back.

## Exercises

1. Core: read the trace in pairs. Take two minutes each way with `04_tool/trace.md` and your own `04_tool/trace.json`. One of you answers the three questions while the other checks them against the file. Then check the answer: does every doc id it cites appear in the `tool` message? Open `corpus/` and look for a study of office hours attendance that the search did not return. If there is one, why did the search miss it?

2. Core: ask your own question, with the tool and without it. Both runs get the same instructions; only the tool differs.

    ```bash
    python 04_tool/starter.py "your question"
    python 04_tool/starter.py --no-tool "your question"
    ```

    The tool searches whatever table Module 3 left in `03_table/`: the sample corpus, or your own documents if you ran `python 03_table/run_folder.py mine`. Ask a question that table could answer. For each reply, mark which claims you can find in a row of the table and which you cannot. If the reply without the tool names sources, can you find them in `corpus/`? A reply that says it cannot see the table is honest, and counts. Write one sentence about what changed.

3. Core: ask a question the table cannot answer, one about something no column records. For example, ask about funding, or about a field none of the documents covers.

    ```bash
    python 04_tool/starter.py "your question the table cannot answer"
    ```

    Count the searches. Check whether `trace.json` has a `user` message you did not write; `04_tool/trace.md` says what it means when it is there and when it is not. Does the final answer say what the evidence does not establish, or does it fill the gap anyway?

4. Stretch (optional): give the model more evidence. In `04_tool/tools.py`, change `search_records` so each hit also includes the record's `excerpt`, the sentence copied from the document in Module 3. Update the docstring so the model knows the field is there. Test the function alone first, then ask a question that needs the supporting sentence.

    ```bash
    python 04_tool/tools.py
    python 04_tool/starter.py "Which pizza study found no effect, and what sentence supports that? Cite doc ids."
    ```

    Does the model quote the excerpt? Search the source file in `corpus/` for the quoted sentence: is it there word for word?

## What you have now

- `agent.py`, the supplied loop, now used with one tool, and a sense of the order of events in it.
- `04_tool/tools.py`, a working tool you have tested on its own, possibly with the excerpt added.
- `04_tool/trace.json`, a saved trace of a question you asked.
- The three questions for any trace: what the model asked for, what Python ran, what evidence came back. Module 5 adds a second tool and uses them on a harder question.

## If something goes wrong

- The search returns `no matches` for something you know is in the table. None of the query's words appear in any row, often because the table uses a different word ("attendance" where you wrote "turnout"). Test words on their own with `python 04_tool/tools.py attendance`.
- The search returns rows that are not about your question. It matches any word, so the pizza studies come back for a question about pizza funding, and a flood simulation whose row mentions "6 hours" comes back for a question about office hours. Look at `matched` in each row: the model is supposed to notice when no row matched the part of the question that matters.
- A `note:` line says your table is missing, has no usable rows, or has rows with errors. The tool is searching the saved table, or skipping the broken rows. To rebuild your table, run `python 03_table/run_folder.py` (add `mine` for your own documents), or `python 03_table/run_folder.py --saved` to replace it with the saved run.
- After the stretch, the starter fails with `SyntaxError` or `NameError`. Run `python 04_tool/tools.py` to see the line. To put the original file back: `git checkout 04_tool/tools.py`.
- The answer is `Stopped: the turn limit was reached before the model answered.` The model kept asking for eight turns. Ask a narrower question, or name the words it should search for.
- The answer stops mid-sentence. The model ran out of room even after the helper's automatic retry. Run the same command again.
