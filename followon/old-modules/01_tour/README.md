# Module 1: What the model can do

One line of Python sends a research document to the model and brings text back. This module runs six of those lines on one document so you can see, side by side, what the model does well and where it slips. Every later module in the day's one program, the document assistant, is this same call with a better prompt around it.

About 40 minutes. Folder: `01_tour/`. Behind? `bash catchup.sh m1`

## You will be able to

1. Call the model from Python with one line, `ask(prompt)`, on a document you choose.
2. Say which of six jobs it did well enough that you would use the result.
3. Judge one claim against the source, using the five judgments below, and point to the passage that settles it. A claim you checked and found supported is a full answer.

## The idea

A prompt is the text you send the model. Each call in this module puts an instruction in front of a document's text and sends it with one line:

```python
reply = ask("Summarize this document in two sentences.\n\nDocument:\n" + text)
```

The starter does this six times, with six instructions.

The model brings two things to each reply: what it learned in training, before you ever called it, and the prompt, here one document. Only the second can be checked against the source in front of you. The documents are invented, so when a reply adds something like "randomized" or "significantly", it did not come from this study. These calls look nothing up; whatever a reply adds, the only question here is whether the document supports it.

On a short research document the model is often useful. It compresses (a two-sentence summary), it re-levels (the same finding for a first-year student), and it lists (methods, numbers, questions a reviewer would ask). The sixth prompt asks what a follow-up study found, which the document cannot know, and asks the model to say so and quote the sentence that proposes it. It also slips, in replies that read just as confidently as the good ones. When you check a claim, give it one of five judgments:

- Supported: the source says it, in these words or others.
- Contradicted: the source says something different, such as a planned test reported as done.
- Added: the source does not say it at all, such as "significantly" when no test is reported.
- Dropped, and it matters: something left out changes how a reader would take the result, such as a limitation.
- Fair simplification: shorter or plainer, and a reader would still take it the right way, such as leaving out what the pizza cost in a three-sentence rewrite.

Supported means faithful to this document, not proven true: the document itself can overstate. And an accurate reply is a good outcome, not a failed exercise; the point is that you checked.

`grep` is a terminal command that prints every line of a file containing some text; `-n` adds line numbers and `-i` ignores capital letters. It only finds the passage; reading it decides whether it says what the reply says. A word that is missing may still be supported in other words, and a number that matches may still be used for the wrong thing.

## Read, then predict

Open `corpus/doc_001.txt` from the file tree and read it: a short, invented study of whether free pizza brings students to office hours. It takes two minutes.

The model will rewrite the main finding for a first-year student in three sentences. Write down one detail you expect it to keep and one limit or caveat you expect it to lose. Make it an idea, not a word: the model is told to avoid jargon, so it will drop some words anyway.

## Do it

1. Run the starter. It makes six calls on `corpus/doc_001.txt` and prints each reply under a numbered heading, from `1. Two-sentence summary` to `6. Handling missing information`. It takes about a minute.

   ```bash
   python 01_tour/starter.py
   ```

   Every reply is also added to the end of `mine/results/module1.md`, with the document, the prompt and the model, so nothing scrolls away. To run only some of the prompts, give their numbers: `python 01_tour/starter.py 2` reruns the first-year rewrite alone, in a few seconds.

2. Compare the rewrite (2) with your prediction. Next to your Keep and Lose, mark whether each came true.

3. Check one claim against the source. Pick a word or number from any reply, find it with `grep`, then read the line it prints.

   ```bash
   grep -n -i "random" corpus/doc_001.txt
   ```

   For example, one methods list began "Random assignment of lab sections to treatment (announcement) vs control". The grep prints nothing. That alone does not settle it, since the document could say the same thing in other words, so read the second paragraph: the afternoon sections were told about the pizza and the morning sections were not. The groups were split by meeting time, not at random. "Random" is the model's word, and the source says something different. A number that is in the document prints its line:

   ```bash
   grep -n "7.6" corpus/doc_001.txt
   ```

   ```text
   9:Across the nine sessions, attendance averaged 7.6 students per session from the afternoon
   sections and 4.1 from the morning sections, an increase of 85 percent. ...
   ```

   The number matches. Now check that the reply used it for the same thing: the average per session from the afternoon sections, not, say, the morning sections' average or a total for the course.

4. Pick the two of the six results you would actually use. Check one claim in each the same way, and give each a judgment from the list above.

## Checkpoint

Show your pair the most useful of the six results, and one claim whose support matters: the claim, the passage you found, and your judgment. If everything you checked was supported, that is your result; say which claim you would check next.

## Exercises

