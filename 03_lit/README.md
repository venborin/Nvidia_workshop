# Stop 3: A research question, answered from papers you can check

You give the agent a research question and a few papers: three that come with the workshop, or your own. It pulls out every value the papers report, each with the sentence and page it came from. A checking program confirms every quote, and the agent fixes what the check rejects. Then it works out why the studies disagree, and decides for itself when it is done.

About 75 minutes, from 11:00. You type in the OpenClaw chat and run one command in a second terminal.

## You will be able to

- Get a table of values from papers, each tied to a quote and a page that a program has confirmed.
- Watch an agent react to a check that fails.
- Judge its explanation by the rows behind it.

## Why

A model asked for a number or a reference from memory writes something that looks right, and some of it does not exist. So here the model never has the last word on a fact. Three small programs do: `pages.py` prints a paper's text page by page, `check_values.py` checks that every quote is really on its page and contains its number, and `lit.py` searches for papers and checks each one's DOI (a paper's permanent identifier) against the publishers' registry. What is left for the agent is judgment: which values can be compared, why they differ, and when to stop.

What the check's words mean:

- PASS: the quote is on that page and contains the number. Whether the sentence means what the row says is for you to judge.
- FAIL: the quote is not on that page, or the number is not in the quote. The agent should reread and fix the row.
- FLAGGED: the row failed a check and the agent says why it cannot be fixed.
- verified: the DOI exists and its title and first author match.

## Choose your papers

Bringing papers is optional. Pick one:

- The shipped papers. Three open-access papers on cover crops and soil carbon, in `corpus/papers/`, with the question already written in `03_lit/question.md`. A cover crop is grown between cash crops to protect the soil, and the papers ask how much carbon it adds. Some report a stock (carbon under an area of land, in Mg C/ha) and some a concentration (carbon in a mass of soil, in g/kg or percent); the two cannot be compared without a conversion.
- Your own papers. Two or three PDFs that report the same kind of quantity (a yield, an efficiency, an error rate, a temperature). They must be PDFs you can select text in, not scans. Set them up now:
  1. Drag the PDFs from your laptop onto the `mine` folder in the Explorer.
  2. In the second terminal, run `python upload_check.py`. Each paper should say `ready`. If one does not, leave it out.
  3. Click `03_lit/question-mine.md`. Replace each [BRACKET] with the quantity your papers report, its unit, and the conditions you care about. Save with Cmd-S (Ctrl-S).

  If this takes more than five minutes, start with the shipped papers and come back to yours as Extension 2.

## Do it

1. Start a fresh chat. In the chat, type `/new` and press Enter. (A `$` prompt instead of the chat? Type `openclaw chat`.)

2. Hand it over. Click `03_lit/question.md` to read the question, the checks it must run, and when to stop. Then, in the chat, type:

   ```
   Read 03_lit/question.md and do what it says.
   ```

   With your own papers, type this instead:

   ```
   Read 03_lit/question-mine.md and do what it says.
   ```

3. Watch the loop. It takes several minutes. `pages.py` is the agent reading a paper. `check_values.py` prints PASS, FAIL or FLAGGED for every row: count the failures, then watch what it does about them. `lit.py` is a search: what did it search for, and why?

4. Check one row yourself. Click `results/values.csv` and pick a row that passed. Click that paper's text in `results/papers/`, press Cmd-F (Ctrl-F) and type a few words of the quote. Is it on the page the row says? Does the sentence say what the row says? Hard to read in the editor? Right-click `results/values.csv` in the Explorer, Download, and open it in Excel. Then run the check yourself, in the second terminal:

   ```
   python 03_lit/check_values.py
   ```

5. Read the answer. Click `results/answer.md`. Which rows support each part of the explanation? Was each idea tested against the rows, or only stated?

6. At 12:10, the minute paper. On a slip of paper or a sticky note, with no name, write the main point of the morning in one sentence, and the muddiest point. Hand it in as you leave for lunch. Then choose the Stop 6 recipe you will build after lunch (if unsure, the first), and tell your pair.

## Checkpoint

Show your pair one row you checked yourself, and one part of the agent's explanation with the rows behind it.

## Extensions

1. Push back. In the chat: `Your explanation leaves <a row> unexplained. Test another idea against the rows.` Does it test, or only argue?
2. Your own papers, if you started with the shipped ones: follow the three setup steps under Choose your papers, type `/new`, and send `Read 03_lit/question-mine.md and do what it says.`
3. The same papers through a fixed program, with no decisions, in the second terminal: `python 03_lit/pdfask.py corpus/papers/*.pdf`. What did the agent do that this did not?
4. Ten papers on a topic of yours: `python 03_lit/lit.py "<topic>" --n 10 --sort cited`.

## If something goes wrong

- The agent stops with rows still failing: type `Run python 03_lit/check_values.py and fix or flag every failing row.`
- The search says it used a saved answer: the room shares a search allowance. Tell the agent `Use only the papers you have and the topics listed by python 03_lit/lit.py --topics.`
- The model is slow or down: a saved run is in `03_lit/saved/`. Click `03_lit/saved/README.md` first, then do steps 4 and 5 on `03_lit/saved/values.csv` and `03_lit/saved/answer.md`. To see its check: `python 03_lit/check_values.py 03_lit/saved/values.csv`.
- The agent edits the tools or writes its own search: tell it `Use the 03_lit tools as they are.` A helper can restore them.
- A PDF of yours has "almost no text": it is a scan, and cannot be read here. Use the shipped papers.
- The chat gets slow: type `/new`, then `Read 03_lit/question.md and the files in results/, then continue.` (with your own papers, `question-mine.md`).
