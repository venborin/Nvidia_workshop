# Module 2: Getting it to do what you mean

A prompt that reads fine to you can still leave the model guessing. This module takes one small, useful job, labeling each study by its method, and improves the prompt the way you would improve an assay: change one thing, measure, look at the failures. The method label you settle on here becomes the `method` column of the table you build in Module 3.

About 50 minutes. Folder: `02_prompts/`. Behind? `bash catchup.sh m2`

## You will be able to

1. Improve a prompt by changing one thing at a time and see the effect of each change as a score on ten labeled documents.
2. Open a miss and say whose fault it was: the model's, the label's, or the prompt's, when it never said which words to answer with.
3. Check whether your best prompt holds up on documents you did not tune it on.

## The idea

A score turns "this prompt seems better" into evidence. `starter.py` sends one prompt to the model for each of ten documents, and `score.py` compares each reply with the label a person chose, stored in `corpus/labels.json`. The labels are six words: experimental, computational, theoretical, qualitative, review, mixed.

The scorer is strict on purpose. It reads the first of those six words in the reply. A reply with none of them scores as "no label". A reply that names two (a hedge) is scored by whichever comes first, so it passes or fails by luck. A miss looks like this:

```
miss doc_009: expected review, got no label   reply: survey
```

That reply is not wrong about the document. It just is not one of the six words, so the prompt is at fault.

Four common things to add to a prompt, often called levers:

- a role: who the model should act as ("You are a ...").
- constraints: rules the answer must follow, such as the allowed answers.
- an output format: exactly what the reply should look like.
- worked examples: one or two short cases with the right answer shown.

Change one lever at a time. If you change two and the score moves, you cannot tell which one did it.

Ten documents is a small test, and a prompt tuned on them can fit them and nothing else. The six held-out documents (`--heldout`) test whether it generalizes, as long as you do not tune on them too. Some misses are the label's fault: two of the sixteen documents are genuinely arguable, one in each set, and `corpus/README.md` says which.

## Predict first

Four changes will be made to a bad prompt: a role, constraints, an output format, two worked examples. Which one do you expect to help most? Write it down.

## Do it

1. Run the starter with the bad prompt that is already in the file.

   ```
   python 02_prompts/starter.py
   ```

   It prints the prompt, one line per document, then the score and the misses. It takes about half a minute. For example:

   ```
   doc_001  expected experimental   got: experiment
   doc_002  expected review         got: Meta-analysis
   ...
   Score: 2 out of 10
     miss doc_001: expected experimental, got no label   reply: experiment
     miss doc_002: expected review, got no label   reply: Meta-analysis
   ```

   Write the score down as your starting point.

2. Open `02_prompts/starter.py`. Near the top is `PROMPT`, a plain string between triple quotes. It is the only thing you edit today. The comment block below it gives one example line for each lever, plus a rule. Keep the line `{document}` in your prompt: that is where each document's text goes.

3. Make one change. Pick one lever, add one sentence for it to `PROMPT` without changing the rest, save, and run the same command again.

   ```
   python 02_prompts/starter.py
   ```

   The first lines of the output echo your prompt, so you can confirm the edit took. For example, after adding a role:

   ```
   Prompt:
   You are a research librarian who classifies studies by their method.

   What kind of study is this? Answer with one word.
   ```

   Write the new score down next to the lever you changed.

4. Open one miss. Pick a line that starts `miss`, open that document in `corpus/` from the file tree on the left, and read it. Ask why the model said what it said. There are three usual causes: the model misread the document; the label itself is arguable; or the model was right in its own words because the prompt never said which words to use.

## Checkpoint

Show your pair one change, its score, and one miss you opened, with your reason for why the model answered as it did.

## Exercises

1. Core. Make a second change. Keep your first change, add one sentence for a different lever to `PROMPT`, and run:

   ```
   python 02_prompts/starter.py
   ```

   Write the score down. Did it move, and which documents changed?

2. Core. Decide whose fault a miss was. Take a miss from any run so far, read the document, then read the "Ambiguous labels" section of `corpus/README.md`. Write down which of the three it was, the model, the label, or the prompt's vocabulary, and one sentence why. A miss on an arguable document is the label's fault only if the reply is the defensible alternative the corpus README names.

3. Core. Test on documents you did not tune on. With your best prompt in place, run:

   ```
   python 02_prompts/starter.py --heldout
   ```

   Compare fractions, not raw scores: 5 out of 6 is 83 percent, 9 out of 10 is 90 percent, and one held-out miss costs 17 points. Open any held-out miss and decide whose fault it was, as in exercise 2. If you now change the prompt because of what you saw here, the six become development data, documents you tuned on, and their score stops being a test. A fair final test then needs documents the prompt has never seen, such as your own in `mine/`.

4. Stretch (optional). A third change. Add one sentence for one more lever, then run both sets:

   ```
   python 02_prompts/starter.py
   python 02_prompts/starter.py --heldout
   ```

   If your score was already at the top, did the extra sentence change anything? What would you need to see before keeping it?

5. Stretch (optional). Fix a held-out miss on purpose. Write one rule in `PROMPT` aimed at a held-out document the model missed. If your held-out run had no miss, borrow one from your pair's run, or pick the held-out label you find least obvious and write a rule that defines it more sharply. Then run both sets:

   ```
   python 02_prompts/starter.py --heldout
   python 02_prompts/starter.py
   ```

   Did the held-out score go up? Did anything break, in either set? Which documents moved, and are they ones the corpus README calls arguable?

## What you have now

A prompt that labels a study's method, a score for each version of it, written down, and the habit that matters more than any one prompt: change one thing, measure, open the failures. In Module 3 the same job becomes one column of a table. Look at the description of `method` in `records.py`: it is a constraint lever, the list of allowed labels, written once so every row of the table uses the same six words.

## If something goes wrong

- `KeyError` or `ValueError: Single '}' encountered` when you run. Your prompt contains a curly brace. Python uses `{document}` to place the text, and any other `{` or `}` confuses it. Remove the extra braces, or double them as `{{` and `}}`.
- The score drops to almost nothing and the replies look like guesses, or a few ask you to describe the study. You deleted `{document}` from `PROMPT`, so the model never saw the document. Put it back on a line of its own.
- `SyntaxError` after editing. The triple quotes around `PROMPT` no longer match. `bash catchup.sh m2` restores the original file. It first copies your edited file to `mine/catchup-backup-<date-time>/`, so you can paste your prompt back in from there.
- The same prompt gives a different score on a second run. The model has a little randomness, so one document can flip between runs. Run twice before you believe a change of one or two points.
- A reply names the right label and still scores as a miss. The scorer reads the first label word, so "not computational but experimental" scores as computational. Ask for the label only.
