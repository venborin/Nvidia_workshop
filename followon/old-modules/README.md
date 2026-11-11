# The first version of the day

These six modules were the workshop's plan until November 6, when the day became a tour of what an agent can do on your own files. They still work, and they teach the parts the tour moves through quickly: calling a model from Python, improving a prompt against a score, structured output with an excerpt for every claim, a tool, and the loop that calls it.

Run each one from the top folder of your repository, with this folder's path in front. For example:

```
python followon/old-modules/01_tour/starter.py
python followon/old-modules/04_tool/starter.py
```

The commands inside each README are written as they were on the day (`python 04_tool/starter.py`); add `followon/old-modules/` in front. Module 3, the evidence table, stayed in place at `03_table/`, and Stop 3 builds on it. Behind on one of them: `bash catchup.sh m4` (or m1 to m6).

- `01_tour/`: one line of Python sends a document to the model; six jobs side by side.
- `02_prompts/`: improve a labeling prompt one change at a time, scored on ten labeled documents.
- `04_tool/`: the model asks for a search over the table; read the exchange step by step.
- `05_agent/`: two tools and a loop on a literature question, and a document that tries to give orders.
- `06_project/`: your own tool over your own data, added to the agent with one line.
