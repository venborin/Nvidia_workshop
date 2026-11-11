"""Module 4: giving the model a tool. The same question, without and with it.

    python 04_tool/starter.py                        the demo question
    python 04_tool/starter.py "your question here"   the one from your pre-work
    python 04_tool/starter.py --no-tool "question"   without the tool, for comparison
    python 04_tool/starter.py --saved                search the saved table, not yours

Both runs get the same instructions (SYSTEM below); only the tool differs.
The program prints the exchange as it happens: what the model asked for, what
Python ran, what came back, and the answer. The trace is saved to
04_tool/trace.json. Read it against 04_tool/trace.md, the annotated one.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent import run, save_trace     # noqa: E402
from llm import ask                   # noqa: E402
from tools import search_records      # noqa: E402

DEFAULT_QUESTION = "Which studies in the table tested pizza, and did they agree about its effect? Cite doc ids."

# The instructions agent.run() uses by default, written out so that the run
# without the tool gets exactly the same ones.
SYSTEM = ("You are a careful research assistant. Use the tools to find evidence before answering. "
          "Cite the doc_id of every record you rely on. If a search finds nothing, try one different "
          "query, then stop searching and say plainly that the evidence does not establish an answer.")

args = [a for a in sys.argv[1:] if not a.startswith("-")]
question = args[0] if args else DEFAULT_QUESTION
print(f"Question: {question}\n")

if "--no-tool" in sys.argv:
    print("[no tool] same instructions, no tool: the model has only its memory\n")
    print(ask(question, system=SYSTEM))
else:
    answer, messages = run(question, tools=[search_records], system=SYSTEM)
    save_trace(messages, Path(__file__).resolve().parent / "trace.json")