1. Core: one more document. The bench note is the default; your own document or another field are alternatives. Each runs one or two prompts, not six.

   The bench note, `01_tour/bench_note.txt`: six sentences of a lab notebook that mix what was observed, what is only suspected, and what is planned next. Run the rewrite (2) and the missing-information question (6):

   ```bash
   python 01_tour/starter.py 01_tour/bench_note.txt 2 6
   ```

   Read the note itself, then sort its sentences into observed, suspected and planned. Then compare the two replies. Asked directly (6), the model says whether the fresh-buffer test has a result. Does the rewrite (2) agree, or does it say the test worked? If your rewrite keeps the plan as a plan, compare it with this one from a test run, where the reply to 6 in the same run said no result was reported:

   ```text
   When we began preparing fresh liquid every morning, the upward creep disappeared,
   suggesting that daily preparation would stop the drift.
   ```

   Your own document: if you put PDF, Word or Markdown files in `mine/`, convert them first with `python convert.py`. If you brought none, right-click `mine/` in the file tree, choose New File, name it `notes.txt`, and paste in a paragraph or two of your own writing. Then run the two prompts you would most likely use, for example:

   ```bash
   python 01_tour/starter.py mine/notes.txt 1 6
   ```

   Put the path in quotes if the name has spaces, here and in `grep`. Check one claim. Plans are worth a look: does any reply describe as done something your document only proposes?

   Another field: each of these samples is about 320 words, with one term to know and one thing worth checking. Run the summary (1), or any two prompts, and check that one thing.

   | Document | Field | Term to know | Worth checking |
   |---|---|---|---|
   | `corpus/doc_006.txt` | chemistry | conversion: the share of nitric oxide the catalyst removes | Is copper aluminate reported as found, or only as consistent with a measured band? |
   | `corpus/doc_010.txt` | chemistry, modeling | extrapolate: run a fitted model past the data it was fitted to | Is 38 percent reported as a measurement or as a prediction? |
   | `corpus/doc_011.txt` | engineering | root mean square error: the typical size of a miss | Do the accuracy figures match the document, in the same units? |
   | `corpus/doc_015.txt` | genomics | recall: the share of true variants a pipeline found | Does any reply name one pipeline as the best overall? |
   | `corpus/doc_016.txt` | education research | self-report: what students said they do, not what anyone observed | Is the improvement called significant, and are the 14 interview volunteers spoken of as the whole class of 61? |

   ```bash
   python 01_tour/starter.py corpus/doc_015.txt 1
   ```

2. Stretch (optional): change one of the six prompts. Open `01_tour/starter.py`. In `PROMPTS`, each entry is a heading in quotes, a colon, then the instruction in quotes, then a comma. Replace one entry with something you actually want from your documents, keeping the quotes and the comma, and rerun only that one, here the fifth:

   ```bash
   python 01_tour/starter.py 5
   ```

   The reply before and after your change are both in `mine/results/module1.md`. Look for whether the new one did what you meant. If it did not, find the words in your prompt that let it go somewhere else. Module 2 is about exactly that.

3. Stretch (optional): send the same prompt twice. Run `python 01_tour/starter.py 1` twice, then compare the last two summaries in `mine/results/module1.md`. Look for which words change, and whether any fact changes. The helper asks the model for a little randomness, so the wording varies from run to run. A detail that changes between runs is a detail to check against the source; a detail that stays the same still needs checking.

4. Stretch (optional): ask about a paper you know well, with no document attached. `01_tour/ask.py` sends one prompt and prints the reply, so the reply comes only from what the model learned in training. Put the paper in your own words inside the quotes.

   ```bash
   python 01_tour/ask.py "What did <a paper you know well> report? Give its full title, journal, volume and pages, and three specific findings with numbers."
   ```

   Check two or three details against the paper itself, a figure or a table. Give each a judgment, and write what in the paper settled it. Specific-sounding details such as page numbers and percentages are the ones to check first.

## What you have now

- `llm.py` and its one call, `ask(prompt)`, which every later module uses.
- The habit of finding the passage behind a claim, reading it, and giving one of five judgments, which Module 3 turns into an audit of a whole table.
- A sense of which of the six jobs are worth asking for, which leads into Module 2.

## If something goes wrong

- A reply is empty or stops in the middle of a line. Most often the model spent its allowance thinking before it answered. Ask for less (fewer items, or add "Keep it brief." to the prompt) and rerun that prompt alone.
- `No such file or directory` for your document. The path starts from the top folder of your repository. Type `ls mine` to see the exact file name, and give it as `mine/name.txt`, in quotes if it has spaces.
- `Prompt numbers run from 1 to 6.` A number after the command picks a prompt; there are six.
- The first line says `Title: not stated`. Your document has no `Title:` line at the top. That is fine; the model still reads the whole text.
- `SyntaxError` after editing `PROMPTS`. A quote or a comma went missing. Fix it, or run `bash catchup.sh m1` to restore the original `01_tour/` files and the shared helpers. Your edited files are copied to `mine/catchup-backup-<date-time>/` first, and `mine/results/module1.md` is not touched.
- All six take about a minute, one call after another; that is normal. Give prompt numbers to run fewer.
