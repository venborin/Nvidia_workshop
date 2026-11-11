# The six charts and the data behind them

Each PNG has a CSV of the same name holding exactly the numbers that were plotted, so an extraction can be measured against the truth. All six are drawn by `make_charts.py` in this folder (`python 04_see/charts/make_charts.py` rebuilds them; the synthetic ones use fixed seeds and come out the same every time). 150 dpi, journal styling.

Column names follow the convention the extraction prompt asks for: the first column is the x axis, then one column per series with units in parentheses, and an error-bar column named `<series> err (<units>)` right after its series, holding the half length of the bar.

| Chart | What it is | Data | Source and license |
|---|---|---|---|
| `co2_line` | Line chart, two series | Annual mean atmospheric CO2, 2000 to 2025, at Mauna Loa and as a global marine surface mean | Real. NOAA Global Monitoring Laboratory, `co2_annmean_mlo.csv` and `co2_annmean_gl.csv` from gml.noaa.gov/ccgg/trends (file created October 9, 2026; downloaded November 6, 2026). Made "freely available to the public" by the file's own data-use statement (US government data); GML asks to be credited, with citation text at gml.noaa.gov/ccgg/trends. Scripps supplied the Mauna Loa record before 1974, which this chart does not use. |
| `calibration_scatter` | Scatter with error bars | A calibration curve: fluorescence against concentration, mean and SD of three replicates | Synthetic, labeled on the chart. |
| `penguin_bars` | Grouped bar chart with error bars | Body mass by species and sex, mean and standard deviation, rounded to the gram (333 penguins with sex recorded) | Real. Palmer penguins (Horst, Hill and Gorman, 2020, the `palmerpenguins` R package, from Gorman, Williams and Fraser, 2014, Palmer Station LTER). CC0. |
| `growth_log` | Logarithmic y axis | Viable cell counts of two bacterial strains over 24 hours | Synthetic, labeled on the chart. |
| `bioreactor_dual` | Dual y axis | Temperature (left axis) and dissolved oxygen (right axis) through a 24-hour bioreactor run | Synthetic, labeled on the chart. |
| `dense_overlap` | The hard one | Two noisy series, 60 points each, whose markers overlap | Synthetic, labeled on the chart. |

## How the model did

Measured on November 6, 2026 with `python 04_see/smoke_test.py --runs 3` and then twice more (Nemotron 3.5 Super VL on OpenRouter; every call was served by DeepInfra under default routing). Each chart took 4 to 39 seconds and cost $0.0014 to $0.009. "Range" is the span of the true values on that axis.

- `penguin_bars`: the easiest. Every bar and error bar read, means within about 1 percent of the range (0.6 to 1.1 percent in the saved and replayed runs, 30 to 60 g), error bars within 1 percent.
- `calibration_scatter`: every point and error bar read in the final runs, within about 1 percent of the range. In one earlier run it snapped the points at 2.5 and 5 µM to 2 and 4 and added a ninth point that is not there; the overlay shows it at once.
- `co2_line`: all 52 points, within 2 percent of the range (about 1 ppm). Before the prompt said "no commas in column names", two of three runs copied the legend label "Mauna Loa, Hawaii" with its comma, which split the header and lost a whole series. A good story for the room: one character in a legend broke the table.
- `growth_log`: every point, and the right decade every time; the median error is about 9 percent of the true value. On a log axis read the relative error, not the percent of range, which the largest values swamp.
- `bioreactor_dual`: each series put on its own axis every run, within about 3 percent of the range. It once read the first oxygen point as 105 percent on an axis that stops at 100.
- `dense_overlap`: kept on purpose, although the model does not read it. It returns a value for nearly every x (70 to 120 of 120 points in eight runs, usually 118 or more), so the table looks complete, but the mean error, about 0.04 absorbance or 6 to 10 percent of the range, is worse than a smooth curve drawn through the cloud (0.03). The overlay shows it following the points for the first 20 minutes or so and then drawing a plausible ramp of its own. It teaches the stop's point: a complete, confident table is not a faithful one, and only the overlay against the truth shows the difference.

Reasoning settings, from a probe of 40 calls on three of these charts: the model thinks for 2,000 to 11,000 tokens before answering. Turning thinking off (`enabled: false` or `effort: "none"`) gave fast answers on the bar chart but, on the dense chart, refusals or the thinking written into the answer. `effort: "low"` and a thinking budget (`reasoning.max_tokens: 1024`) did not shorten the thinking, and with an overall limit of 6,000 one call spent all of it thinking and returned nothing. So `see.py` leaves thinking on, hides it (`exclude: true`), and allows 24,000 tokens. Providers differed in speed: DeepInfra 4 to 39 s, Together and BaseTen 17 to 28 s, CoreWeave 22 to 71 s, Darkbloom 81 to 94 s, which is near the 90-second deadline.

## How the two real-data CSVs were made

Run once on November 6, 2026, from the downloaded public files, then `make_charts.py` drew the charts from the resulting CSVs.

```python
import pandas as pd
# NOAA GML: https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv and co2_annmean_gl.csv
mlo = pd.read_csv("co2_annmean_mlo.csv", comment="#")
gl = pd.read_csv("co2_annmean_gl.csv", comment="#")
df = mlo.merge(gl, on="year", suffixes=("_mlo", "_gl"))
df = df[(df.year >= 2000) & (df.year <= 2025)]
pd.DataFrame({"year": df.year, "Mauna Loa (ppm)": df.mean_mlo, "global (ppm)": df.mean_gl}).to_csv("co2_line.csv", index=False)

# Palmer penguins: https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/penguins.csv
p = pd.read_csv("penguins.csv").dropna(subset=["sex", "body_mass_g"])
s = p.groupby(["species", "sex"]).body_mass_g.agg(["mean", "std"]).round(0)
rows = [{"species": sp, "female (g)": s.loc[(sp, "female"), "mean"], "female err (g)": s.loc[(sp, "female"), "std"],
         "male (g)": s.loc[(sp, "male"), "mean"], "male err (g)": s.loc[(sp, "male"), "std"]}
        for sp in ["Adelie", "Chinstrap", "Gentoo"]]
pd.DataFrame(rows).to_csv("penguin_bars.csv", index=False)
```
