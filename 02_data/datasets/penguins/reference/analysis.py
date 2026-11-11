"""Reference analysis for the palmerpenguins fallback (Stop 2).

Rebuilds every figure and every number in report.md from the raw CSV.
Run from the labs/ folder:

    python 02_data/datasets/penguins/reference/analysis.py

Question: how does bill (culmen) depth relate to bill length, and does the
answer change once species is taken into account?
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "penguins_raw.csv"
FIG = HERE / "figures"
REPORT = HERE / "report.md"

LENGTH = "Culmen Length (mm)"
DEPTH = "Culmen Depth (mm)"
MEASURES = [LENGTH, DEPTH, "Flipper Length (mm)", "Body Mass (g)"]
COLORS = {"Adelie": "#d55e00", "Chinstrap": "#6a3d9a", "Gentoo": "#1b9e77"}

# ---------------------------------------------------------------- load
raw = pd.read_csv(RAW)
n_rows, n_cols = raw.shape
raw["species"] = raw["Species"].str.split().str[0]  # "Adelie Penguin (Pygoscelis adeliae)" -> "Adelie"
print(f"rows={n_rows} columns={n_cols}")

# ---------------------------------------------------------------- explore
missing = raw[MEASURES + ["Sex", "Delta 15 N (o/oo)", "Delta 13 C (o/oo)"]].isna().sum()
print("missing values per column:")
print(missing.to_string())
no_measures = raw[raw[MEASURES].isna().all(axis=1)]
print("rows with no body measurements:", ", ".join(no_measures["Individual ID"] + " (" + no_measures["species"] + ")"))
n_sex_missing = int(raw["Sex"].isna().sum())
n_incomplete_clutch = int((raw["Clutch Completion"] == "No").sum())
print(f"sex missing: {n_sex_missing} birds; from nests never seen with a full clutch: {n_incomplete_clutch} birds")
counts = raw["species"].value_counts().sort_index()
print("birds per species:", counts.to_dict())

# ---------------------------------------------------------------- exclusions
data = raw.dropna(subset=[LENGTH, DEPTH]).copy()
n_used = len(data)
n_dropped = n_rows - n_used
print(f"rows used={n_used} dropped={n_dropped} (missing bill length or depth)")

# ---------------------------------------------------------------- numbers
pooled_r = data[LENGTH].corr(data[DEPTH])
pooled_slope, pooled_int = np.polyfit(data[LENGTH], data[DEPTH], 1)
print(f"pooled: r={pooled_r:.3f} slope={pooled_slope:.4f} mm/mm")

by_species = []
for sp, g in data.groupby("species"):
    slope, intercept = np.polyfit(g[LENGTH], g[DEPTH], 1)
    by_species.append({
        "species": sp,
        "n": len(g),
        "mean_length": g[LENGTH].mean(),
        "mean_depth": g[DEPTH].mean(),
        "r": g[LENGTH].corr(g[DEPTH]),
        "slope": slope,
        "intercept": intercept,
    })
by_species = pd.DataFrame(by_species).set_index("species")
print("by species:")
print(by_species.round(4).to_string())

# One aggregate a participant can recompute by hand or with a one-liner.
mean_depth_all = data[DEPTH].mean()
print(f"hand-check aggregate: mean culmen depth over {n_used} birds = {mean_depth_all:.2f} mm")

# ---------------------------------------------------------------- figures
FIG.mkdir(parents=True, exist_ok=True)
xs = np.linspace(data[LENGTH].min(), data[LENGTH].max(), 50)

fig, ax = plt.subplots(figsize=(6.5, 4.5))
ax.scatter(data[LENGTH], data[DEPTH], s=14, color="0.45", alpha=0.7)
ax.plot(xs, pooled_int + pooled_slope * xs, color="black", lw=2)
ax.set(xlabel="Bill (culmen) length, mm", ylabel="Bill (culmen) depth, mm",
       title=f"All species pooled: r = {pooled_r:.2f}")
fig.tight_layout()
fig.savefig(FIG / "1_depth_vs_length_pooled.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.5, 4.5))
for sp, g in data.groupby("species"):
    row = by_species.loc[sp]
    ax.scatter(g[LENGTH], g[DEPTH], s=14, alpha=0.7, color=COLORS[sp], label=f"{sp} (r = {row.r:.2f})")
    gx = np.linspace(g[LENGTH].min(), g[LENGTH].max(), 20)
    ax.plot(gx, row.intercept + row.slope * gx, color=COLORS[sp], lw=2)
ax.set(xlabel="Bill (culmen) length, mm", ylabel="Bill (culmen) depth, mm",
       title="Within each species the slope is positive")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "2_depth_vs_length_by_species.png", dpi=150)
plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharex=True, sharey=True)
for ax, (sp, g) in zip(axes, data.groupby("species")):
    row = by_species.loc[sp]
    ax.scatter(data[LENGTH], data[DEPTH], s=6, color="0.85")
    ax.scatter(g[LENGTH], g[DEPTH], s=12, alpha=0.8, color=COLORS[sp])
    ax.plot(xs, pooled_int + pooled_slope * xs, color="black", lw=1, ls="--")
    gx = np.linspace(g[LENGTH].min(), g[LENGTH].max(), 20)
    ax.plot(gx, row.intercept + row.slope * gx, color=COLORS[sp], lw=2)
    ax.set(title=f"{sp}: slope {row.slope:+.3f}", xlabel="Bill length, mm")
axes[0].set_ylabel("Bill depth, mm")
fig.suptitle("Each species against the pooled line (dashed): the species gap drives the pooled slope")
fig.tight_layout()
fig.savefig(FIG / "3_depth_vs_length_panels.png", dpi=150)
plt.close(fig)
print("figures written:", ", ".join(sorted(p.name for p in FIG.glob("*.png"))))

# ---------------------------------------------------------------- report
rows = "\n".join(
    f"| {sp} | {int(r.n)} | {r.mean_length:.1f} | {r.mean_depth:.1f} | {r.r:.2f} | {r.slope:.3f} |"
    for sp, r in by_species.iterrows()
)
report = f"""# Bill depth against bill length in the Palmer penguins

