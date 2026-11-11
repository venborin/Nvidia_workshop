"""Stop 4: put the model's numbers next to the picture they came from.

    python 04_see/compare.py <image> <extracted.csv> [<truth.csv>]
    python 04_see/compare.py <image> <extracted.csv> --yscale log     draw the y axis logarithmic
    python 04_see/compare.py <image> <extracted.csv> --xscale linear  draw the x axis linear

Always writes results/seen/<image-stem>-compare.png: the original image beside
a fresh plot of the extracted CSV. If there is a truth CSV (given, or a CSV
with the same name next to the image, as every shipped chart has), it also
draws truth and extracted on the same axes, and prints and saves an error
table, results/seen/<image-stem>-errors.csv.

The replot's scales: linear, unless a y axis's values are all positive and
span more than three decades, which is drawn logarithmic. --xscale and
--yscale (log or linear) override that. Two plots only look alike when their
scales match, so set them to match the original before judging the table.

The error table's first row is the x axis (kind "x axis"):
    matched     true x values that have an extracted point near them, of all of them
    mean_err    mean distance between those x values and the extracted ones,
    max_err     and the largest, in the x axis's units (empty for categories)
    pct_range   mean_err as a percent of the span of the true x values
    extra       extracted points (or categories) that match no true point
    duplicates  extracted points that repeat an x value (or category) already given

Then one row per truth column (kind "series" or "error bar"):
    matched     truth points the model gave a value for, out of all of them
    mean_err    mean absolute error, in the data's units
    max_err     the largest absolute error, in the data's units
    pct_range   mean_err as a percent of the span of the true values on that
                y axis (lowest to highest true value; for a bar chart, zero to
                the tallest true bar). It is not the drawn axis, which usually
                runs further, so it is the stricter of the two.
    median_rel  the median error as a percent of the true value; the number to
                read for a logarithmic axis, where the range is dominated by
                the largest values

The first column of each CSV is the x axis. Other columns are matched by name
(ignoring units and capitals). An error-bar column with no name match takes
the error column that follows its matched series. What is still unmatched is
paired by order only when exactly as many truth and extracted columns of the
same kind are left; otherwise it stays unmatched and shows as 0 points read.
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                     # no screen needed in a Codespace
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / "results" / "seen"


# ---------- reading the columns ----------

def unit_of(column):
    """The units in parentheses at the end of a column name, or ''."""
    found = re.search(r"\(([^()]*)\)\s*$", str(column))
    return found.group(1).strip() if found else ""


def key_of(column):
    """A column name reduced for matching: no units, no capitals, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\([^()]*\)", "", str(column).lower()))


_ERROR_WORDS = {"err", "error", "sd", "se", "sem", "std", "uncertainty"}


def words_of(column):
    """The words of a column name, without units, capitals or the error word:
    'Female err (g)' gives {'female'}."""
    return set(re.findall(r"[a-z0-9]+", re.sub(r"\([^()]*\)", "", str(column).lower()))) - _ERROR_WORDS


def near_name(a, b):
    """True when two names are close enough to pair: one's words are all among
    the other's ('male' and 'male mass'), or one name begins with the other
    ('temp' and 'temperature', three letters or more). 'male' inside 'female'
    is not a match."""
    wa, wb = words_of(a), words_of(b)
    if wa and wb and (wa <= wb or wb <= wa):
        return True
    ka, kb = key_of(a), key_of(b)
    return min(len(ka), len(kb)) >= 3 and (ka.startswith(kb) or kb.startswith(ka))   # 'A' does not begin 'Adelie' closely enough


def is_error(column):
    """True for an error-bar column, such as 'control err (mg/L)'."""
    return bool(re.search(r"\b(err|error|sd|se|sem|std|uncertainty)\b", str(column).lower()))


def numeric_x(df):
    """True when the first column holds numbers (a line or scatter), False for categories (bars)."""
    return pd.api.types.is_numeric_dtype(df.iloc[:, 0])


def series_and_errors(df):
    """Pairs of (series column, its error column or None), in table order. An
    error column belongs to the series just before it."""
    pairs = []
    for col in df.columns[1:]:
        if is_error(col) and pairs and pairs[-1][1] is None:
            pairs[-1] = (pairs[-1][0], col)
        elif not is_error(col):
            pairs.append((col, None))
    return pairs


