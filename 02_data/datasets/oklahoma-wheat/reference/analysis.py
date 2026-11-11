"""Reference analysis for the Oklahoma county wheat fallback (Stop 2).

Rebuilds every figure and every number in report.md from the raw CSV.
Run from the labs/ folder:

    python 02_data/datasets/oklahoma-wheat/reference/analysis.py

Question: how has county winter wheat yield in Oklahoma changed from 2000 to
2025, and how much does it swing from year to year?
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "ok_county_winter_wheat_2000-2025.csv"
FIG = HERE / "figures"
REPORT = HERE / "report.md"
STATS = {
    "WHEAT, WINTER - YIELD, MEASURED IN BU / ACRE": "yield_bu_ac",
    "WHEAT, WINTER - ACRES HARVESTED": "harvested_ac",
    "WHEAT, WINTER - ACRES PLANTED": "planted_ac",
    "WHEAT, WINTER - PRODUCTION, MEASURED IN BU": "production_bu",
}

# ---------------------------------------------------------------- load
raw = pd.read_csv(RAW, dtype=str, keep_default_na=False)
n_rows, n_cols = raw.shape
print(f"rows={n_rows} columns={n_cols} (long format: one statistic per row)")

# ---------------------------------------------------------------- explore
years = sorted(raw["YEAR"].astype(int).unique())
absent_years = sorted(set(range(years[0], years[-1] + 1)) - set(years))
print(f"years {years[0]}-{years[-1]}, absent: {absent_years}")
print("rows by production practice:", raw["PRODN_PRACTICE_DESC"].value_counts().to_dict())
combined = raw["COUNTY_CODE"] == "998"
print(f"rows for combined counties (county code 998): {int(combined.sum())}")
print("CV_% filled in:", int((raw["CV_%"] != "").sum()), "of", n_rows)

# ---------------------------------------------------------------- exclusions and reshape
keep = (raw["PRODN_PRACTICE_DESC"] == "ALL PRODUCTION PRACTICES") & ~combined & raw["SHORT_DESC"].isin(STATS)
practice = raw["PRODN_PRACTICE_DESC"] != "ALL PRODUCTION PRACTICES"
n_practice = int(practice.sum())
n_both = int((practice & combined).sum())            # rows that are both: counted once in the total
n_excluded = int((practice | combined).sum())
d = raw[keep].copy()
d["value"] = pd.to_numeric(d["VALUE"].str.replace(",", "", regex=False))  # "10,289,000" -> 10289000
d["stat"] = d["SHORT_DESC"].map(STATS)
d["year"] = d["YEAR"].astype(int)
d["county"] = d["COUNTY_NAME"].str.title()
assert not d.duplicated(["year", "county", "stat"]).any(), "duplicate county-year-statistic rows"
cy = d.pivot_table(index=["year", "county", "ASD_DESC"], columns="stat", values="value", aggfunc="first").reset_index()
cy = cy.dropna(subset=["yield_bu_ac"])
n_cy, n_counties = len(cy), cy["county"].nunique()
per_year = cy.groupby("year")["county"].nunique()
print(f"county-years with a yield={n_cy}, counties={n_counties}, counties per year {per_year.min()}-{per_year.max()}")
print(f"dropped: {n_practice} irrigated/non-irrigated rows and {int(combined.sum())} combined-county rows; "
      f"{n_both} rows are both, so {n_excluded} rows are dropped in all")
print("counties published per year:", per_year.to_dict())

# ---------------------------------------------------------------- numbers
both = cy.dropna(subset=["production_bu", "harvested_ac"])
recomputed = both["production_bu"] / both["harvested_ac"]
# Published yield is rounded to 0.1 bu, or to whole bushels in early years, so allow half that.
step = both["yield_bu_ac"].map(lambda v: 0.1 if v != round(v) else 1.0)
n_consistent = int(((recomputed - both["yield_bu_ac"]).abs() <= step / 2 + 1e-9).sum())
print(f"yield = production / harvested acres within rounding for {n_consistent} of {len(both)} county-years")

state = both.groupby("year").agg(production=("production_bu", "sum"), harvested=("harvested_ac", "sum"),
                                 planted=("planted_ac", "sum"))
state["weighted_yield"] = state["production"] / state["harvested"]
state["median_county"] = cy.groupby("year")["yield_bu_ac"].median()
state["harvested_share"] = state["harvested"] / state["planted"]
print("by year:")
print(state.assign(counties=per_year)[["counties", "weighted_yield", "median_county", "harvested_share"]].round(2).to_string())
best, worst = state["weighted_yield"].idxmax(), state["weighted_yield"].idxmin()
first_years = state.loc[state.index <= 2004, "weighted_yield"].mean()
last_years = state.loc[state.index >= 2021, "weighted_yield"].mean()
share_mean = state["harvested_share"].mean()
print(f"best year {best} ({state.loc[best, 'weighted_yield']:.1f}), worst {worst} ({state.loc[worst, 'weighted_yield']:.1f})")
print(f"mean of 2000-2004 = {first_years:.1f}; mean of 2021-2025 (2024 absent) = {last_years:.1f}")
print(f"counties published 2000-2004: {per_year.loc[:2004].min()} to {per_year.loc[:2004].max()}; "
      f"2021-2025: {per_year.loc[2021:].min()} to {per_year.loc[2021:].max()}")
print(f"mean harvested share of planted acres, over the years: {share_mean:.0%}")

hand_year = 2025
hand = cy.loc[cy["year"] == hand_year, "yield_bu_ac"]
print(f"hand-check aggregate: {len(hand)} counties in {hand_year}, mean county yield {hand.mean():.2f} bu/acre")

# Reindex to every calendar year so the plotted lines break at 2024 instead of bridging it.
full_years = range(years[0], years[-1] + 1)
district = cy.groupby(["year", "ASD_DESC"])["yield_bu_ac"].median().unstack().reindex(full_years)
state_plot = state.reindex(full_years)

# ---------------------------------------------------------------- figures
FIG.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.boxplot([cy.loc[cy["year"] == y, "yield_bu_ac"] for y in state.index], positions=list(state.index), widths=0.6)
ax.set_xticks(list(state.index), [str(y) for y in state.index], rotation=90)
ax.set(ylabel="County yield, bu per harvested acre", title="Winter wheat yield across Oklahoma counties (2024: no county estimates)")
fig.tight_layout()
fig.savefig(FIG / "1_county_yield_by_year.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(state_plot.index, state_plot["weighted_yield"], marker="o", label="Production / harvested acres, reported counties")
ax.plot(state_plot.index, state_plot["median_county"], marker="s", ls="--", label="Median county")
ax.set(xlabel="Harvest year", ylabel="Bu per harvested acre", title="Statewide yield from the county estimates")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "2_state_yield_by_year.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
for asd in district.columns:
    ax.plot(district.index, district[asd], marker=".", lw=1, label=asd.title())
ax.set(xlabel="Harvest year", ylabel="Median county yield, bu per acre", title="By crop reporting district")
ax.legend(frameon=False, fontsize=7, ncol=3)
fig.tight_layout()
fig.savefig(FIG / "3_district_yield_by_year.png", dpi=150)
plt.close(fig)
print("figures written:", ", ".join(sorted(p.name for p in FIG.glob("*.png"))))

# ---------------------------------------------------------------- report
rows = "\n".join(
    f"| {y} | {per_year[y]} | {r.weighted_yield:.1f} | {r.median_county:.1f} | {r.harvested_share:.0%} |"
    for y, r in state.iterrows()
)
report = f"""# Oklahoma county winter wheat yield, 2000 to 2025

