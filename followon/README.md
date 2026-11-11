# Follow-on: going further on your own

Nothing here is for the workshop day. Start with continue.md, which is the one you need on Thursday morning: how to keep everything running on your own key, the two tasks the day left for Thursday, and which of the day's helpers to adapt for your own work.

- continue.md: Thursday morning. Your own key in two lines, the inferential question on your own data, scheduling the digest, each stop's helper as a thing to adapt, and asking the HPCC about Cimarron.
- old-modules/: the first version of the day, six modules on calling a model from Python, improving a prompt against a score, structured output with evidence, a tool, and the loop that calls it. The tour moves through these quickly; here they are step by step. Its README says how to run them.
- openclaw/: OpenClaw, the full agent program you used at Stops 1, 2, 3, 5 and 6, for comparison with the forty-line loop in `agent.py`.

For the old modules, in roughly increasing order of effort:

- own-record.md: write your own Record from scratch for a different kind of document.
- write-the-loop/: write the tool-calling loop yourself from a fill-in-the-blanks version, then compare with agent.py.
- concurrency.md: run the folder script over hundreds of documents at once.
- embeddings.md: replace keyword search with meaning-based search.
- public-api.md: look up references through a public API as a tool. Stop 3's `03_lit/lit.py` is a finished example.
- frameworks.md: the same agent in a popular framework, and what you give up.

Two free resources outside this repository. NVIDIA's Generative AI Teaching Kit lectures 8.1 to 8.3 (LLM components, retrieval, agents) are the theory behind the workshop, as free lecture videos linked from https://developer.nvidia.com/gen-ai-teaching-kit-syllabus. Two self-paced DLI courses, Building RAG Agents with LLMs and Evaluating RAG and Semantic Search Systems, are the next step after the old Module 5 (`old-modules/05_agent/`); faculty who join the DLI Teaching Kit program at https://developer.nvidia.com/teaching-kits are eligible for free codes for themselves and their students.