def pair_columns(truth, seen):
    """Which extracted column goes with each truth column. Returns (pairs, how):
    pairs is a list of (truth column, extracted column or None) in truth order;
    how is "by name" when every truth column was matched by name, otherwise
    "partly by order" (some pairs were made by order) or "incomplete" (some
    truth columns found no partner). Matching runs in three passes, and a match
    made in one pass is never undone by a later one:
      1. by name, one to one, an error column only with an error column:
         every exact name first, then names that share whole words or begin
         alike (so 'male' never takes 'female');
      2. an unmatched error column takes the error column that follows its
         matched series in the extracted table;
      3. by order, separately for series and for error columns, but only when
         exactly as many of that kind are left on both sides. Otherwise the
         rest stay unmatched rather than guessed."""
    t_cols, s_cols = list(truth.columns[1:]), list(seen.columns[1:])
    match, used, ordered = {}, set(), False

    for t in t_cols:                                        # pass 1a: exact names, all of them first
        same = [s for s in s_cols if key_of(s) == key_of(t) and is_error(s) == is_error(t) and s not in used]
        if same:
            match[t] = same[0]
            used.add(same[0])
    for t in t_cols:                                        # pass 1b: near names, whole words or a shared beginning
        if t in match:
            continue
        near = [s for s in s_cols if is_error(s) == is_error(t) and s not in used and near_name(s, t)]
        near.sort(key=lambda s: abs(len(key_of(s)) - len(key_of(t))))   # the closest in length wins
        if near:
            match[t] = near[0]
            used.add(near[0])

    def attach_errors():                                    # pass 2: error bars follow their series
        t_series_of = {e: s for s, e in series_and_errors(truth) if e}
        s_error_of = {s: e for s, e in series_and_errors(seen) if e}
        for t_err, t_ser in t_series_of.items():
            if t_err in match or t_ser not in match:
                continue
            candidate = s_error_of.get(match[t_ser])
            if candidate is not None and candidate not in used:
                match[t_err] = candidate
                used.add(candidate)

    attach_errors()
    for kind in (False, True):                              # pass 3: order, only when unambiguous
        t_left = [t for t in t_cols if t not in match and is_error(t) == kind]
        s_left = [s for s in s_cols if s not in used and is_error(s) == kind]
        if t_left and len(t_left) == len(s_left):
            for t, s in zip(t_left, s_left):
                match[t] = s
                used.add(s)
            ordered = True
        if not kind:
            attach_errors()                                 # a series matched by order brings its error bars
    pairs = [(t, match.get(t)) for t in t_cols]
    if any(s is None for _, s in pairs):
        how = "incomplete"
    elif ordered:
        how = "partly by order"
    else:
        how = "by name"
    return pairs, how


# ---------- drawing ----------

def plot_table(ax, df, style, label_prefix="", xscale=None, yscale=None):
    """Draw a table on ax: lines and markers for numeric x, grouped bars or
    points for categories. Series with different units than the first go on
    a second y axis, as a dual-axis figure would. xscale and yscale ("log" or
    "linear") override the automatic choice. Returns the axes used."""
    pairs = series_and_errors(df)
    units = [unit_of(s) for s, _ in pairs]
    first_unit = units[0] if units else ""
    other = ax.twinx() if any(u != first_unit for u in units) else None
    x = df.iloc[:, 0]
    if not numeric_x(df):
        x = np.arange(len(df))
        ax.set_xticks(x, df.iloc[:, 0].astype(str))
    width = 0.8 / max(1, len(pairs))
    for i, (col, err) in enumerate(pairs):
        target = other if (other is not None and unit_of(col) != first_unit) else ax
        y = pd.to_numeric(df[col], errors="coerce")
        yerr = pd.to_numeric(df[err], errors="coerce") if err else None
        label = label_prefix + re.sub(r"\s*\([^()]*\)\s*$", "", str(col))
        color = f"C{i}"
        if style == "bars" and not numeric_x(df):
            target.bar(x + (i - (len(pairs) - 1) / 2) * width, y, width, yerr=yerr, capsize=3,
                       color=color, alpha=0.8, label=label)
        else:
            offset = 0 if numeric_x(df) else (i - (len(pairs) - 1) / 2) * width
            marker = {"truth": "o", "seen": "x", "plain": "o"}[style if style != "bars" else "plain"]
            line = "-" if style == "plain" and numeric_x(df) else "none"
            target.errorbar(x + offset, y, yerr=yerr, fmt=marker, linestyle=line, ms=5, capsize=2,
                            color=color, alpha=0.55 if style == "truth" else 1,
                            mfc="none" if style == "truth" else color, label=label)
    for target, on_left in ((ax, True), (other, False)):
        if target is None:
            continue
        cols = [c for c, _ in pairs if (unit_of(c) == first_unit) == on_left]
        target.set_ylabel(", ".join(sorted({unit_of(c) for c in cols})))
        if yscale:
            target.set_yscale(yscale)
        elif _auto_log(df, cols):
            target.set_yscale("log")       # spans more than three decades: a guess at what the chart did
    if xscale and numeric_x(df):
        ax.set_xscale(xscale)
    ax.set_xlabel(str(df.columns[0]))
    return ax, other