Generated by analysis.py from ok_county_winter_wheat_2000-2025.csv. Every number below is
computed by the script; rerun it to rebuild this file and the three figures.

## The data

The raw file is long: {n_rows} rows, each one statistic (yield, acres planted, acres
harvested or production) for one county and year. Values are text with thousands
separators. There are no county estimates for {', '.join(map(str, absent_years))}. Dropped:
{n_practice} rows that split a county into irrigated and non-irrigated (published only to
2009; the all-practices rows already cover them) and {int(combined.sum())} rows with county
code 998 ("OTHER (COMBINED) COUNTIES" within a district, "OTHER COUNTIES" statewide from
2020), which pool counties NASS did not publish separately. {n_both} rows are both, so {n_excluded}
rows are dropped in all, not the sum of the two. After reshaping, {n_cy} county-years have a yield, from {n_counties} counties;
the number of counties published per year ranges from {per_year.min()} to {per_year.max()}, and fewer are published after 2007.
As a consistency check, production divided by harvested acres reproduces the published
yield to within its rounding (0.1 bushel, or a whole bushel where NASS published whole
bushels) for {n_consistent} of {len(both)} county-years.

## What the plots show

County yields swing far more from year to year than they trend (figure 1). Production
over harvested acres for the published counties was highest in {best}
({state.loc[best, 'weighted_yield']:.1f} bu per acre) and lowest in {worst}
({state.loc[worst, 'weighted_yield']:.1f}). The 2000 to 2004 average was {first_years:.1f}
and the 2021 to 2025 average {last_years:.1f} (figure 2), but these average different sets of
published counties ({per_year.loc[:2004].min()} to {per_year.loc[:2004].max()} then, {per_year.loc[2021:].min()} to {per_year.loc[2021:].max()} now), so they
are not a trend; extension.md compares each county with itself. Districts move together in the
bad years (figure 3), which is what statewide weather does. On average only {share_mean:.0%} of
planted acres were harvested for grain; much Oklahoma wheat is grazed by cattle or
abandoned.

| Year | Counties | Production / harvested (bu/ac) | Median county (bu/ac) | Harvested share of planted |
|---|---|---|---|---|
{rows}

## Independent check

In {hand_year}, {len(hand)} counties have a yield, with a mean of {hand.mean():.2f} bu per acre.
Recompute with

    python -c "import pandas as pd; d=pd.read_csv('02_data/datasets/oklahoma-wheat/ok_county_winter_wheat_2000-2025.csv', dtype=str); y=d[(d.YEAR=='{hand_year}')&(d.STATISTICCAT_DESC=='YIELD')&(d.PRODN_PRACTICE_DESC=='ALL PRODUCTION PRACTICES')&(d.COUNTY_CODE!='998')]; print(len(y), y.VALUE.astype(float).mean())"

## Figures

- figures/1_county_yield_by_year.png
- figures/2_state_yield_by_year.png
- figures/3_district_yield_by_year.png
"""
REPORT.write_text(report)
print("report written: report.md")
