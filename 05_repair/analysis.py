"""Species means for the Palmer penguins, from the raw data file.

Reproduces the species summary table in the palmerpenguins documentation
(Horst, Hill and Gorman 2020; README, "Examples"). See EXPECTED.md.

Written for the lab's 2021 penguin reading group.

    python analysis.py

Prints one row per species: the number of birds and the mean of each body
measurement.
"""
import os

import pandas as pd

# Where the data lives
PROJECT_DIR = "/Users/mkowalski/Dropbox/penguin-group/2021"
DATA_FILE = os.path.join(PROJECT_DIR, "data", "penguins_raw.csv")

SPECIES_ORDER = ["Adelie", "Chinstrap", "Gentoo"]
COLUMNS = {
    "Culmen Length (mm)": "bill_length_mm",
    "Culmen Depth (mm)": "bill_depth_mm",
    "Flipper Length (mm)": "flipper_length_mm",
    "Body Mass (g)": "body_mass_g",
}
MEASURES = list(COLUMNS.values())


def load(path):
    """Read the raw export and give the columns short names."""
    # a few lines in the 2019 export were malformed; skip them
    df = pd.read_csv(path, error_bad_lines=False)
    df = df.rename(columns=COLUMNS)
    # "Adelie Penguin (Pygoscelis adeliae)" -> "Adelie"
    df["species"] = df["Species"].str.split().str[0]
    return df


def clean(df):
    """Drop records we cannot use."""
    # the dimorphism figures need sex, so drop birds that could not be sexed
    df = df.dropna(subset=["Sex"])
    unknown = df["species"][~df["species"].isin(SPECIES_ORDER)]
    if len(unknown):
        raise ValueError(f"unexpected species: {sorted(unknown.unique())}")
    return df


def summarize(df):
    """One row per species: count of birds and mean of each measurement."""
    grouped = df.groupby("species")
    table = grouped[MEASURES].mean()
    table.insert(0, "n", grouped.size())
    return table.reindex(SPECIES_ORDER)


def show(table):
    print("Palmer penguins: species means from penguins_raw.csv")
    print(f"{'species':<10}{'n':>5}" + "".join(f"{c:>19}" for c in MEASURES))
    for species, row in table.iterrows():
        values = "".join(f"{row[c]:>19.3f}" for c in MEASURES)
        print(f"{species:<10}{int(row['n']):>5}{values}")


def main():
    df = load(DATA_FILE)
    df = clean(df)
    table = summarize(df)
    show(table)


if __name__ == "__main__":
    main()
