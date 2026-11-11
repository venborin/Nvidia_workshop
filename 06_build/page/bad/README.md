# The page recipe's bad input

A report that the page recipe must refuse to turn into a page:

- `report.md` names `figures/2_missing.png`, which is not in `figures/`;
- it has a number typed by hand, 4242.7, that the analysis never printed (`analysis-output.txt`).

    python 06_build/page/make_page.py --from 06_build/page/bad --out results/page-bad

It should print NOT WRITTEN and name both problems. Nothing in `results/page/` is touched.
