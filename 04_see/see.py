"""Stop 4: show an image to a model that can see, and ask about it.

    python 04_see/see.py <image> "<question>"     ask anything about a PNG or JPEG
    python 04_see/see.py <image> --extract        the plotted data, as a CSV
    python 04_see/see.py <image> --extract "only the left panel"

--extract saves the table to results/seen/<image-stem>.csv and the model's
whole reply beside it, so you can see what it actually said. Then:

    python 04_see/compare.py <image> results/seen/<image-stem>.csv

From Python:  from see import see, extract
              see("04_see/charts/co2_line.png", "What is on the x axis?")

The model is NVIDIA Nemotron 3.5 Super VL on OpenRouter. It thinks before it
answers, and the thinking is billed as output tokens, so each call prints what
it cost. A call that runs past the deadline is abandoned and tried once more.
"""
import base64
import io
import re
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm                                             # noqa: E402  (the shared client, .env and cost tally)

VISION_MODEL = "nvidia/nemotron-3.5-super-vl"
DEADLINE = 90            # seconds of wall clock per attempt; one retry after that
MAX_TOKENS = 24000       # room for thinking plus the answer (thinking alone has reached 11,000)
# Let it think, but do not send the thinking back. Tested November 6: turning
# thinking off made it refuse or ramble on dense charts, and OpenRouter's
# "effort" and thinking "max_tokens" settings did not shorten the thinking on
# this model, so the only reliable control is a generous MAX_TOKENS.
REASONING = {"exclude": True}
MAX_BYTES = 2_000_000    # images bigger than this are shrunk before sending
SEEN = llm.ROOT / "results" / "seen"

# Filled in by every call: provider, seconds, attempts. llm.LAST has the tokens and cost.
INFO = {}

EXTRACT_PROMPT = """Read the data plotted in this chart and reply with it as a CSV table.

Rules for the table:
- A header row, then one row per plotted point (or per bar, or per category).
- The first column is the x axis: its quantity with units in parentheses, for example "time (h)". For a bar chart it holds the category names.
- Then one column per data series, named after its legend label with units in parentheses, for example "control (mg/L)". If the chart has two y axes, each series takes the units of its own axis.
- If error bars are drawn, put a column right after its series named "<series> err (<units>)" holding the half length of the error bar. Leave error columns out if there are no error bars.
- Read every marker or bar you can see, at its center. On a logarithmic axis give the actual value (for example 3000000), not the exponent.
- Plain numbers only: no thousands separators, no units in the cells, no "~". Leave a cell empty if a series has no point at that x.
- No commas inside a column name or category name (write "Mauna Loa Hawaii", not "Mauna Loa, Hawaii").
- Reply with the CSV only: no explanation, no code fence."""


def image_data_url(image_path):
    """The image as a base64 data URL. PNG and JPEG are sent as they are; any
    other format is converted to PNG. Over about 2 MB, the picture is shrunk
    step by step until it fits, because large uploads are slow and the model
    does not need more pixels than a screen shows."""
    from PIL import Image                 # imported here so --help works without Pillow
    path = Path(image_path)
    data = path.read_bytes()
    try:
        img_file = Image.open(io.BytesIO(data))
    except Exception:
        raise RuntimeError(f"{path.name} is not a picture Python can open: it is empty, cut short, "
                           "or not an image. Export it again as PNG or JPEG.")
    with img_file as img:
        kind = img.format
        if kind in ("PNG", "JPEG") and len(data) <= MAX_BYTES:
            mime = "image/png" if kind == "PNG" else "image/jpeg"
            return f"data:{mime};base64," + base64.b64encode(data).decode()
        img = img.convert("RGB") if kind == "JPEG" or img.mode not in ("RGB", "RGBA", "L") else img
        out_kind = "JPEG" if kind == "JPEG" else "PNG"
        scale = 1.0
        while True:
            size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            buffer = io.BytesIO()
            img.resize(size).save(buffer, out_kind, **({"quality": 90} if out_kind == "JPEG" else {}))
            if buffer.tell() <= MAX_BYTES or scale < 0.1:
                break
            scale *= 0.8
        if scale < 1.0:
            print(f"(image shrunk to {size[0]} x {size[1]} pixels to stay under 2 MB)")
    mime = "image/png" if out_kind == "PNG" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buffer.getvalue()).decode()


def _one_request(messages, max_tokens=MAX_TOKENS):
    """One request with a hard wall-clock deadline. Returns the response, or
    raises TimeoutError. The request runs in a background thread so a slow
    provider cannot hold the program past the deadline; the HTTP timeout and
    max_retries=0 stop the library from quietly retrying on its own."""
    client = llm.client.with_options(timeout=DEADLINE, max_retries=0)
    result = {}

    def work():
        try:
            result["response"] = client.chat.completions.create(
                model=VISION_MODEL, messages=messages, max_tokens=max_tokens, temperature=0.2,
                extra_body={"usage": {"include": True}, "reasoning": REASONING})
        except Exception as err:          # handed to the caller below
            result["error"] = err

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    thread.join(DEADLINE)
    if thread.is_alive():
        raise TimeoutError(f"no answer within {DEADLINE} seconds; abandoned (the provider may still bill it)")
    if "error" in result:
        raise result["error"]
    return result["response"]


