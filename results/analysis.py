#!/usr/bin/env python3
"""
Analysis script for AHU trend data.
Reads raw CSV, applies fixes from findings.md, computes daily tracking metrics,
generates plot, and writes report.md with all computed values.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_CSV = Path('02_data/datasets/hvac-ahu/ahu_trend_2017-09-25_to_2017-10-08.csv')
REPORT_MD = Path('results/report.md')
FIG_DIR = Path('results/figures')
FIG_PNG = FIG_DIR / 'tracking.png'

# ----------------------------------------------------------------------
# Load raw data
# ----------------------------------------------------------------------
print(f"Reading {RAW_CSV}...")
df = pd.read_csv(RAW_CSV)
df['Datetime'] = pd.to_datetime(df['Datetime'])
rows_raw = len(df)
print(f"  Raw rows: {rows_raw}")

# ----------------------------------------------------------------------
# Fix 1: Drop duplicate timestamps (Problem 1)
# ----------------------------------------------------------------------
dupes = df[df.duplicated(subset='Datetime', keep=False)]
dupe_timestamps = dupes['Datetime'].nunique()
dupe_rows = len(dupes)
df = df.drop_duplicates(subset='Datetime', keep='first').reset_index(drop=True)
rows_after_fix1 = len(df)
print(f"  Fix 1 (drop duplicates): {dupe_timestamps} timestamps, {dupe_rows} rows -> {rows_raw - rows_after_fix1} rows removed")
print(f"  Rows after fix 1: {rows_after_fix1}")

# ----------------------------------------------------------------------
# Flag rows per findings.md (leave in place, add flag columns)
# ----------------------------------------------------------------------
# Problem 2: SA_CFM != 0 when fan off
df['flag_sa_cfm_fan_off'] = (df['SF_SPD_DM'] == 0) & (df['SA_CFM'] != 0)
n_flag2 = df['flag_sa_cfm_fan_off'].sum()
print(f"  Flag 2 (SA_CFM!=0 fan off): {n_flag2} rows")

# Problem 3: OA_CFM constant (flag entire column - mark all rows)
df['flag_oa_cfm_constant'] = True
n_flag3 = len(df)
print(f"  Flag 3 (OA_CFM constant): {n_flag3} rows (entire column)")

# Problem 4: CHWC_VLV_DM > 0 when fan off
df['flag_valve_fan_off'] = (df['SF_SPD_DM'] == 0) & (df['CHWC_VLV_DM'] > 0)
n_flag4 = df['flag_valve_fan_off'].sum()
print(f"  Flag 4 (valve open fan off): {n_flag4} rows")

# Problem 5: MA_TEMP outside [OA_TEMP, RA_TEMP]
df['ma_between'] = ((df['MA_TEMP'] >= df[['OA_TEMP','RA_TEMP']].min(axis=1)) &
                     (df['MA_TEMP'] <= df[['OA_TEMP','RA_TEMP']].max(axis=1)))
df['flag_ma_oob'] = ~df['ma_between']
# Separate Type A (slightly below OA) and Type B (above RA)
df['flag_ma_type_a'] = df['flag_ma_oob'] & (df['MA_TEMP'] < df['OA_TEMP'])
df['flag_ma_type_b'] = df['flag_ma_oob'] & (df['MA_TEMP'] > df['RA_TEMP'])
n_flag5 = df['flag_ma_oob'].sum()
n_flag5a = df['flag_ma_type_a'].sum()
n_flag5b = df['flag_ma_type_b'].sum()
print(f"  Flag 5 (MA_TEMP out of bounds): {n_flag5} rows (Type A: {n_flag5a}, Type B: {n_flag5b})")

# Problem 6: SA_TEMP > MA_TEMP + 1.5
df['flag_sa_gt_ma'] = df['SA_TEMP'] > df['MA_TEMP'] + 1.5
n_flag6 = df['flag_sa_gt_ma'].sum()
print(f"  Flag 6 (SA_TEMP > MA_TEMP+1.5): {n_flag6} rows")

# Problem 7: OA_DMPR stuck at 0.25 (2017-10-03 and 2017-10-04)
df['flag_damper_stuck'] = df['OA_DMPR'] == 0.25
n_flag7 = df['flag_damper_stuck'].sum()
print(f"  Flag 7 (OA_DMPR stuck at 0.25): {n_flag7} rows")

# Problem 8: SF_CS=1.0 when fan off
df['flag_sf_cs_fan_off'] = (df['SF_SPD_DM'] == 0) & (df['SF_CS'] == 1.0)
n_flag8 = df['flag_sf_cs_fan_off'].sum()
print(f"  Flag 8 (SF_CS=1.0 fan off): {n_flag8} rows")

# Problem 9: SF_WAT>0 when fan off
df['flag_sf_wat_fan_off'] = (df['SF_SPD_DM'] == 0) & (df['SF_WAT'] > 0)
n_flag9 = df['flag_sf_wat_fan_off'].sum()
print(f"  Flag 9 (SF_WAT>0 fan off): {n_flag9} rows")

# ----------------------------------------------------------------------
# Compute daily medians for fan-on rows (excluding flagged problematic rows)
# ----------------------------------------------------------------------
# For supply air tracking, we want clean fan-on data.
# Exclude rows flagged in Problems 2, 4, 6, 7 (these affect SA_TEMP reliability)
# Note: Problem 3 is OA_CFM only, Problem 5 Type A is minor, Problems 8-9 overlap with 2
fan_on = df[df['SF_SPD_DM'] == 1].copy()

# Create a clean mask for tracking analysis
# Exclude: fan-off-flagged rows (shouldn't be in fan_on anyway), valve-fan-off,
# SA>MA violations, damper-stuck days
clean_mask = (
    (~fan_on.index.isin(df.index[df['flag_valve_fan_off']])) &
    (~fan_on.index.isin(df.index[df['flag_sa_gt_ma']])) &
    (~fan_on.index.isin(df.index[df['flag_damper_stuck']]))
)
fan_on_clean = fan_on[clean_mask].copy()

print(f"  Fan-on rows total: {len(fan_on)}")
print(f"  Fan-on clean rows: {len(fan_on_clean)}")

# Compute daily stats on CLEAN fan-on data
fan_on_clean['SA_diff'] = fan_on_clean['SA_TEMP'] - fan_on_clean['SA_TEMPSPT']
fan_on_clean['date'] = fan_on_clean['Datetime'].dt.date

daily = fan_on_clean.groupby('date').agg(
    median_SA_diff=('SA_diff', 'median'),
    median_OA_TEMP=('OA_TEMP', 'median'),
    count=('SA_diff', 'count')
).reset_index()

# Also compute on ALL fan-on data for comparison
fan_on['SA_diff'] = fan_on['SA_TEMP'] - fan_on['SA_TEMPSPT']
fan_on['date'] = fan_on['Datetime'].dt.date
daily_all = fan_on.groupby('date').agg(
    median_SA_diff=('SA_diff', 'median'),
    median_OA_TEMP=('OA_TEMP', 'median'),
    count=('SA_diff', 'count')
).reset_index()

print("\nDaily medians (clean fan-on):")
print(daily.to_string(index=False))

# ----------------------------------------------------------------------
# Identify equipment problem days vs weather-driven drift
# ----------------------------------------------------------------------
# Economizer range: OA_TEMP between 33.8F and 60F -> mechanical cooling locked out
# If OA_TEMP in that range and SA_diff is large, it's weather-driven
# If OA_TEMP outside that range and SA_diff is large, it's equipment problem

daily['economizer_active'] = (daily['median_OA_TEMP'] > 33.8) & (daily['median_OA_TEMP'] < 60.0)
daily['large_drift'] = daily['median_SA_diff'].abs() > 2.0  # >2F drift
daily['equipment_problem'] = daily['large_drift'] & ~daily['economizer_active']
daily['weather_driven'] = daily['large_drift'] & daily['economizer_active']

equip_days = daily[daily['equipment_problem']]['date'].tolist()
weather_days = daily[daily['weather_driven']]['date'].tolist()
normal_days = daily[~daily['large_drift']]['date'].tolist()

print(f"\nEquipment problem days (drift >2F, outside economizer range): {equip_days}")
print(f"Weather-driven drift days (drift >2F, OA 33.8-60F): {weather_days}")
print(f"Normal tracking days (drift <=2F): {normal_days}")

# ----------------------------------------------------------------------
# Create plot
# ----------------------------------------------------------------------
FIG_DIR.mkdir(parents=True, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(12, 6))

dates = daily['date']
sa_diff = daily['median_SA_diff']
oa_temp = daily['median_OA_TEMP']

# Bar plot for SA_TEMP - SA_TEMPSPT
colors = ['red' if d in equip_days else 'orange' if d in weather_days else 'green' for d in dates]
bars = ax1.bar(dates, sa_diff, color=colors, alpha=0.7, width=0.8, label='Median SA_TEMP - SA_TEMPSPT (°F)')
ax1.axhline(y=0, color='black', linewidth=0.8)
ax1.axhline(y=2, color='gray', linestyle='--', linewidth=0.8, label='±2°F threshold')
ax1.axhline(y=-2, color='gray', linestyle='--', linewidth=0.8)
ax1.set_xlabel('Date')
ax1.set_ylabel('Median SA_TEMP - SA_TEMPSPT (°F)', color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax1.set_ylim(-5, max(25, sa_diff.max() + 2))

# Twin axis for outdoor temperature
ax2 = ax1.twinx()
ax2.plot(dates, oa_temp, 'b-o', markersize=4, label='Median OA_TEMP (°F)')
ax2.axhline(y=33.8, color='blue', linestyle=':', linewidth=1, label='Economizer limits (33.8/60°F)')
ax2.axhline(y=60.0, color='blue', linestyle=':', linewidth=1)
ax2.set_ylabel('Median Outdoor Air Temp (°F)', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')

# Annotate bars with values
for bar, val, oa in zip(bars, sa_diff, oa_temp):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{val:.1f}', ha='center', va='bottom', fontsize=9)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('Daily Supply Air Temperature Tracking vs Outdoor Temperature\n'
          '(Green=Normal, Orange=Weather-driven drift, Red=Equipment problem)')
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(FIG_PNG, dpi=150)
plt.close()
print(f"\nPlot saved to {FIG_PNG}")

# ----------------------------------------------------------------------
# Write report.md with ALL computed values
# ----------------------------------------------------------------------
with open(REPORT_MD, 'w') as f:
    f.write("# AHU Supply Air Temperature Tracking Analysis\n\n")
    f.write(f"**Source file:** {RAW_CSV}\n")
    f.write(f"**Analysis date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")

    f.write("## 1. Data Fixes Applied\n\n")
    f.write(f"### Fix 1: Duplicate Timestamps\n")
    f.write(f"- **Raw rows:** {rows_raw}\n")
    f.write(f"- **Duplicate timestamps found:** {dupe_timestamps} (on 2017-10-02 14:00–14:55)\n")
    f.write(f"- **Duplicate rows removed:** {rows_raw - rows_after_fix1}\n")
    f.write(f"- **Rows after fix:** {rows_after_fix1}\n\n")

    f.write("## 2. Rows Flagged (Left in Place)\n\n")
    f.write(f"| Problem | Description | Rows Flagged |\n")
    f.write(f"|---------|-------------|--------------|\n")
    f.write(f"| 2 | SA_CFM ≠ 0 when fan off | {int(n_flag2)} |\n")
    f.write(f"| 3 | OA_CFM constant (all rows) | {int(n_flag3)} |\n")
    f.write(f"| 4 | Cooling valve open when fan off | {int(n_flag4)} |\n")
    f.write(f"| 5 | MA_TEMP outside [OA,RA] bounds | {int(n_flag5)} (Type A: {int(n_flag5a)}, Type B: {int(n_flag5b)}) |\n")
    f.write(f"| 6 | SA_TEMP > MA_TEMP + 1.5°F | {int(n_flag6)} |\n")
    f.write(f"| 7 | OA_DMPR stuck at 0.25 (2017-10-03, 2017-10-04) | {int(n_flag7)} |\n")
    f.write(f"| 8 | SF_CS=1.0 when fan off | {int(n_flag8)} |\n")
    f.write(f"| 9 | SF_WAT > 0 when fan off | {int(n_flag9)} |\n\n")

    f.write("## 3. Daily Supply Air Tracking (Clean Fan-On Data)\n\n")
    f.write("Only fan-on rows (`SF_SPD_DM=1`) excluding flagged problematic rows ")
    f.write("(valve-open-fan-off, SA>MA violations, stuck-damper days) were used.\n\n")
    f.write("| Date | Median SA_TEMP − SA_TEMPSPT (°F) | Median OA_TEMP (°F) | Clean Fan-On Count |\n")
    f.write("|------|----------------------------------|---------------------|-------------------|\n")
    for _, row in daily.iterrows():
        f.write(f"| {row['date']} | {row['median_SA_diff']:.2f} | {row['median_OA_TEMP']:.2f} | {int(row['count'])} |\n")
    f.write("\n")

    f.write("## 4. Day Classification\n\n")
    f.write(f"**Economizer active range:** 33.8°F < OA_TEMP < 60°F (mechanical cooling locked out)\n")
    f.write(f"**Large drift threshold:** |SA_TEMP − SA_TEMPSPT| > 2°F\n\n")

    f.write("### Equipment Problem Days (drift >2°F, outside economizer range)\n")
    if equip_days:
        for d in equip_days:
            row = daily[daily['date']==d].iloc[0]
            f.write(f"- **{d}**: median SA_diff = {row['median_SA_diff']:.2f}°F, median OA_TEMP = {row['median_OA_TEMP']:.2f}°F\n")
            f.write(f"  OA_TEMP {row['median_OA_TEMP']:.2f}°F is outside 33.8–60°F; mechanical cooling should be available.\n")
            f.write(f"  Supply air deviates from setpoint by {row['median_SA_diff']:.2f}°F → suggests equipment issue.\n")
    else:
        f.write("None.\n")
    f.write("\n")

    f.write("### Weather-Driven Drift Days (drift >2°F, OA_TEMP in economizer range)\n")
    if weather_days:
        for d in weather_days:
            row = daily[daily['date']==d].iloc[0]
            f.write(f"- **{d}**: median SA_diff = {row['median_SA_diff']:.2f}°F, median OA_TEMP = {row['median_OA_TEMP']:.2f}°F\n")
            f.write(f"  OA_TEMP {row['median_OA_TEMP']:.2f}°F is in economizer range (33.8–60°F); mechanical cooling locked out.\n")
            f.write(f"  Drift of {row['median_SA_diff']:.2f}°F is expected weather-driven behavior.\n")
    else:
        f.write("None.\n")
    f.write("\n")

    f.write("### Normal Tracking Days (drift ≤2°F)\n")
    for d in normal_days:
        row = daily[daily['date']==d].iloc[0]
        f.write(f"- **{d}**: median SA_diff = {row['median_SA_diff']:.2f}°F, median OA_TEMP = {row['median_OA_TEMP']:.2f}°F\n")
    f.write("\n")

    f.write("## 5. Conclusions\n\n")
    if equip_days:
        f.write(f"**Equipment problems detected on {len(equip_days)} day(s):** {', '.join(str(d) for d in equip_days)}.\n")
        f.write("On these days, the supply air temperature deviated from its 55.2°F setpoint by more than 2°F ")
        f.write("while outdoor temperature was outside the economizer range (mechanical cooling should have been available). ")
        f.write("This points to a cooling coil valve, sensor, or control sequence issue rather than weather.\n\n")
    if weather_days:
        f.write(f"**Weather-driven drift on {len(weather_days)} day(s):** {', '.join(str(d) for d in weather_days)}.\n")
        f.write("On these days, outdoor air temperature was in the economizer range (33.8–60°F), ")
        f.write("where the control sequence locks out mechanical cooling and uses outdoor air for cooling. ")
        f.write("Supply air temperature drift is expected and not an equipment fault.\n\n")
    f.write(f"**Normal tracking on {len(normal_days)} day(s):** {', '.join(str(d) for d in normal_days)}.\n")
    f.write("Supply air temperature stayed within 2°F of setpoint.\n\n")

    f.write("## 6. Plot\n\n")
    f.write(f"![Tracking plot](figures/tracking.png)\n\n")
    f.write("*Green bars = normal tracking (≤2°F drift), Orange = weather-driven drift (>2°F drift, OA 33.8–60°F), ")
    f.write("Red = equipment problem (>2°F drift, OA outside economizer range). Blue line = median outdoor temperature. ")
    f.write("Dashed blue lines = economizer limits (33.8°F and 60°F).*\n")

print(f"\nReport written to {REPORT_MD}")

# ----------------------------------------------------------------------
# Print all computed numbers for traceability
# ----------------------------------------------------------------------
print("\n=== ALL COMPUTED VALUES FOR TRACEABILITY ===")
print(f"rows_raw = {rows_raw}")
print(f"dupe_timestamps = {dupe_timestamps}")
print(f"dupe_rows = {dupe_rows}")
print(f"rows_after_fix1 = {rows_after_fix1}")
print(f"n_flag2 = {int(n_flag2)}")
print(f"n_flag3 = {int(n_flag3)}")
print(f"n_flag4 = {int(n_flag4)}")
print(f"n_flag5 = {int(n_flag5)}")
print(f"n_flag5a = {int(n_flag5a)}")
print(f"n_flag5b = {int(n_flag5b)}")
print(f"n_flag6 = {int(n_flag6)}")
print(f"n_flag7 = {int(n_flag7)}")
print(f"n_flag8 = {int(n_flag8)}")
print(f"n_flag9 = {int(n_flag9)}")
print(f"fan_on_total = {len(fan_on)}")
print(f"fan_on_clean = {len(fan_on_clean)}")
for _, row in daily.iterrows():
    print(f"daily[{row['date']}] median_SA_diff={row['median_SA_diff']:.2f} median_OA_TEMP={row['median_OA_TEMP']:.2f} count={int(row['count'])}")
print(f"equip_days = {equip_days}")
print(f"weather_days = {weather_days}")
print(f"normal_days = {normal_days}")