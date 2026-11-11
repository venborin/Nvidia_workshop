"""Your own check of the air-handler file, written by a person, not by the agent.

    python 02_data/check.py

It prints the row count (and the count you would expect), how many rows are
exact repeats, and the outdoor air temperature for each day. Compare what it
shows with what you know about the file, and with results/findings.md.
"""
from pathlib import Path

import pandas as pd

CSV = Path(__file__).parent / "datasets/hvac-ahu/ahu_trend_2017-09-25_to_2017-10-08.csv"

d = pd.read_csv(CSV)
print("Rows:", len(d), "   Exact repeated rows:", d.duplicated().sum())
print("Expected for 14 days of 5-minute readings: 14 x 288 =", 14 * 288)
print()
print("Outdoor air temperature (OA_TEMP), median of each day. The dictionary says degrees F.")
print(d.groupby(d.Datetime.str[:10]).OA_TEMP.median().round(1).to_string())