def _auto_log(df, cols):
    """True when these columns' values are all positive and span more than three decades."""
    if not cols:
        return False
    values = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in cols]).dropna()
    return bool(len(values) and (values > 0).all() and values.max() / values.min() > 1000)


def _y_axes(df):
    """The series on the left y axis and on the right one, grouped as plot_table draws them."""
    series = [c for c, _ in series_and_errors(df)]
    first_unit = unit_of(series[0]) if series else ""
    return ([c for c in series if unit_of(c) == first_unit], [c for c in series if unit_of(c) != first_unit])


def scales_used(df, xscale=None, yscale=None):
    """A sentence saying how the replot's axes were drawn, so a reader can check
    them against the original before judging the table."""
    if yscale:
        y = f"y axis {yscale} (as asked)"
    else:
        left, right = _y_axes(df)
        said = {True: "logarithmic (values span more than three decades)", False: "linear"}
        if not right:
            y = f"y axis {said[_auto_log(df, left)]}"
        elif _auto_log(df, left) == _auto_log(df, right):
            y = f"both y axes {said[_auto_log(df, left)]}"
        else:
            y = f"left y axis {said[_auto_log(df, left)]}, right y axis {said[_auto_log(df, right)]}"
    x = f"x axis {xscale} (as asked)" if xscale else "x axis linear"
    return f"Replot drawn with {x}, {y}. If the original uses other scales, rerun with --xscale or --yscale (log or linear)."


def draw(image_path, seen, truth, out_path, xscale=None, yscale=None):
    """The comparison figure: original | replot | (truth and extracted overlaid)."""
    panels = 3 if truth is not None else 2
    fig, axes = plt.subplots(1, panels, figsize=(5.2 * panels, 4.2))
    axes[0].imshow(plt.imread(str(image_path)))
    axes[0].set_title("Original image")
    axes[0].axis("off")
    style = "plain" if numeric_x(seen) else "bars"
    a, b = plot_table(axes[1], seen, style, xscale=xscale, yscale=yscale)
    axes[1].set_title("Replotted from the extracted CSV")
    _legend(a, b)
    if truth is not None:
        a, b = plot_table(axes[2], truth, "truth", "true: ", xscale=xscale, yscale=yscale)
        # Give the extracted columns the truth names, so each lands on its own axis.
        renamed = seen.rename(columns={s: t for t, s in pair_columns(truth, seen)[0] if s is not None})
        _overlay(axes[2], b, renamed, truth)
        axes[2].set_title("Truth (circles) and extracted (crosses)")
        _legend(a, b)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _overlay(ax, twin, seen, truth):
    """Draw extracted values as crosses on the truth panel, on the matching axis."""
    first_unit = unit_of(series_and_errors(truth)[0][0])
    x_seen = seen.iloc[:, 0] if numeric_x(truth) else _category_positions(truth, seen)
    pairs = series_and_errors(truth)
    width = 0.8 / max(1, len(pairs))
    for i, (col, err) in enumerate(pairs):
        if col not in seen.columns:
            continue
        target = twin if (twin is not None and unit_of(col) != first_unit) else ax
        offset = 0 if numeric_x(truth) else (i - (len(pairs) - 1) / 2) * width
        yerr = pd.to_numeric(seen[err], errors="coerce") if err and err in seen.columns else None
        target.errorbar(np.asarray(x_seen, dtype=float) + offset, pd.to_numeric(seen[col], errors="coerce"),
                        yerr=yerr, fmt="x", ms=6, capsize=2, color=f"C{i}", label="seen: " + re.sub(r"\s*\([^()]*\)\s*$", "", str(col)))


def _category_positions(truth, seen):
    """Where each extracted category sits on the truth chart, by name. A
    category the chart does not have gets no place, so it is not drawn."""
    places = [np.nan] * len(seen)
    for t_index, s_index in enumerate(match_rows(truth, seen)):
        if s_index is not None:
            places[s_index] = t_index
    return places


def _legend(ax, twin):
    """One legend for both y axes."""
    handles, labels = ax.get_legend_handles_labels()
    if twin is not None:
        h2, l2 = twin.get_legend_handles_labels()
        handles, labels = handles + h2, labels + l2
    if handles:
        ax.legend(handles, labels, fontsize=7, frameon=False)