def see(image_path, question):
    """Ask the vision model one question about one image. Returns the answer
    text. Tries twice: a second attempt follows a deadline, an error, or an
    empty or cut-off answer (the model can spend its whole allowance thinking)."""
    if not llm.ON_OPENROUTER:
        raise SystemExit("Stop 4 needs OpenRouter, where the model that reads images is. "
                         "Switch with: bash 00_setup/switch_backend.sh openrouter")
    messages = [{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": image_data_url(image_path)}}]}]
    start = time.time()
    spent_before = llm.TOTAL["cost"]          # so a retried call reports both attempts' cost
    problem = ""
    max_tokens = MAX_TOKENS
    unknown = 0                               # attempts whose cost nobody reported
    INFO.clear()
    for attempt in (1, 2):
        try:
            response = _one_request(messages, max_tokens)
        except Exception as err:
            unknown += 1                      # an abandoned or failed request may still be billed
            problem = f"{type(err).__name__}: {str(err)[:160]}"
            print(f"(attempt {attempt}: {problem})")
            continue
        llm._record(response)              # tokens and cost into llm.LAST and llm.TOTAL
        if not isinstance(llm.LAST.get("cost"), (int, float)):
            unknown += 1
        if not response.choices:           # the service answered with an error instead, e.g. an image it cannot read
            err = (response.model_extra or {}).get("error") or {}
            reason = err.get("message", "no reason given") if isinstance(err, dict) else str(err)
            raise RuntimeError(f"The model service would not read this image ({reason[:120]}). "
                               "Is it a real PNG or JPEG? Export it again and retry.")
        choice = response.choices[0]
        text = choice.message.content or ""
        # Some providers return the thinking inline. It is not the answer.
        text = re.sub(r"<think>.*?(</think>\s*|$)", "", text, flags=re.S).strip()
        INFO.update({"provider": (response.model_extra or {}).get("provider"),
                     "seconds": round(time.time() - start, 1), "attempts": attempt,
                     "cost": llm.TOTAL["cost"] - spent_before, "cost_unknown": unknown})
        if text and choice.finish_reason != "length":
            return text
        problem = "the model used its whole allowance thinking" if not text else "the answer was cut off"
        print(f"(attempt {attempt}: {problem})")
        max_tokens = 32000                 # more room for the second try (the most some providers allow)
    INFO.update({"provider": None, "seconds": round(time.time() - start, 1), "attempts": 2,
                 "cost": llm.TOTAL["cost"] - spent_before, "cost_unknown": unknown})
    raise RuntimeError(f"No answer after two tries ({problem}). Run it again in a minute.")


def cost_text():
    """The dollars for the last call, saying plainly when some of it is unknown:
    an abandoned request, or a provider that reported no cost, may still be billed."""
    cost, unknown = INFO.get("cost"), INFO.get("cost_unknown", 0)
    if not isinstance(cost, (int, float)):
        return "cost not reported"
    if unknown and cost == 0:
        return "cost not reported"
    if unknown:
        return f"${cost:.4f} reported, plus {unknown} attempt(s) whose cost is unknown"
    return f"${cost:.4f}"


def cost_line():
    """One line saying what the last call took: provider, time, tokens, dollars.
    The dollars cover every attempt of that call that reported a cost, and the
    line says when an attempt's cost is unknown."""
    dollars = cost_text()
    return (f"[{VISION_MODEL} via {INFO.get('provider')}, {INFO.get('seconds')} s, "
            f"attempt {INFO.get('attempts')}, {llm.LAST.get('prompt_tokens', 0):,} tokens in, "
            f"{llm.LAST.get('completion_tokens', 0):,} out (mostly thinking), {dollars}]")


def _number(cell):
    """The cell as a float, ignoring stray symbols such as "~"; None if it is
    empty; raises ValueError if it is not a number at all."""
    cell = re.sub(r"[~≈<>\s]", "", cell)
    return None if cell == "" else float(cell)


def _numeric_row(cells):
    """True when every cell after the first is a number or empty."""
    try:
        [_number(c) for c in cells[1:]]
        return True
    except ValueError:
        return False


def _has_number(cells):
    """True when at least one of the cells is a number."""
    for c in cells:
        try:
            if _number(str(c)) is not None:
                return True
        except ValueError:
            pass
    return False


def csv_from_reply(text):
    """The CSV table inside a reply, as a pandas DataFrame, or raise ValueError.
    Models wrap tables in code fences and add a sentence before or after, so
    this looks for a header row (words) followed by rows of numbers with the
    same number of cells, and keeps only those."""
    import csv
    import pandas as pd
    text = re.sub(r"```[a-zA-Z]*", "", text)
    rows = [row for row in csv.reader(line.strip() for line in text.splitlines()) if any(c.strip() for c in row)]
    for h in range(len(rows) - 1):
        header, width = rows[h], len(rows[h])
        if width >= 2 and len(rows[h + 1]) == width and _numeric_row(rows[h + 1]) and not _numeric_row(header):
            break
    else:
        raise ValueError("no header row followed by rows of numbers")
    data = []
    rest = rows[h + 1:]
    for n, row in enumerate(rest):
        if len(row) != width or not _numeric_row(row):
            # Either the table has ended and prose follows, or a row is broken
            # (an extra comma, a missing cell) with more data after it. Stopping
            # quietly would drop those rows, so a broken row is an error.
            later = [r for r in rest[n + 1:] if len(r) == width and _numeric_row(r)]
            looks_like_data = len(row) >= 2 and _numeric_row(row)
            # A last row as wide as the table with a number in it is a data row
            # with an unreadable cell ("12,unreadable"), not a closing sentence.
            half_read = len(row) == width and (_has_number(row[1:]) or (data and _has_number(row[:1])
                                                                        and all(_has_number([d[0]]) for d in data)))
            if later or looks_like_data:
                raise ValueError(
                    f"table row {n + 1} has {len(row)} cells where the header has {width}: "
                    f"{','.join(row)[:80]!r}. Reading on would drop {len(later)} later row(s), "
                    "so the whole table is refused")
            if half_read:
                raise ValueError(
                    f"table row {n + 1} has a cell that is not a number: {','.join(row)[:80]!r}. "
                    "Dropping it would leave a table that looks complete, so the whole table is refused")
            break
        data.append([row[0].strip()] + [_number(c) for c in row[1:]])
    df = pd.DataFrame(data, columns=[c.strip() for c in header])
    first = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    if first.notna().all():
        df[df.columns[0]] = first          # a numeric x axis, not category names
    return df


def extract(image_path, note="", quiet=False):
    """Ask for the plotted data as CSV and save it to results/seen/<stem>.csv.
    Returns the CSV path, or None when the reply was not a usable table (the
    reply is saved as <stem>.reply.txt either way, so you can read it). The
    CSV, reply, comparison and error table left from an earlier run of the same
    chart are removed before the model is asked, so when this run fails, for
    any reason, an old table cannot pass for this run's."""
    stem = Path(image_path).stem
    SEEN.mkdir(parents=True, exist_ok=True)
    prompt = EXTRACT_PROMPT + (f"\n\nAlso: {note}" if note else "")
    raw_path = SEEN / f"{stem}.reply.txt"
    stale = [p for p in (SEEN / f"{stem}.csv", raw_path, SEEN / f"{stem}-compare.png", SEEN / f"{stem}-errors.csv")
             if p.exists()]
    for p in stale:
        p.unlink()
    try:
        reply = see(image_path, prompt)
    except RuntimeError as err:
        if stale:
            raise RuntimeError(f"{err} Removed the earlier {', '.join(p.name for p in stale)}, "
                               "so it cannot be mistaken for this run's.") from None
        raise
    raw_path.write_text(reply + "\n")
    try:
        df = csv_from_reply(reply)
    except Exception as err:
        stale = [p for p in stale if p != raw_path]
        print(f"The reply is not a table pandas can read ({err}). No CSV saved; "
              f"the reply is in {raw_path.relative_to(llm.ROOT)}"
              + (f". Removed the earlier {', '.join(p.name for p in stale)} so it cannot be mistaken for this run's."
                 if stale else ""))
        return None
    csv_path = SEEN / f"{stem}.csv"
    df.to_csv(csv_path, index=False)
    if not quiet:
        print(f"{len(df)} rows x {df.shape[1]} columns: {', '.join(df.columns)}")
        print(f"Saved {csv_path.relative_to(llm.ROOT)} (the model's reply is in {raw_path.name})")
    return csv_path


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help") or len(args) < 2:
        print(__doc__)
        return
    image = args[0]
    if not Path(image).is_file():
        raise SystemExit(f"No such image: {image}")
    try:
        if args[1] == "--extract":
            saved = extract(image, " ".join(args[2:]))
        else:
            saved = True
            print(see(image, " ".join(args[1:])))
    except RuntimeError as err:
        raise SystemExit(f"{err} [{cost_text()}]")    # one sentence for the room, not a traceback
    print(cost_line())
    if saved is None:
        sys.exit(1)                        # no usable table: a failure, not a quiet success


if __name__ == "__main__":
    main()
