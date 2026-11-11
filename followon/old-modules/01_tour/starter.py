"""Module 1: what the model can do. Six prompts on one document.

    python 01_tour/starter.py                         all six, on the pizza study
    python 01_tour/starter.py 2                       only prompt 2
    python 01_tour/starter.py 01_tour/bench_note.txt 2 6     a document, prompts 2 and 6
    python 01_tour/starter.py mine/notes.txt          one of your own (after convert.py)

Every reply is also added to the end of mine/results/module1.md, with the
document, the prompt and the model, so you can compare a reply from before and
after you change a prompt.

The only things to change are below this docstring: the document, and the six
prompts. Everything else is one line per call: ask(prompt).
"""
import shlex
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from docs import load                # noqa: E402
from llm import ask, model_name      # noqa: E402

# ---- Change these. -------------------------------------------------------
DOCUMENT = "corpus/doc_001.txt"

PROMPTS = {
    "Two-sentence summary":
        "Summarize this document in two sentences.",
    "For a first-year student":
        "Rewrite the main finding of this document for a first-year undergraduate, in three sentences, no jargon.",
    "Methods used":
        "List the methods this document reports using, at most eight, one per line, nothing else.",
    "Key numbers":
        "List up to eight key numbers in this document, one per line: value, unit, what it measures, and the group and time it belongs to if the document says. Keep it brief.",
    "Two reviewer questions":
        "Write two questions a careful peer reviewer would ask about this document, one sentence each. After each, quote the sentence it is about, or write: not reported in the document.",
    "Handling missing information":
        "What did the follow-up work this document proposes find? Answer only from the document. If it does not report a result, say so and quote the sentence that proposes the follow-up; if it proposes none, say that.",
}
# --------------------------------------------------------------------------

# A path on the command line replaces DOCUMENT; numbers pick prompts.
numbers = []
for arg in sys.argv[1:]:
    if arg.isdigit():
        numbers.append(int(arg))
    else:
        DOCUMENT = arg
headings = list(PROMPTS)
if any(n < 1 or n > len(headings) for n in numbers):
    raise SystemExit(f"Prompt numbers run from 1 to {len(headings)}.")
numbers = numbers or range(1, len(headings) + 1)

doc = load(DOCUMENT)
print(f"Document: {doc['source']}   Title: {doc['title']}\n")

# A subfolder, so convert.py and the folder scripts never mistake it for a document.
results = ROOT / "mine" / "results" / "module1.md"
results.parent.mkdir(parents=True, exist_ok=True)
with open(results, "a") as saved:
    saved.write(f"\n## {datetime.now():%Y-%m-%d %H:%M}   {DOCUMENT}   model: {model_name()}\n")
    for n in numbers:
        heading = headings[n - 1]
        reply = ask(f"{PROMPTS[heading]}\n\nDocument:\n{doc['text']}")
        print("=" * 72)
        print(f"{n}. {heading}")
        print("=" * 72)
        print(reply)
        print()
        saved.write(f"\n### {n}. {heading}\n\nPrompt: {PROMPTS[heading]}\n\n{reply}\n")

print("Saved to mine/results/module1.md.")
print("Check one claim against the source. Find the passage with a word or number from a reply,")
print("then read it and ask whether it says the same thing:")
print(f'    grep -n -i "the word" {shlex.quote(DOCUMENT)}')
