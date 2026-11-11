"""Is what you brought ready for the day? Checks every file in mine/.

    python upload_check.py

Drag your files from your laptop onto the mine/ folder in the file tree first
(or right-click mine/ and choose Upload). For each file it prints its size and
what the day can do with it: the columns of a CSV, whether a PDF has text the
model can read, the size of an image. When a file will not work, it says why
and which shipped example to use instead. Nothing leaves the Codespace here.

Give a file three minutes at most. If it still does not work, use the shipped
example for now and come back to your own file in Stop 6.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINE = ROOT / "mine"
MB = 1024 * 1024

FALLBACK = {
    "data": "Stop 2 has four datasets ready: 02_data/datasets/",
    "paper": "Stop 3 has three open-access papers ready: corpus/papers/",
    "image": "Stop 4 has six charts ready, with the data behind them: 04_see/charts/",
}


def size(path):
    n = path.stat().st_size
    return f"{n / MB:.1f} MB" if n >= MB else f"{max(1, n // 1024)} KB"


def check_csv(path):
    """Read it the way Stop 2 will. Tries the usual encodings and lets pandas guess the separator."""
    import pandas as pd
    if path.stat().st_size > 50 * MB:
        return False, f"too big for a one-hour stop. Take a sample (a few thousand rows). {FALLBACK['data']}"
    last = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=enc, nrows=20000)
            break
        except Exception as err:
            last = err
    else:
        return False, f"could not be read as a table ({type(last).__name__}). {FALLBACK['data']}"
    if df.shape[1] < 2:
        return False, f"has only one column: is it separated by something unusual? {FALLBACK['data']}"
    cols = ", ".join(str(c) for c in df.columns[:12]) + (" ..." if df.shape[1] > 12 else "")
    numeric = df.select_dtypes("number").shape[1]
    note = "" if numeric else " No column reads as numbers, so plots will be limited."
    return True, f"{df.shape[0]:,} rows{' (first 20,000 read)' if df.shape[0] == 20000 else ''}, {df.shape[1]} columns: {cols}.{note}"


def check_pdf(path):
    """A PDF is usable if it has a text layer. A scan is a picture of text and has none."""
    from pypdf import PdfReader
    try:
        pages = PdfReader(str(path)).pages
        chars = sum(len((p.extract_text() or "").strip()) for p in pages)
    except Exception as err:
        return False, f"could not be opened ({type(err).__name__}): password or damage? {FALLBACK['paper']}"
    if chars < 50 * max(1, len(pages)):
        return False, f"{len(pages)} pages but almost no text: a scan. The model cannot read it here. {FALLBACK['paper']}"
    long = " Long: only the first part will be read." if chars > 120_000 else ""
    return True, f"{len(pages)} pages, text readable (about {chars // 5:,} words).{long}"


def check_image(path):
    from PIL import Image
    try:
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        return False, f"could not be opened as an image. {FALLBACK['image']}"
    small = " Small: labels may be hard to read." if max(w, h) < 600 else ""
    return True, f"{w} x {h} pixels.{small}"


def check(path):
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        return check_csv(path)
    if ext == ".pdf":
        return check_pdf(path)
    if ext in (".png", ".jpg", ".jpeg"):
        return check_image(path)
    if ext in (".xlsx", ".xls"):
        return False, f"an Excel file. Open it on your laptop, choose File, Save As, CSV, and upload that. {FALLBACK['data']}"
    if ext in (".heic", ".heif"):
        return False, f"an iPhone photo format. On the Mac, open it in Preview and choose File, Export, JPEG. {FALLBACK['image']}"
    if ext in (".md", ".txt"):
        return True, "text, ready as it is."
    if ext == ".docx":
        return True, "a Word file: python convert.py turns it into text."
    if ext in (".json", ".parquet"):
        return True, "data, but not a CSV: Stop 2's prompts expect a CSV, so say in the prompt what the file is."
    return False, "a kind of file the day does not use."


def main():
    MINE.mkdir(exist_ok=True)
    files = sorted(p for p in MINE.iterdir() if p.is_file() and p.name != "README.md" and not p.name.startswith("."))
    if not files:
        print("mine/ is empty. That is fine: every stop has a shipped example.")
        print("To use your own: drag files from your laptop onto mine/ in the file tree, then run this again.")
        return
    ready = 0
    for path in files:
        ok, what = check(path)
        ready += ok
        print(f"{'ready' if ok else 'NOT READY':<9}  {path.name}  ({size(path)})\n           {what}")
    print(f"\n{ready} of {len(files)} files ready.")
    print("Everything in mine/ stays out of git. When a stop reads a file, its contents go to the model service.")


if __name__ == "__main__":
    main()
