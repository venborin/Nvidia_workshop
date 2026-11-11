# Two traces from the dry run, for reference

These are saved exchanges from runs that went wrong in a way the answer alone would not show. Exercise 4 in `05_agent/README.md` uses the first one. Print either with `show_trace.py`; it makes no model call.

## stopped-early.json

The question asked the agent to summarize what the copper zeolite documents conclude about stability under thermal cycling, and to read each one. The trace was saved before the search changed on November 1. A query then had to appear word for word in a record; now a record matches any of the query's words, so the same first search finds more.

```
python 05_agent/show_trace.py 05_agent/failures/stopped-early.json
```

Things to look at: each search query and how many records it returned, which documents were read, and how many copper zeolite documents the corpus holds (the corpus README lists the clusters). Then read the answer and ask what a reader who saw only the answer would believe about the collection.

## rut.json

A question about an instrument log, asked when the tools on offer were `search_records`, `read_document` and a CSV summarizer. The run did not finish, so this trace is reconstructed from its printed output.

```
python 05_agent/show_trace.py 05_agent/failures/rut.json
```

Things to look at: what the agent kept doing, what the last request was, and which tool it never tried. Then read the block in `agent.py` that begins "The program, not the model, notices a rut".
