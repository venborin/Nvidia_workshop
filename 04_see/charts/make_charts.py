"""Rebuild the six shipped charts and the truth CSV behind each one.

    python 04_see/charts/make_charts.py

Every chart is drawn from exactly the numbers written to its CSV, so the CSV
is the truth the extraction is measured against. The synthetic charts use a
fixed random seed, so they come out the same every time. The two charts made
from public data (Mauna Loa CO2, Palmer penguins) read the numbers from their
CSV, which was derived once from the public files; SOURCES.md says how.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                     # no screen needed in a Codespace
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DPI = 150

# Journal-like styling: sans-serif, thin axes, ticks outward, no top/right box.
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.labelsize": 10,
    "axes.titlesize": 10, "legend.fontsize": 9, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out", "lines.linewidth": 1.4,
})


def save(fig, stem, df=None):
    """Write the PNG, and the truth CSV when one is given."""
    fig.tight_layout()
    fig.savefig(HERE / f"{stem}.png", dpi=DPI)
    plt.close(fig)
    if df is not None:
        df.to_csv(HERE / f"{stem}.csv", index=False)
    print("wrote", stem)


def co2_line():
    """Two series on one line chart: real NOAA annual means, 2000 to 2025."""
    df = pd.read_csv(HERE / "co2_line.csv")
    x, a, b = df.columns
    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.plot(df[x], df[a], "o-", ms=3.5, label="Mauna Loa, Hawaii")
    ax.plot(df[x], df[b], "s--", ms=3.5, label="Global marine surface")
    ax.set_xlabel("Year")
    ax.set_ylabel("Atmospheric CO$_2$ (ppm)")
    ax.legend(loc="upper left")
    save(fig, "co2_line")


def calibration_scatter():
    """Scatter with error bars: a synthetic calibration curve, mean and SD of three replicates."""
    rng = np.random.default_rng(4)
    conc = np.array([0, 2.5, 5, 10, 20, 30, 40, 50])
    signal = np.round(120 + 48.5 * conc + rng.normal(0, 40, conc.size), 0)
    sd = np.round(25 + 0.06 * signal + rng.uniform(0, 30, conc.size), 0)
    df = pd.DataFrame({"concentration (uM)": conc, "fluorescence (a.u.)": signal,
                       "fluorescence err (a.u.)": sd})
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.errorbar(conc, signal, yerr=sd, fmt="o", ms=5, capsize=3, color="black", mfc="white")
    ax.set_xlabel("Concentration (µM)")
    ax.set_ylabel("Fluorescence (a.u.)")
    ax.set_title("Synthetic data: calibration, mean ± SD, n = 3", loc="left", fontsize=9)
    save(fig, "calibration_scatter", df)


def penguin_bars():
    """Grouped bars with error bars: real Palmer penguins body mass by species and sex."""
    df = pd.read_csv(HERE / "penguin_bars.csv")
    species = df.iloc[:, 0]
    pos = np.arange(len(species))
    w = 0.38
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.bar(pos - w / 2, df.iloc[:, 1], w, yerr=df.iloc[:, 2], capsize=3, color="#bbbbbb",
           edgecolor="black", label="Female")
    ax.bar(pos + w / 2, df.iloc[:, 3], w, yerr=df.iloc[:, 4], capsize=3, color="#555555",
           edgecolor="black", label="Male")
    ax.set_xticks(pos, species)
    ax.set_ylabel("Body mass (g)")
    ax.set_ylim(0, 6500)
    ax.set_title("Palmer penguins, mean ± SD", loc="left", fontsize=9)
    ax.legend(loc="upper left")
    save(fig, "penguin_bars")


def growth_log():
    """A log-scale axis: synthetic bacterial growth of two strains, CFU per mL."""
    rng = np.random.default_rng(7)
    t = np.arange(0, 25, 3)                # 0, 3, ..., 24 h

    def logistic(t, n0, nmax, r, lag):
        grow = nmax / (1 + (nmax / n0 - 1) * np.exp(-r * np.clip(t - lag, 0, None)))
        return grow * 10 ** rng.normal(0, 0.05, t.size)

    wt = logistic(t, 2e4, 3e9, 0.9, 2)
    mut = logistic(t, 2e4, 4e7, 0.55, 4)
    df = pd.DataFrame({"time (h)": t, "wild type (CFU/mL)": wt.round(-2).astype(float),
                       "mutant (CFU/mL)": mut.round(-2).astype(float)})
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.semilogy(t, df.iloc[:, 1], "o-", color="black", label="Wild type")
    ax.semilogy(t, df.iloc[:, 2], "^--", color="gray", label="Mutant")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Viable cells (CFU/mL)")
    ax.set_ylim(1e4, 1e10)
    ax.set_title("Synthetic data", loc="left", fontsize=9)
    ax.legend(loc="lower right")
    save(fig, "growth_log", df)


def bioreactor_dual():
    """A dual-axis figure: synthetic bioreactor run, temperature left, dissolved oxygen right."""
    rng = np.random.default_rng(11)
    t = np.arange(0, 25, 2)
    temp = np.round(30 + 7 * (1 - np.exp(-t / 5)) + rng.normal(0, 0.3, t.size), 1)
    do = np.round(np.clip(92 * np.exp(-t / 9) + 8 + rng.normal(0, 2, t.size), 0, 100), 1)
    df = pd.DataFrame({"time (h)": t, "temperature (C)": temp, "dissolved oxygen (%)": do})
    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.plot(t, temp, "o-", color="tab:red", label="Temperature")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Temperature (°C)", color="tab:red")
    ax.set_ylim(28, 40)
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot(t, do, "s--", color="tab:blue", label="Dissolved oxygen")
    ax2.set_ylabel("Dissolved oxygen (% saturation)", color="tab:blue")
    ax2.set_ylim(0, 110)
    ax.set_title("Synthetic data: bioreactor run", loc="left", fontsize=9)
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [l.get_label() for l in lines], loc="center right")
    save(fig, "bioreactor_dual", df)


def dense_overlap():
    """The hard one: two noisy series, 60 points each, markers overlapping."""
    rng = np.random.default_rng(23)
    x = np.arange(0, 60, 1.0)
    base = 0.2 + 0.6 * (1 - np.exp(-x / 18))
    control = np.round(base + rng.normal(0, 0.035, x.size), 3)
    treated = np.round(base * 0.93 + rng.normal(0, 0.035, x.size), 3)
    df = pd.DataFrame({"time (min)": x, "control (absorbance)": control,
                       "treated (absorbance)": treated})
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.plot(x, control, "o", ms=6, color="black", alpha=0.7, label="Control")
    ax.plot(x, treated, "o", ms=6, mfc="white", color="gray", label="Treated")
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Absorbance at 600 nm")
    ax.set_title("Synthetic data", loc="left", fontsize=9)
    ax.legend(loc="lower right")
    save(fig, "dense_overlap", df)


if __name__ == "__main__":
    co2_line()
    calibration_scatter()
    penguin_bars()
    growth_log()
    bioreactor_dual()
    dense_overlap()
