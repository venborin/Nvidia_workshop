"""Module 6, the default path: a summarizer over a small CSV. Two marked edits.

    python 06_project/csv_tool.py        tests the tool on its own, no model involved

The sample file is an instrument log: one row per reading, with a condition
column and a value column. Change the two marked lines so the tool reports on
your columns and answers your question, run this file to test it, then add it
to the agent in starter.py with one line.
"""
import csv
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- EDIT 1: the file and the two columns the tool reports on. ------------
CSV_FILE = HERE / "sample_log.csv"     # or your own: HERE.parents[2] / "mine" / "your_file.csv"
GROUP_COLUMN = "condition"             # the column whose values define the groups
VALUE_COLUMN = "reading"               # the numeric column to summarize
# ---- EDIT 2: the question this tool is good at, for the model to read. ----
QUESTION_IT_ANSWERS = "the instrument log: mean, spread and count of the readings for each condition"
# ---------------------------------------------------------------------------


def summarize_csv(group: str) -> str:
    # The docstring is what the model reads. It is built from EDIT 2 just below.
    want = group.strip().lower()
    if not CSV_FILE.exists():
        return f"error: no file at {CSV_FILE}; check CSV_FILE in EDIT 1"
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return f"error: {CSV_FILE.name} is empty"
    for col in (GROUP_COLUMN, VALUE_COLUMN):
        if col not in rows[0]:
            return f"error: no column named {col!r}; the columns are {', '.join(rows[0])}"
    groups, skipped = {}, {}
    for row in rows:
        name = (row[GROUP_COLUMN] or "").strip()
        groups.setdefault(name, [])          # every group counts, even one with no usable readings
        try:
            value = float(row[VALUE_COLUMN])
        except (TypeError, ValueError):
            value = math.nan
        if math.isfinite(value):
            groups[name].append(value)
        else:                                # blank, text, NaN or infinity: skipped and counted
            skipped[name] = skipped.get(name, 0) + 1
    if not any(groups.values()):
        return f"error: no numbers in column {VALUE_COLUMN!r}; check VALUE_COLUMN in EDIT 1"
    chosen = {g: v for g, v in groups.items() if want in ("all", "", "*") or g.lower() == want}
    if not chosen:
        return f"no group named {group!r}; the groups are {', '.join(sorted(groups))}"
    lines = []
    for g, vals in sorted(chosen.items()):
        note = f", skipped={skipped[g]} (blank or not a number)" if skipped.get(g) else ""
        if not vals:
            lines.append(f"{g}: no valid numeric readings{note}")
            continue
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        lines.append(f"{g}: n={len(vals)}, mean={statistics.mean(vals):.3g}, sd={sd:.2g}, "
                     f"min={min(vals):.3g}, max={max(vals):.3g}{note}")
    return "\n".join(lines)


summarize_csv.__doc__ = (
    f"Use this for any question about the data in {CSV_FILE.name}, which is not in the records "
    f"table. It answers questions about {QUESTION_IT_ANSWERS}. Give one {GROUP_COLUMN} name, or 'all' "
    "for every one. "
    "Returns one line per group with the count, mean, standard deviation, minimum and maximum, "
    "and how many readings were skipped as blank or not a number, so the answer rests on actual "
    "numbers rather than on a guess."
)


if __name__ == "__main__":
    print("what the model reads (the docstring):")
    print(summarize_csv.__doc__)
    print("\nall groups:")
    print(summarize_csv("all"))
    print("\none group:")
    first = ""
    if CSV_FILE.exists():
        with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
            first = next(csv.DictReader(f), {}).get(GROUP_COLUMN, "")
    print(summarize_csv(first or "all"))
    print("\na bad input:")
    print(summarize_csv("no such group"))
