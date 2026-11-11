# Stop 6: Build one thing from your week

This morning you made things once: an analysis, a table of values from papers, a chart read into data. Now you turn one of them into a small tool you can run again next week. You pick a recipe that already runs, change it with the agent, and test it on input it has never seen. You leave with a program, not a chat.

About 95 minutes, from 2:25. You type requests in the OpenClaw chat and run your tool in a second terminal. Click any file it makes to open it.

## You will be able to

- Turn something you did once into a program that runs with one command.
- Test it on new input and on bad input, and say what it did with each.
- Keep it: the code, a sample, the command, and your own key.

## Pick one recipe (if unsure, the first)

Each recipe has a starter that already works, a bad input to test it with, and an unseen input for the swap at 3:15. Bad inputs write beside your good results, never over them.

### 1. Documents into a table

A folder of documents you read every week becomes a table with the columns you choose. Every value comes with its quoted sentence, its page, and a check: `yes` (the quote is in the document), `NO` (it is not), `not stated`, or `UNSUPPORTED` (no quote at all).

```
python 06_build/table/build_table.py corpus/papers
```

- Your columns are in `06_build/table/fields.json`: a name and one sentence each. The table is `results/build/table.csv`.
- Bad input: `python 06_build/table/build_table.py 06_build/table/bad --out results/build-bad`
- Unseen input at 3:15: `python 06_build/table/build_table.py 06_build/table/interviews --out results/build-unseen` (three invented interviews, with your partner's columns). A column that does not fit an interview should say `not stated`, not invent a value.

### 2. Your Stop 2 analysis as a web page

Your report and plot become one web page you can email or post. It refuses to build if the report has a number the script never printed.

```
python results/analysis.py > results/analysis-output.txt
python 06_build/page/make_page.py --title "Air handler"
```

- The page is `results/page/index.html`. To see it, right-click it in the Explorer, Download, and open it on your laptop.
- No `results/analysis.py`? Run `cp 06_build/page/from_reference.py results/analysis.py` first.
- Bad input: `python 06_build/page/make_page.py --from 06_build/page/bad --out results/page-bad` (it must say NOT WRITTEN).
- Unseen input at 3:15, two commands:

  ```
  python 02_data/datasets/stillwater-weather/reference/analysis.py > results/weather-output.txt
  python 06_build/page/make_page.py --from 02_data/datasets/stillwater-weather/reference --output results/weather-output.txt --out results/page-weather --title "Stillwater weather"
  ```

### 3. What is new on your topic

A script that lists papers on your topic that it has not shown you before, each checked against the publishers' registry.

```
python 06_build/digest/digest.py
```

- As it comes, it searches for cover crops and soil carbon. Your own topic: `python 06_build/digest/digest.py "your topic in a few words"`.
- To keep your topic, put it in `QUERY` near the top of `06_build/digest/digest.py`. Each run writes a new `results/digest-<date>.md`.
- Bad input: `python 06_build/digest/digest.py --records 06_build/digest/fixtures/no-match.json` (it must say nothing matches).
- Unseen input at 3:15: your partner's topic. They tell you; you type it.

Something else in mind? Click `06_build/IDEAS.md` for examples by field. Your own idea is fine if a helper agrees it fits in an hour.

## Do it

1. Run the starter as it is, in the second terminal. It works before you change anything.

2. Change it with the agent. In the chat, type `/new` and press Enter. Then say what you want, for example:

   ```
   Read 06_build/table/build_table.py and 06_build/table/fields.json. Change the columns to: study site, soil depth sampled, years of the experiment, and the main result. Run it on corpus/papers.
   ```

   With your own documents in `mine/`, name your own columns and end with `Run it on mine/.` To see exactly what the agent changed, in the second terminal: `git diff 06_build/` (press `q` to leave).

3. Get a first result by 3:15. Then make the comment at the top of your file true: the one command that runs your tool now. Your partner will have nothing else to go on.

4. Swap at 3:15. Trade seats with your partner, so each of you sits at the other's laptop. Nothing is copied or sent: you run their tool where it lives, in their Codespace. Go by that comment alone, with no agent and no explaining: first on the recipe's unseen input, then on its bad input. For each, decide what it did: the right answer, a wrong answer, an honest `not stated` or error, or a crash. Note where the comment left you stuck. Trade back, tell your partner, and fix your comment.

5. Keep it. Five things:
   - the code, saved;
   - a small sample input in a new folder named `sample` beside your code (a shipped file is fine; nothing private, because the repository may be public);
   - the command, and what it prints, in the comment at the top of the file;
   - any library the agent installed, added to `requirements.txt`;
   - your own key after today (below).

   Then, in the second terminal:

   ```
   git add 05_repair 06_build requirements.txt
   git commit -m "my tool, and the repaired script"
   git push
   bash export.sh
   ```

   `git push` keeps the code on GitHub. `bash export.sh` packs `results/` into a zip: right-click it in the Explorer and Download.

6. Show and tell, at 4:00. On your own laptop, show your pair your tool running: on the unseen input, or on something they pick, such as a topic or a column they would want. Then watch theirs. Then volunteers nominate what they saw in their partner's work.

## Checkpoint

Tell your pair what their tool did on the unseen input and on the bad input, and where its comment left you stuck.

## After today: your own key

The workshop key stops at 5:00. Make a key at openrouter.ai (Keys, Create key, with a credit limit), then run `bash setup.sh --reset-key` and paste it. Setup writes these two lines in `.env` for you:

```
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...your key...
```

## If something goes wrong

- The starter fails before you change anything: ask a helper. The page recipe runs without the model, so you can start there meanwhile.
- The agent changed more than you asked: `git checkout 06_build/<file>` puts one file back.
- The page says a number is not in the script's output: run `python results/analysis.py > results/analysis-output.txt` again, then the page command.
- Your documents are scans: the model cannot read a picture of a page. Use the shipped papers.
- Out of time: commit what runs, and write the next step in the comment at the top. A small tool that runs beats a large one that almost does.