# ---------- measuring ----------

def match_rows(truth, seen):
    """For each truth row, the index of the extracted row at the same x, or None.
    Numbers: the nearest extracted x within 45 percent of the smallest gap
    between true x values, so one reading cannot stand for two neighbours.
    Categories: the same name, ignoring capitals, spaces and accents, or a
    name that shares whole words or begins alike. A category with no such
    partner stays unmatched: pairing by order would score a table of the
    wrong categories as correct."""
    if numeric_x(truth) and numeric_x(seen):
        tx = truth.iloc[:, 0].to_numpy(float)
        sx = seen.iloc[:, 0].to_numpy(float)
        gaps = np.diff(np.unique(tx))
        tolerance = 0.45 * gaps.min() if len(gaps) else np.inf
        matches = []
        for x in tx:
            nearest = int(np.nanargmin(np.abs(sx - x))) if len(sx) else None
            matches.append(nearest if nearest is not None and abs(sx[nearest] - x) <= tolerance else None)
        return matches
    return _match_categories(truth.iloc[:, 0].astype(str).tolist(), seen.iloc[:, 0].astype(str).tolist())


def _plain(name):
    """A category name without accents, so 'Adélie' matches 'Adelie'."""
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(name)) if not unicodedata.combining(ch))


def _match_categories(t_names, s_names):
    """For each true category, the index of the extracted row with that name, or None."""
    t_names, s_names = [_plain(n) for n in t_names], [_plain(n) for n in s_names]
    found, used = [None] * len(t_names), set()
    for exact in (True, False):                 # every exact name first, then near names
        for i, t in enumerate(t_names):
            if found[i] is not None:
                continue
            for j, s in enumerate(s_names):
                if j in used:
                    continue
                if (key_of(s) == key_of(t) and key_of(t)) if exact else near_name(s, t):
                    found[i] = j
                    used.add(j)
                    break
    return found


def axis_ranges(truth):
    """The span of the true values on each y axis (grouped by units). Error
    columns use the span of their series' axis. Bar charts start at zero."""
    spans = {}
    for unit in {unit_of(c) for c, _ in series_and_errors(truth)}:
        cols = [c for c, _ in series_and_errors(truth) if unit_of(c) == unit]
        values = truth[cols].apply(pd.to_numeric, errors="coerce").to_numpy(float).ravel()
        values = values[~np.isnan(values)]
        low = min(values.min(), 0) if not numeric_x(truth) else values.min()
        spans[unit] = (values.max() - low) or abs(values.max()) or 1.0
    return spans


def x_axis_row(truth, seen, rows_matched):
    """The x axis's row of the error table: how many true x values have an
    extracted point near them, how far the extracted x values are from the
    true ones, how many extracted points match no true point, and how many
    repeat an x value already given."""
    t_x, s_x = truth.columns[0], seen.columns[0]
    used = {i for i in rows_matched if i is not None}
    extra = len(seen) - len(used)
    if numeric_x(truth) and numeric_x(seen):
        sx = seen.iloc[:, 0].to_numpy(float)
        dup = int(pd.Series(sx).duplicated().sum())
        tx = truth.iloc[:, 0].to_numpy(float)
        dx = np.array([abs(sx[i] - x) for x, i in zip(tx, rows_matched) if i is not None])
        span = (np.nanmax(tx) - np.nanmin(tx)) or 1.0
        mean = _round(dx.mean()) if len(dx) else np.nan
        worst = _round(dx.max()) if len(dx) else np.nan
        pct = round(100 * dx.mean() / span, 1) if len(dx) else np.nan
    else:
        names = [key_of(c) for c in seen.iloc[:, 0].astype(str)]
        dup = int(pd.Series(names).duplicated().sum())
        mean = worst = pct = np.nan
    return {"kind": "x axis", "column": t_x, "matched to": s_x,
            "matched": f"{sum(i is not None for i in rows_matched)}/{len(truth)}",
            "mean_err": mean, "max_err": worst, "pct_range": pct, "median_rel": np.nan,
            "extra": extra, "duplicates": dup}


