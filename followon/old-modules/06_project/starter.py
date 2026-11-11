"""Module 6: your own tool, added to the agent with one line.

    python 06_project/starter.py                      the default question
    python 06_project/starter.py "your question"

Test your tool on its own first (python 06_project/csv_tool.py). Then the one
line that matters is the tools=[...] list below: your function goes in it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "05_agent"))
from agent import run, save_trace                   # noqa: E402
from tools import read_document, search_records     # noqa: E402
from csv_tool import summarize_csv                  # noqa: E402  <- or your own function
# A starter instead, or as well? Remove the # from its line and add the name below.
# from starters.fasta_tool import describe_sequences   # FASTA: length and GC per sequence
# from starters.bibtex_tool import find_references     # BibTeX: search a reference list
# from starters.log_tool import log_summary            # potentiostat log: per channel
# from starters.citation_tool import check_citation    # Crossref: is a citation real and correct?

DEFAULT_QUESTION = ("Using the instrument log, which condition gave the highest mean reading, "
                    "and how much higher was it than baseline? Give the numbers you used.")

args = [a for a in sys.argv[1:] if not a.startswith("-")]
question = args[0] if args else DEFAULT_QUESTION
print(f"Question: {question}\n")

# ---- The one line: your tool joins the list. -----------------------------
answer, messages = run(question, tools=[search_records, read_document, summarize_csv])
# ---------------------------------------------------------------------------
save_trace(messages, Path(__file__).resolve().parent / "trace.json")
