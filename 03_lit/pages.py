"""Stop 3: a paper's text, page by page, exactly as the checker reads it. No model.

    python 03_lit/pages.py corpus/papers/zheng2020cover.pdf       every page
    python 03_lit/pages.py corpus/papers/zheng2020cover.pdf 3     page 3 only
    python 03_lit/pages.py                                       list every PDF in mine/ (or the shipped three) and save its text

Prints the text with === page N === markers, and keeps a copy in
results/papers/<name>.txt: click it in the Explorer to read what the agent read,
and use Cmd-F (Ctrl-F) to find a quoted sentence. A quote copied from this text,
with its page number, is what 03_lit/check_values.py can confirm.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quotes import pdf_pages, scanned   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEXTS = ROOT / "results" / "papers"
SHIPPED = ROOT / "corpus" / "papers"


def show(path, only=None, summary=False):
    pages = pdf_pages(path)
    if path.is_absolute() and ROOT in path.parents:
        path = path.relative_to(ROOT)
    TEXTS.mkdir(parents=True, exist_ok=True)
    text = "".join(f"\n=== page {n} ===\n{t}" for n, t in enumerate(pages, 1))
    (TEXTS / f"{path.stem}.txt").write_text(text)
    if scanned(pages):
        print(f"{path}: almost no text, a scanned PDF. Its words cannot be read or checked here; use another paper.")
        return
    if summary:
        print(f"{path}: {len(pages)} pages, {sum(len(p) for p in pages):,} characters -> results/papers/{path.stem}.txt")
        return
    if only:
        if not 1 <= only <= len(pages):
            sys.exit(f"{path} has {len(pages)} pages, so there is no page {only}.")
        print(f"=== {path}, page {only} of {len(pages)} ===\n{pages[only - 1]}")
    else:
        print(f"=== {path}, {len(pages)} pages ==={text}")
    print(f"\n(Saved as results/papers/{path.stem}.txt)")


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    if argv:
        path = Path(argv[0])
        if not path.exists():
            sys.exit(f"No file {path}. The papers are in mine/ (yours) and corpus/papers/ (the shipped three).")
        show(path, int(argv[1]) if len(argv) > 1 else None)
        return
    mine = sorted((ROOT / "mine").glob("*.pdf"))
    for path in mine or sorted(SHIPPED.glob("*.pdf")):
        show(path, summary=True)


if __name__ == "__main__":
    main(sys.argv[1:])