def error_table(truth, seen):
    """The x axis's row, then one row per truth column: how many points were
    read, and how far off."""
    pairs, how = pair_columns(truth, seen)
    rows_matched = match_rows(truth, seen)
    spans = axis_ranges(truth)
    rows = [x_axis_row(truth, seen, rows_matched)]
    for t_col, s_col in pairs:
        true = pd.to_numeric(truth[t_col], errors="coerce").to_numpy(float)
        got = (pd.to_numeric(seen[s_col], errors="coerce").to_numpy(float) if s_col is not None
               else np.full(len(seen), np.nan))        # a series the model left out
        read = np.array([got[i] if i is not None else np.nan for i in rows_matched])
        ok = ~np.isnan(true) & ~np.isnan(read)
        err = np.abs(read[ok] - true[ok])
        span = spans.get(unit_of(t_col), next(iter(spans.values())))
        rel = err / np.where(true[ok] != 0, np.abs(true[ok]), np.nan)
        rows.append({"kind": "error bar" if is_error(t_col) else "series",
                     "column": t_col, "matched to": s_col,
                     "matched": f"{ok.sum()}/{(~np.isnan(true)).sum()}",
                     "mean_err": _round(err.mean()) if ok.any() else np.nan,
                     "max_err": _round(err.max()) if ok.any() else np.nan,
                     "pct_range": round(100 * err.mean() / span, 1) if ok.any() else np.nan,
                     "median_rel": round(100 * np.nanmedian(rel), 1) if ok.any() and not np.isnan(rel).all() else np.nan,
                     "extra": np.nan, "duplicates": np.nan})
    table = pd.DataFrame(rows)
    for col in ("extra", "duplicates"):
        table[col] = table[col].astype("Int64")       # whole numbers, blank where they do not apply
    return table, how


def _round(value):
    """Three significant figures, so 0.0123 and 2,345,000 both print sensibly."""
    return float(f"{value:.3g}")


def compare(image_path, seen_csv, truth_csv=None, quiet=False, xscale=None, yscale=None):
    """Write the comparison figure and, given truth, the error table. Returns
    the table (a DataFrame) or None when there is no truth to measure against."""
    image_path, seen_csv = Path(image_path), Path(seen_csv)
    stem = image_path.stem
    if truth_csv is None and image_path.with_suffix(".csv").exists():
        truth_csv = image_path.with_suffix(".csv")
        if not quiet:
            print(f"Truth found beside the image: {truth_csv}")
    seen = pd.read_csv(seen_csv)
    truth = pd.read_csv(truth_csv) if truth_csv else None
    SEEN.mkdir(parents=True, exist_ok=True)
    out = SEEN / f"{stem}-compare.png"
    table, how = (error_table(truth, seen) if truth is not None else (None, None))
    draw(image_path, seen, truth, out, xscale=xscale, yscale=yscale)
    if not quiet:
        print(f"Wrote {out.relative_to(ROOT)}")
        print(scales_used(seen, xscale, yscale))
    if table is None:
        if not quiet:
            print("No truth CSV, so no error table. Look at the two panels side by side.")
        return None
    table.to_csv(SEEN / f"{stem}-errors.csv", index=False)
    if not quiet:
        if how != "by name":
            print("Not every column matched by name. How each truth column was paired:")
            for t, s in pair_columns(truth, seen)[0]:
                print(f"   truth '{t}'  <->  extracted '{s}'" if s else f"   truth '{t}'  <->  nothing (left out, or too ambiguous to pair)")
        shown = table.drop(columns="matched to").astype(object)
        print(shown.where(table.drop(columns="matched to").notna(), "").to_string(index=False))
        x = table.iloc[0]
        if not (numeric_x(truth) and numeric_x(seen)):
            missing = [str(name) for name, i in zip(truth.iloc[:, 0], match_rows(truth, seen)) if i is None]
            if missing:
                print(f"No extracted row is named for {', '.join(missing)}: "
                      f"{'that category is' if len(missing) == 1 else 'those categories are'} "
                      "counted as not read, and rows with other names as extra. Rows are never paired by order.")
        if x["extra"] or x["duplicates"]:
            print(f"The model gave {x['extra']} point(s) that match no true point and {x['duplicates']} that repeat "
                  "an x value: a full-looking table can still contain points the chart does not have.")
        print(f"Saved {(SEEN / f'{stem}-errors.csv').relative_to(ROOT)}")
    return table


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    scales = {}
    for flag in ("--xscale", "--yscale"):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args) or args[i + 1] not in ("log", "linear"):
                raise SystemExit(f"{flag} takes log or linear.")
            scales[flag[2:]] = args[i + 1]
            del args[i:i + 2]
    for path in args:
        if not Path(path).is_file():
            raise SystemExit(f"No such file: {path}")
    compare(args[0], args[1], args[2] if len(args) > 2 else None, **scales)


if __name__ == "__main__":
    main()
