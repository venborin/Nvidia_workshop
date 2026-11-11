"""Reference analysis for the Stillwater weather fallback (Stop 2).

Rebuilds every figure and every number in report.md from the raw CSV.
Run from the labs/ folder:

    python 02_data/datasets/stillwater-weather/reference/analysis.py

Question: are days with measurable rain cooler than dry days at Stillwater
Regional Airport, and how much of the gap is just the season?
"""
import calendar as cal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "stillwater_daily_2021-2025.csv"
FIG = HERE / "figures"
REPORT = HERE / "report.md"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------------------------------------------------------- load
raw = pd.read_csv(RAW, parse_dates=["DATE"])
n_rows, n_cols = raw.shape
station = raw["NAME"].iloc[0]
first, last = raw["DATE"].min(), raw["DATE"].max()
print(f"rows={n_rows} columns={n_cols} station={station!r} from {first.date()} to {last.date()}")

# ---------------------------------------------------------------- explore
calendar = pd.date_range(first, last, freq="D")
absent = calendar.difference(raw["DATE"])
print(f"calendar days={len(calendar)} absent dates={[d.date().isoformat() for d in absent]}")
missing = raw[["TMAX", "TMIN", "PRCP", "AWND", "SNOW", "SNWD"]].isna().sum()
print("blank values per column:")
print(missing.to_string())
trace = raw["PRCP_ATTRIBUTES"].fillna("").str.startswith("T")
n_trace = int(trace.sum())
print(f"trace precipitation days (PRCP recorded as 0.00 with flag T)={n_trace}")
n_z = int(raw.filter(like="_ATTRIBUTES").apply(lambda c: c.fillna("").str.contains("Z")).any(axis=1).sum())
print(f"rows with a value replaced by an official NCEI investigation (source flag Z)={n_z}")
coldest = raw.loc[raw["TMIN"].idxmin()]
hottest = raw.loc[raw["TMAX"].idxmax()]
print(f"coldest TMIN {coldest.TMIN:.0f} F on {coldest.DATE.date()}; hottest TMAX {hottest.TMAX:.0f} F on {hottest.DATE.date()}")

# ---------------------------------------------------------------- exclusions
d = raw.dropna(subset=["TMAX", "PRCP"]).copy()
n_used = len(d)
n_dropped = n_rows - n_used
d["wet"] = d["PRCP"] >= 0.01  # measurable rain; trace days (0.00, flag T) count as dry
d["month"] = d["DATE"].dt.month
print(f"days used={n_used} dropped={n_dropped} (blank TMAX or PRCP)")

# ---------------------------------------------------------------- numbers
n_wet, n_dry = int(d["wet"].sum()), int((~d["wet"]).sum())
mean_wet = d.loc[d["wet"], "TMAX"].mean()
mean_dry = d.loc[~d["wet"], "TMAX"].mean()
raw_gap = mean_wet - mean_dry
print(f"wet days={n_wet} dry days={n_dry}")
print(f"mean TMAX wet={mean_wet:.1f} F dry={mean_dry:.1f} F gap={raw_gap:+.1f} F")

monthly = d.pivot_table(index="month", columns="wet", values="TMAX", aggfunc="mean")
monthly.columns = ["dry", "wet"]
monthly["gap"] = monthly["wet"] - monthly["dry"]
monthly["wet_share"] = d.groupby("month")["wet"].mean()
monthly["n_wet"] = d.groupby("month")["wet"].sum()
print("by month:")
print(monthly.round(2).to_string())
# Same-month comparison: the average of the twelve monthly gaps, weighted by wet days.
within_gap = (monthly["gap"] * monthly["n_wet"]).sum() / monthly["n_wet"].sum()
print(f"within-month gap (weighted by wet days)={within_gap:+.1f} F")
wettest = monthly["wet_share"].idxmax()
driest = monthly["wet_share"].idxmin()

mean_tmax_all = d["TMAX"].mean()
print(f"hand-check aggregate: mean TMAX over {n_used} days = {mean_tmax_all:.2f} F; wet days = {n_wet}")

