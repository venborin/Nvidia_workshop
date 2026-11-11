"""Module 2: getting it to do what you mean. One prompt, ten labeled documents, a score.

    python 02_prompts/starter.py             the ten labeled documents
    python 02_prompts/starter.py --heldout   the six held-out ones, to test whether your best prompt generalizes

The prompt is the plain string PROMPT below. That is the only thing to edit.
Change one thing at a time, run, write the score down.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from docs import load                    # noqa: E402
from llm import ask                      # noqa: E402
from score import LABELS, cases, score   # noqa: E402

# ---- The prompt. Edit this and nothing else. ------------------------------
PROMPT = """What kind of study is this? Answer with one word.

{document}"""
# ---------------------------------------------------------------------------
# Things people try, one at a time:
#   a role         "You are a librarian classifying research methods."
#   constraints    "Choose exactly one of: experimental, computational, theoretical, qualitative, review, mixed."
#   a format       "Answer with the label only, in lowercase, nothing else."
#   two examples   "Example: a study that runs a simulation and reports its output is computational. ..."
#   a rule         "Use mixed only when the document itself reports two kinds of method."

which = "heldout" if "--heldout" in sys.argv else "cases"
docs = cases(which)
print(f"Prompt:\n{PROMPT.strip()}\n")
print(f"Labels the scorer accepts: {', '.join(LABELS)}\n")

answers = {}
for doc_id, expected in docs.items():
    doc = load(Path(__file__).resolve().parents[3] / "corpus" / f"{doc_id}.txt")
    reply = ask(PROMPT.format(document=doc["text"]))
    answers[doc_id] = reply
    first = reply.strip().splitlines()[0] if reply.strip() else "(empty)"
    print(f"{doc_id}  expected {expected:<14} got: {first[:70]}")

print()
score(answers, docs)