Generated by analysis.py from penguins_raw.csv. Every number below is computed by
the script; rerun it to rebuild this file and the three figures.

## The data

The raw file has {n_rows} rows (one adult penguin each) and {n_cols} columns. Birds per
species: Adelie {counts['Adelie']}, Chinstrap {counts['Chinstrap']}, Gentoo {counts['Gentoo']}.
Two birds have no body measurements at all ({', '.join(no_measures['Individual ID'])}), so
{n_dropped} rows are dropped and {n_used} are used. Sex is missing for {n_sex_missing} birds
and {n_incomplete_clutch} birds come from nests never seen with a full clutch; neither matters
for this question, so those birds stay in.

## What the plots show

Pooled across species, deeper bills go with shorter bills: r = {pooled_r:.2f}, slope
{pooled_slope:.3f} mm of depth per mm of length (figure 1). Within every species the
relationship is positive (figure 2):

| Species | n | Mean length (mm) | Mean depth (mm) | r | Slope (mm/mm) |
|---|---|---|---|---|---|
{rows}

The reversal happens because species differ in both measurements at once: Gentoo bills
are long and shallow, Adelie bills short and deep (figure 3, where each species sits against the dashed pooled line). Species is the confounder.
Pooling hides it and reports a negative relationship that holds for no species.

## Independent check

Mean culmen depth over the {n_used} birds used is {mean_depth_all:.2f} mm. Recompute it with

    python -c "import pandas as pd; print(pd.read_csv('02_data/datasets/penguins/penguins_raw.csv')['Culmen Depth (mm)'].mean())"

## Figures

- figures/1_depth_vs_length_pooled.png
- figures/2_depth_vs_length_by_species.png
- figures/3_depth_vs_length_panels.png
"""
REPORT.write_text(report)
print(f"report written: {REPORT.relative_to(HERE.parent.parent.parent.parent)}")
