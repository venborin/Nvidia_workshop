# Module 6: Your own tool

The agent from Module 5 can only search the table and read documents. Here you give it one more ability of your own: a short Python function over your data, such as a CSV of readings, a FASTA file or a reference list. You test the function by itself, add it to the agent with one line, and ask a question that only your function can answer. It is the last piece of the day's one program, and it stays in the repository you keep.

About 80 minutes. Folder: `06_project/`. Behind? `bash catchup.sh m6`

## You will be able to

- Write or adapt one Python function with a docstring, and test it on its own before the agent sees it.
- Add it to the agent with one line and get a correct, evidence-bearing answer to a question only that function can answer, with the trace saved.
- Say what the agent does when your tool is given a bad input or a question it cannot answer.

## The idea

A tool is a plain Python function that takes strings and returns a string. The model never runs it. The model reads a description of the tool, asks for it by name with arguments, and `agent.py` runs the function and hands the result back. That description comes from the function's docstring, the text in quotes at the top of a function that says what it does. So the docstring is not a comment for people. It is how the model decides when to use your tool and what to pass it.

`csv_tool.py` is a working tool over `sample_log.csv`, an instrument log. A CSV (comma-separated values) file is a table saved as plain text, one row per line. The tool groups the rows by one column and summarizes a numeric column. Run on its own, it prints what the model will read, then its answers:

```
Use this for any question about the data in sample_log.csv, which is not in the records table. ...
baseline: n=11, mean=21.3, sd=0.54, min=20.6, max=22, skipped=1 (blank or not a number)
heated: n=12, mean=35.1, sd=1.1, min=33.6, max=37.7
```

Two habits matter more than anything clever. First, test the function alone. If it is wrong on its own, the agent will be wrong with confidence. Second, return the evidence, not a verdict: counts and numbers the answer can be checked against. The model can only reason over what the tool returns, so a tool that hides why it matched invites a wrong answer. A small tool that is correct beats an impressive answer that nothing supports.

## Predict first

Write down, before any code: what your function takes, what it returns, and the one test you will run on it before the agent sees it. Write down what that test should print. Then read your pair's notes and ask one question about them.

## Do it

1. Test the supplied tool on its own. No model is involved.

   ```
   python 06_project/csv_tool.py
   ```

   You should see the docstring, then every group, one group, and a bad input. For example:

   ```
   a bad input:
   no group named 'no such group'; the groups are baseline, cooled, heated
   ```

   That last line is deliberate. A tool that explains what went wrong lets the agent recover.

2. Open `06_project/starter.py` and find the two lines that matter: the import of your function and the `tools=[...]` list.

   ```
   from csv_tool import summarize_csv                  # noqa: E402  <- or your own function
   ...
   answer, messages = run(question, tools=[search_records, read_document, summarize_csv])
   ```

3. Run the agent on its default question.

   ```
   python 06_project/starter.py
   ```

   For example:

   ```
   [turn 1] model asks for summarize_csv(group='all')
   [turn 1] summarize_csv returned: baseline: n=11, mean=21.3, sd=0.54, min=20.6, max=22, skipped=1 (blank or not a number)
   ...
   - Baseline mean: 21.3
   - Heated mean: 35.1
   trace saved to .../06_project/trace.json
   ```

4. Make the two marked edits in `06_project/csv_tool.py` so the tool reports by sensor instead of by condition. Change `GROUP_COLUMN` in EDIT 1 and the sentence in EDIT 2:

   ```
   GROUP_COLUMN = "sensor"
   QUESTION_IT_ANSWERS = "the instrument log: count, mean and spread of the readings from each sensor (S1, S2, S3), all conditions together"
   ```

   Test it on its own again.

   ```
   python 06_project/csv_tool.py
   ```

   For example:

   ```
   S1: n=12, mean=22.7, sd=9.9, min=11.1, max=36.6
   S2: n=11, mean=23, sd=11, min=10.8, max=37.7, skipped=1 (blank or not a number)
   ```

   Check one number by hand: open `sample_log.csv` and count the S2 rows. There are 12, and one of them has no reading.

