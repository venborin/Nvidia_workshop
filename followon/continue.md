# Thursday morning: keeping this working

The workshop key stops working at the end of the day. From Thursday, typing the workshop word at setup's key prompt prints a message saying so, with what to do instead, and the prompt asks again. Everything you built keeps working the moment you point it at another endpoint, because the only two things the code knows are in .env:

    LLM_BASE_URL=...
    LLM_API_KEY=...

For an OpenRouter key (starts with `sk-or-`) or an NVIDIA key (starts with `nvapi-`), run `bash setup.sh --reset-key` and paste it: setup recognizes the key and picks the endpoint and a Nemotron model itself. For any other endpoint, run `bash setup.sh --reset-key --base-url <url>` and paste its key, or edit .env by hand. Then `python 00_setup/check.py` tells you whether it worked.

`results/` is not in your repository; it was never committed. If you ran `bash export.sh` and downloaded the zip, you have it. If not, do it before you delete the Codespace.

## Two tasks the day left for Thursday

1. The inferential question on your own data. Stop 2 stopped at description on purpose: on your own data, which test, regression or trend model is right is your call, not a one-hour stop's. Write down the question, the model you would defend, and its assumptions, then ask the agent for that analysis and compare it with what you would have done. Each shipped dataset's `02_data/datasets/<name>/reference/extension.py` shows the pattern: one model, its assumptions stated.
2. Schedule the digest. `06_build/digest/digest.py` prints, at the end of its output, the line to add to `crontab -e` to run it every Monday. Cron runs only on a machine that stays on; a Codespace stops when idle, so put it on your own computer or a server you use.

## Each stop's helper, as a thing to adapt

Every stop left a short program behind. Each is a starting point for your own version:

- Stop 2: `results/analysis.py`, your analysis rebuilt from the raw file. Run it on next month's data.
- Stop 3: `03_lit/lit.py` (search OpenAlex, verify DOIs in Crossref, write BibTeX from the records) and `03_lit/pdfask.py` (an evidence table with a quoted sentence and a page behind every value).
- Stop 4: `04_see/see.py` and `04_see/compare.py`, a chart read back into data and checked against the original.
- Stop 5: `05_repair/check_expected.py`, a check the agent cannot edit. Write one like it for a script of yours.
- Stop 6: the three starters in `06_build/` (a folder-to-table tool, a page for a dataset, a literature digest), and the one you built.

## Where to point it

1. Cimarron. Whether the workshop's Cimarron endpoint keeps running after November 11, and for whom, is the HPCC's decision, not a promise this repository makes. Ask them, and ask about an account for your own research computing, at https://hpcc.okstate.edu. The same rule applies there as on the day: the model's work happens on OSU hardware, but your files are wherever you run the code.
2. A hosted endpoint. NVIDIA's hosted models at build.nvidia.com serve the same API: create a free developer account, make an API key, and paste it into `bash setup.sh --reset-key`. OpenRouter (openrouter.ai) serves the same Nemotron models with a pay-as-you-go key that works the same way; give the key a credit limit. Other OpenAI-compatible hosts work the same way; only the URL and key change.
3. Your own laptop. Ollama, LM Studio, and vLLM all serve the same API on localhost. For example, with Ollama running a small model, the base URL is http://localhost:11434/v1 and any non-empty string is the key. The helpers are slower on a laptop and the small models make more mistakes, which is itself instructive. Stop 4 needs a model that reads images.

Your Codespace keeps your files when it is stopped. It is deleted after a retention period you can set at https://github.com/settings/codespaces. The repository itself is yours forever; the Codespace is only a place to run it. To run the labs on your own computer instead: clone the repository, `pip install -r requirements.txt`, write .env, and the same commands work.

The first version of the day, six modules on prompting, structured output and the tool loop, is in `followon/old-modules/` if you want the steps the tour moved through quickly.
