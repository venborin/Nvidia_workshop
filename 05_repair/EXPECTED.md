# What analysis.py should reproduce

analysis.py computes, for each penguin species, the number of birds and the mean bill length, bill depth, flipper length and body mass from the raw Palmer penguins file. Those numbers are published, so the script can be checked against them.

## The published numbers

From the palmerpenguins package documentation (README, section "Examples", also the package home page https://allisonhorst.github.io/palmerpenguins/), produced there by

    penguins %>% count(species)
    penguins %>% group_by(species) %>% summarize(across(where(is.numeric), mean, na.rm = TRUE))

| Species | Birds | Bill length (mm) | Bill depth (mm) | Flipper length (mm) | Body mass (g) |
|---|---|---|---|---|---|
| Adelie | 152 | 38.8 | 18.3 | 190 | 3701 |
| Chinstrap | 68 | 48.8 | 18.4 | 196 | 3733 |
| Gentoo | 124 | 47.5 | 15.0 | 217 | 5076 |

The R table prints flipper length and body mass with a trailing point ("190.", "3701."), meaning whole units. Bill length and depth in the R data are the culmen length and depth columns of the raw file.

## Tolerance

Half a unit in the last published digit: 0.05 mm for bill length and depth, 0.5 mm for flipper length, 0.5 g for body mass. Bird counts must match exactly.

## The data

02_data/datasets/penguins/penguins_raw.csv (see SOURCE.md and DICTIONARY.md in that folder). It is the same raw file the package's tables are built from.

## The check

From the labs/ folder:

    python 05_repair/check_expected.py

It runs analysis.py from labs/, reads the table it prints, and prints PASS or FAIL with every value that is off. It needs a header line that starts with "species" followed by the column names n, bill_length_mm, bill_depth_mm, flipper_length_mm and body_mass_g, then one line per species, as analysis.py prints now. Keep that output format when you change the script.

## Citation

Horst AM, Hill AP, Gorman KB (2020). palmerpenguins: Palmer Archipelago (Antarctica) penguin data. R package version 0.1.0. https://allisonhorst.github.io/palmerpenguins/. doi:10.5281/zenodo.3960218. README at https://github.com/allisonhorst/palmerpenguins/blob/32d1fcb576d79956985d38e10811cf38321286df/README.md (the last commit to change it, 2022-08-13), read 2026-11-06. The data are CC0.
