"""Checks agent_blanks.py against a fake model, no endpoint needed."""
import ast, sys
from pathlib import Path
src = Path(__file__).with_name("agent_blanks.py").read_text()
import re
left = [i + 1 for i, line in enumerate(src.splitlines())
        if re.match(r"^\s*(\.\.\.|result = \.\.\.)\s*(#.*)?$", line) or re.search(r"\bif \.\.\.:|in \.\.\.:|append\(\.\.\.\)", line)]
if left:
    print("Blanks still open on lines:", ", ".join(map(str, left)))
    sys.exit(1)
try:
    ast.parse(src)
except SyntaxError as e:
    print("Syntax error:", e); sys.exit(1)
print("No blanks left and the file parses. Now point followon/old-modules/04_tool/starter.py at it: change")
print("    from agent import run, save_trace")
print("to  from agent_blanks import run, save_trace   (after copying this file next to agent.py)")