5. Ask the agent a question only your tool can answer.

   ```
   python 06_project/starter.py "Does every sensor in the instrument log have the same number of readings? Give the counts."
   ```

   For example:

   ```
   [turn 1] model asks for summarize_csv(group='all')
   ...
   - Sensor S2: 11 readings
   ```

## Checkpoint

By 3:30: show your pair your function's own test output from step 4 (or from Exercise 1), and the `[turn ...] model asks for ...` line where the agent chose your tool. Point to the line of tool output that each number in the answer came from. If you are pairing on one keyboard, swap here.

## Exercises

1. Core. Point the tool at a CSV of your own in `mine/`. Drag one onto the `mine/` folder, or use this invented growth assay: three bacterial strains, three replicate cultures each, with OD600 read 24 hours after inoculation. OD600 is optical density at 600 nm, the usual measure of how much a culture has grown. Right-click `mine/` in the file tree, choose **New File**, name it `growth.csv`, and paste these ten lines:

   ```
   strain,replicate,od600
   wild_type,1,0.82
   wild_type,2,0.79
   wild_type,3,0.85
   mutant_A,1,1.12
   mutant_A,2,1.05
   mutant_A,3,NA
   mutant_B,1,0.41
   mutant_B,2,0.38
   mutant_B,3,0.44
   ```

   In `csv_tool.py`, set EDIT 1 to `CSV_FILE = HERE.parents[2] / "mine" / "growth.csv"`, `GROUP_COLUMN = "strain"` and `VALUE_COLUMN = "od600"`, and rewrite EDIT 2 to say what the data is and what it answers. Run `python 06_project/csv_tool.py` until the counts match what you see in the file (does `NA` count?). Then ask the agent a question only this file can answer, for example `python 06_project/starter.py "In my growth assay, which strain grew best after 24 hours, and by how much over the wild type? Give the numbers."` Look for your tool in the `[turn ...]` lines and the numbers in the answer.

2. Stretch (optional). Wire in the FASTA reader. FASTA is the plain-text format for DNA and protein sequences: a `>` header line, then the sequence. GC content is the share of bases that are G or C. This reader handles DNA only. Test it alone with `python 06_project/starters/fasta_tool.py`. In `starter.py`, remove the `# ` from the line `# from starters.fasta_tool import describe_sequences` and add `describe_sequences` to the `tools=[...]` list. Ask `python 06_project/starter.py "Which of my sequences has the highest GC content, and how long is it?"` and check the answer against the tool's own test output. Each starter reads one layout, described at the top of its file. A file of yours in another layout gets an error message or a note about skipped lines, not a summary; changing the reading code to fit is part of the work.

3. Stretch (optional). Wire in the BibTeX reader the same way. BibTeX is the plain-text reference-list format LaTeX uses, one `@article{...}` entry per reference; this reader accepts the one-field-per-line layout most reference managers export. Then test `python 06_project/starters/bibtex_tool.py`, uncomment `from starters.bibtex_tool import find_references`, add `find_references` to the list, and ask `python 06_project/starter.py "Which papers in my reference list did Okafor co-author, and in what years?"` Look at what the tool returns for each match. Would the answer still be right if the tool printed only the first author?

4. Stretch (optional). Wire in the potentiostat log parser. A potentiostat is an electrochemistry instrument that sets a voltage (potential) and measures the current that flows; a saturated reading (flag `sat`) is one that hit the top of the instrument's range. Then test `python 06_project/starters/log_tool.py`, uncomment `from starters.log_tool import log_summary`, add `log_summary` to the list, and ask `python 06_project/starter.py "In the potentiostat log, which channel had a saturated reading, and at what time?"`