# ---------------------------------------------------------------- figures
FIG.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(5.5, 4.5))
ax.boxplot([d.loc[~d["wet"], "TMAX"], d.loc[d["wet"], "TMAX"]], widths=0.5)
ax.set_xticks([1, 2], [f"Dry or trace\n(n = {n_dry})", f"Measurable rain\n(n = {n_wet})"])
ax.set(ylabel="Daily maximum temperature, F", title=f"All days, 2021 to 2025: gap {raw_gap:+.1f} F")
fig.tight_layout()
fig.savefig(FIG / "1_tmax_wet_vs_dry.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(monthly.index, monthly["dry"], marker="o", color="#d55e00", label="Dry or trace")
ax.plot(monthly.index, monthly["wet"], marker="o", color="#0072b2", label="Measurable rain")
ax.set_xticks(range(1, 13), MONTHS)
ax.set(ylabel="Mean daily maximum, F", title=f"Same month, wet against dry: weighted gap {within_gap:+.1f} F")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "2_tmax_by_month_wet_vs_dry.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(d["DATE"], d["TMAX"], color="0.75", lw=0.6)
ax.scatter(d.loc[d["wet"], "DATE"], d.loc[d["wet"], "TMAX"], s=6, color="#0072b2", label="Day with measurable rain")
ax.set(ylabel="Daily maximum, F", title="Daily maximum temperature, Stillwater Regional Airport")
ax.legend(frameon=False, loc="lower left")
fig.tight_layout()
fig.savefig(FIG / "3_tmax_timeline.png", dpi=150)
plt.close(fig)
print("figures written:", ", ".join(sorted(p.name for p in FIG.glob("*.png"))))

# ---------------------------------------------------------------- report
if abs(within_gap) > abs(raw_gap):
    season_sentence = (
        "The same-month gap is larger than the raw one: rain falls most often in the warm "
        "spring and early summer months, which lifts the average high of wet days and hides "
        "part of the cooling. Season is a confounder here, and ignoring it understates the effect."
    )
else:
    season_sentence = (
        "The same-month gap is smaller than the raw one, so part of the raw gap is season, "
        "not rain. Season is a confounder here, and ignoring it overstates the effect."
    )
print("season:", season_sentence)

rows = "\n".join(
    f"| {MONTHS[m - 1]} | {r.dry:.1f} | {r.wet:.1f} | {r.gap:+.1f} | {r.wet_share:.0%} |"
    for m, r in monthly.iterrows()
)
report = f"""# Rainy days and daily high temperature at Stillwater, 2021 to 2025

Generated by analysis.py from stillwater_daily_2021-2025.csv. Every number below is
computed by the script; rerun it to rebuild this file and the three figures.

## The data

{n_rows} rows, one per day, from {first.date()} to {last.date()} at {station}. The calendar
has {len(calendar)} days, so {len(absent)} dates are absent from the file entirely
({', '.join(d.date().isoformat() for d in absent)}). Blank values: TMAX {missing['TMAX']},
PRCP {missing['PRCP']}. Days used: {n_used}; dropped: {n_dropped} (blank high temperature
or precipitation). {n_trace} days record a trace of precipitation as 0.00 with flag T;
they count as dry here. Snowfall and snow depth are blank on most days and are not used.
Extremes: {coldest.TMIN:.0f} F on {coldest.DATE.date()} and {hottest.TMAX:.0f} F on {hottest.DATE.date()}.

## What the plots show

Days with measurable rain (0.01 inch or more, {n_wet} days) had a mean high of
{mean_wet:.1f} F against {mean_dry:.1f} F on the other {n_dry} days, a gap of {raw_gap:+.1f} F
(figure 1). Rain is not spread evenly over the year: {cal.month_name[wettest]} had rain on
{monthly.loc[wettest, 'wet_share']:.0%} of days and {cal.month_name[driest]} on
{monthly.loc[driest, 'wet_share']:.0%}. Comparing wet and dry days within the same month
(figure 2) gives a weighted gap of {within_gap:+.1f} F. {season_sentence}

| Month | Dry mean high (F) | Wet mean high (F) | Gap (F) | Share of days wet |
|---|---|---|---|---|
{rows}

## Independent check

Mean daily high over the {n_used} days used is {mean_tmax_all:.2f} F, and {n_wet} of them had
measurable rain. Recompute with

    python -c "import pandas as pd; d=pd.read_csv('02_data/datasets/stillwater-weather/stillwater_daily_2021-2025.csv').dropna(subset=['TMAX','PRCP']); print(d.TMAX.mean(), (d.PRCP>=0.01).sum())"

## Figures

- figures/1_tmax_wet_vs_dry.png
- figures/2_tmax_by_month_wet_vs_dry.png
- figures/3_tmax_timeline.png
"""
REPORT.write_text(report)
print("report written: report.md")
