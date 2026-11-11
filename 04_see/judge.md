Goal: decide, from evidence, what one chart extraction is good enough for.

Chart: 04_see/charts/dense_overlap.png (one of the shipped charts in 04_see/charts/, which each have the true data beside them).

1. Run python 04_see/see.py 04_see/charts/dense_overlap.png --extract, then python 04_see/compare.py 04_see/charts/dense_overlap.png results/seen/dense_overlap.csv. Read the whole printed error table, including its first row, the x axis: extra points, repeated points and how far the x values are off.

2. Decide whether one retry is worth it: for example a series with points missing, columns not matched by name, extra or repeated points, or a series error above 5 percent of the span. If it is, run the --extract command once more (add a short note after --extract if it would help, such as "one row per minute from 0 to 59"), then compare again. At most one retry, and say why you did or did not retry. Do not edit see.py, compare.py, the chart's true data or any extracted CSV.

3. Write results/verdict.md: which run you kept and why; the error numbers you relied on, copied from compare.py's printed table; and for which uses this extraction is good enough (a first look at a published figure, a check of your own reading, a quantitative fit or a reanalysis) and for which it is not, each with the numbers that decide it. Every number in verdict.md must appear in compare.py's printed output.
