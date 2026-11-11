"""Stop 4 smoke test: every shipped chart through the live model, measured.

    python 04_see/smoke_test.py            each chart once (about two minutes, under two cents)
    python 04_see/smoke_test.py --runs 3   each chart three times, to see how much answers vary

For each chart: see.py --extract, then compare.py against the truth CSV.
Prints one line per run (points read; for the worst series, mean error as a
percent of the true data's span and median relative error; for error bars, the
worst percent of span; extra or repeated x values; seconds, cost, with +? when
an attempt's cost was not reported; provider) and a final line with totals. Exits with status 1 if any run failed to give a table pandas can read.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compare                                         # noqa: E402
import see                                             # noqa: E402
llm = see.llm


def summary(table):
    """Points read, then the worst series and the worst error bars, then the
    x axis's extra and repeated points, from one error table."""
    x = table[table["kind"] == "x axis"].iloc[0]
    table = table[table["kind"] != "x axis"]
    read = sum(int(m.split("/")[0]) for m in table["matched"])
    total = sum(int(m.split("/")[1]) for m in table["matched"])
    bars = table["kind"] == "error bar"
    text = (f"{read:>3}/{total:<3} points  series: worst {table[~bars]['pct_range'].max():4.1f}% of range, "
            f"median rel {table[~bars]['median_rel'].max():4.1f}%")
    if bars.any():
        text += f"  error bars: worst {table[bars]['pct_range'].max():4.1f}% of range"
    if x["max_err"] == x["max_err"] and x["max_err"] > 0:          # not NaN, not zero
        text += f"  x off by up to {x['max_err']:g}"
    if x["extra"] or x["duplicates"]:
        text += f"  x: {x['extra']} extra, {x['duplicates']} repeated"
    return text


def main():
    runs = int(sys.argv[sys.argv.index("--runs") + 1]) if "--runs" in sys.argv else 1
    charts = sorted((HERE / "charts").glob("*.png"))
    failures, started = 0, time.time()
    for chart in charts:
        for run in range(1, runs + 1):
            spent_before = llm.TOTAL["cost"]
            label = f"{chart.stem:<20} run {run}"
            try:
                csv_path = see.extract(chart, quiet=True)
            except (RuntimeError, SystemExit) as err:
                csv_path = None
                print(f"   {err}")
            cost = llm.TOTAL["cost"] - spent_before
            unknown = "+?" if see.INFO.get("cost_unknown") else ""
            where = f"{see.INFO.get('seconds', 0):5.1f} s  ${cost:.4f}{unknown}  {see.INFO.get('provider')}"
            if csv_path is None:
                failures += 1
                print(f"{label}  FAILED: no usable table                         {where}")
                continue
            table = compare.compare(chart, csv_path, quiet=True)
            how = compare.pair_columns(compare.pd.read_csv(chart.with_suffix(".csv")),
                                       compare.pd.read_csv(csv_path))[1]
            print(f"{label}  {summary(table)}  {where}" + (f"  (columns {how})" if how != "by name" else ""))
            if runs > 1:   # keep each run's files so they can be compared afterwards
                for name in (f"{chart.stem}.csv", f"{chart.stem}-errors.csv", f"{chart.stem}-compare.png",
                             f"{chart.stem}.reply.txt"):
                    src = see.SEEN / name
                    if src.exists():
                        src.replace(see.SEEN / name.replace(chart.stem, f"{chart.stem}.run{run}"))
    print(f"\n{len(charts) * runs} runs, {failures} failed, {llm.TOTAL['calls']} model calls, "
          f"{llm.TOTAL['completion_tokens']:,} output tokens, ${llm.TOTAL['cost']:.4f}, "
          f"{time.time() - started:.0f} s. Results in {see.SEEN.relative_to(llm.ROOT)}/")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
