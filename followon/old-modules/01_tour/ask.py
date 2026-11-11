"""One prompt, one reply. The whole program is the ask() line at the bottom.

    python 01_tour/ask.py "your question"
    python 01_tour/ask.py "your question" corpus/doc_003.txt     the document goes after the question

Without a document the model answers from what it learned in training: some
of that is right and some is not, and nothing in the prompt lets you tell
which.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from docs import load          # noqa: E402
from llm import ask            # noqa: E402

if not 2 <= len(sys.argv) <= 3:
    raise SystemExit('usage: python 01_tour/ask.py "your question" [document]')

prompt = sys.argv[1]
if len(sys.argv) == 3:
    prompt += "\n\nDocument:\n" + load(sys.argv[2])["text"]

print(ask(prompt))