5. Stretch (optional). Give your tool a bad input through the agent: ask about a group your file does not have. Use whichever fits your tool now: a condition the log does not have (with the supplied tool), a sensor such as S9 (after step 4), or a strain you did not type (after Exercise 1). With the supplied tool:

   ```
   python 06_project/starter.py "Using the instrument log, what was the mean reading under the frozen condition?"
   ```

   The model can take either of two paths, and both are fine. It may send the bad name to your tool: look for a `returned: no group named ...` line, then see what it did next. Or it may ask for `all` and notice the group is missing from the list. Either way, check that the answer says plainly that the data does not cover it. To see your tool's own error message whatever the model does, call it directly:

   ```
   python -c "import sys; sys.path.insert(0, '06_project'); from csv_tool import summarize_csv; print(summarize_csv('frozen'))"
   ```

6. Stretch (optional). Ask a question your tool should refuse: one about the same data that it cannot answer, because it returns summaries, not single rows. Ask for one row of your file, by time, replicate or id. With the supplied tool:

   ```
   python 06_project/starter.py "Using the instrument log, exactly what did sensor S2 read at 11:00?"
   ```

   Count the turns before the agent answered, and note which tools it tried. It may run out of turns instead (`Stopped: the turn limit was reached`); that is a result too, so write down which tools it kept asking for. If it did answer, write down whether the answer is true of the file or only true of the tool.

7. Stretch (optional). Wire in the citation checker. A model asked for sources can write references that look right and do not exist, or attach a real DOI to the wrong paper; this tool looks each citation up in Crossref, the public catalogue of journal DOIs, and compares the title, first author and year. Test it alone with `python 06_project/starters/citation_tool.py`: it checks `sample_citations.txt`, a test bibliography with deliberate mistakes, and prints one verdict per line with the record it found. In `starter.py`, remove the `# ` from `# from starters.citation_tool import check_citation`, add `check_citation` to the `tools=[...]` list, and ask `python 06_project/starter.py "Check every citation in 06_project/starters/sample_citations.txt and tell me which ones I can trust."` Set `CROSSREF_MAILTO` to your own email address to identify yourself to Crossref; a shared address shares one rate limit. Notice what a match does and does not show. A record that matches proves the paper exists, not that it says what it was cited for, and a citation Crossref cannot find is not proof of invention, since arXiv preprints and datasets are registered elsewhere.

Optional: `bash gallery.sh` posts a card about your site, now with your question, your tool and one result someone could check, to the show-and-tell wall, as a public GitHub issue on the workshop repository. You see the card in full before anything is posted, and you click Submit yourself.

## What you have now

A repository you own, with a working agent and your own tool in it: `06_project/csv_tool.py` (or a starter) tested on its own, the one line in `starter.py` that adds it, and a saved trace in `06_project/trace.json`. Two habits carry beyond today: test a tool alone before the model sees it, and write its docstring for the model. When the workshop key stops working, `followon/continue.md` shows how to point the same code at another endpoint, and `followon/` has the next steps.

## If something goes wrong

- `bash catchup.sh m6` restores all of `06_project/`, and the Module 4 and 5 tool files it uses, from the repository. It first copies your current versions to `mine/catchup-backup-<date-time>/`; copy back what you need from there, for example `cp mine/catchup-backup-*/06_project/csv_tool.py 06_project/`.
- The tool prints `error: no column named ...`: the name in EDIT 1 must match the CSV header exactly, including capitals. The message lists the real columns.
- The tool prints `error: no numbers in column ...` or `error: no file at ...`: `VALUE_COLUMN` names a column of text, or `CSV_FILE` points at the wrong place. A file in `mine/` is `HERE.parents[2] / "mine" / "name.csv"`.
- The agent never asks for your tool, or searches the records table first: the docstring does not say what kind of question the tool answers. Rewrite EDIT 2 (or the starter's docstring) to name the data, and name it in your question too.
- `NameError` when you run `starter.py`: a function is in the `tools=[...]` list but its import line still starts with `#`. The reverse, an import with the name left out of the list, gives no error; the agent simply never sees the tool.
