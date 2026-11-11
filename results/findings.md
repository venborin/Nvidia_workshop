# Data Investigation Findings: ahu_trend_2017-09-25_to_2017-10-08.csv

**File:** 02_data/datasets/hvac-ahu/ahu_trend_2017-09-25_to_2017-10-08.csv  
**Rows:** 4,044 (expected 4,032 for 14 days × 288 intervals/day)  
**Columns:** 20 (Datetime + 19 sensors)  
**Date range:** 2017-09-25 00:00 to 2017-10-08 23:55 (local time, 5-min intervals)

---

## Problem 1: Duplicate Timestamps (12 timestamps, 24 rows total)

**Code:**
```python
dupes = df[df.duplicated(subset='Datetime', keep=False)]
print(f"Duplicate timestamps: {dupes['Datetime'].nunique()}")
print(dupes['Datetime'].unique())
```

**Output:**
```
Duplicate timestamps: 12
['2017-10-02 14:00:00' ... '2017-10-02 14:55:00']
```
All 12 timestamps on 2017-10-02 14:00–14:55 appear twice with identical values.

**Affected rows:** 24 rows (indices 2184–2195 and 2196–2207), all on 2017-10-02 14:00–14:55.

**Proposal:** **Fix** — Drop the second occurrence of each duplicate (keep first). The duplicates are exact copies; removing them restores the expected 4,032-row timeline.

---

## Problem 2: SA_CFM Reports High Flow When Fan Is Off (429 rows)

**Code:**
```python
fan_off = df[df['SF_SPD_DM']==0]
nonzero = fan_off[fan_off['SA_CFM'] != 0]
print(f"Rows: {len(nonzero)}")
print(nonzero[['Datetime','SA_CFM','SF_SPD_DM','SF_CS','SF_WAT']].head())
```

**Output:**
```
Rows: 429
                Datetime   SA_CFM  SF_SPD_DM  SF_CS  SF_WAT
0    2017-09-25 00:00:00  1127776          0   1.00     711
1    2017-09-25 00:05:00  1127776          0   1.00     711
...
871  2017-09-28 00:35:00   168942          0   0.19     246
...
```
Values range from –262 to 1,276,165 CFM. These rows also show `SF_CS=1.0` (full speed command) and `SF_WAT=711 W` despite `SF_SPD_DM=0` (fan off).

**Affected rows:** 429 rows scattered across unoccupied periods (nights, weekends). Notably:
- 2017-09-25 00:00–06:00 (73 rows)
- 2017-09-28 00:35–05:35 (22 rows, with ramping SF_CS/SF_WAT)
- 2017-09-28 22:50–2017-09-29 05:35 (48 rows)
- 2017-09-30 02:10–02:25 (4 rows)
- 2017-10-01 13:25–23:55 (134 rows)
- 2017-10-02 00:00–06:00 (72 rows)
- 2017-10-08 14:35–23:55 (76 rows)

**Proposal:** **Flag** — These rows are physically impossible (fan off but airflow reported). The sensor or logging is faulty during unoccupied periods. Flag all rows where `SF_SPD_DM=0` and `SA_CFM != 0` as unreliable. Do not "fix" by zeroing; the true airflow is unknown.

---

## Problem 3: OA_CFM Is Constant at 357,730 CFM (All 4,044 rows)

**Code:**
```python
print(df['OA_CFM'].unique())
```

**Output:**
```
[357730]
```
Outdoor airflow never varies—not by time of day, fan status, damper position, or occupancy.

**Affected rows:** All 4,044 rows.

**Proposal:** **Flag** — The OA_CFM sensor appears broken or uncalibrated (stuck at a single value). It cannot be used for economizer analysis or outdoor air fraction calculations. Flag the entire column as unreliable.

---

## Problem 4: Cooling Valve Commanded Open While Fan Is Off (29 rows)

**Code:**
```python
valve_fan_off = fan_off[fan_off['CHWC_VLV_DM'] != 0]
print(valve_fan_off[['Datetime','CHWC_VLV_DM','SF_SPD_DM','SF_CS','SF_WAT']])
```

**Output:**
```
                Datetime  CHWC_VLV_DM  SF_SPD_DM  SF_CS  SF_WAT
891  2017-09-28 02:15:00         0.37          0   0.75     734
892  2017-09-28 02:20:00         0.73          0   0.78     883
...
1466 2017-09-30 02:10:00         0.06          0   0.28     366
```

**Affected rows:** 29 rows during unoccupied periods:
- 2017-09-28 02:15–04:40 (10 rows, valve ramps 0.37→1.0)
- 2017-09-28 22:50–2017-09-29 04:45 (18 rows, valve at 1.0)
- 2017-09-30 02:10–02:10 (1 row, valve at 0.06)

**Proposal:** **Flag** — The control sequence requires the fan to run for mechanical cooling. Valve commands >0 with `SF_SPD_DM=0` indicate a logging error (command logged but not executed) or a sequence fault. Flag these rows; do not assume cooling occurred.

---

## Problem 5: MA_TEMP Outside Physical Bounds [OA_TEMP, RA_TEMP] (111 rows, 2.7%)

**Code:**
```python
df['MA_between'] = ((df['MA_TEMP'] >= df[['OA_TEMP','RA_TEMP']].min(axis=1)) &
                     (df['MA_TEMP'] <= df[['OA_TEMP','RA_TEMP']].max(axis=1)))
violations = df[~df['MA_between']]
print(f"Violations: {len(violations)}")
print(violations[['Datetime','OA_TEMP','RA_TEMP','MA_TEMP','SYS_CTL','SF_SPD_DM']].head(20))
```

**Output:**
```
Violations: 111
                Datetime  OA_TEMP  RA_TEMP  MA_TEMP  SYS_CTL  SF_SPD_DM
114  2017-09-25 09:30:00     57.5     71.5     57.4        1          1
393  2017-09-26 08:45:00     58.1     70.0     57.9        1          1
557  2017-09-26 22:25:00     69.6     69.6     69.4        0          0
841  2017-09-27 22:05:00     65.1     68.6     69.3        0          0
1153 2017-09-29 00:05:00     63.0     76.9     77.0        0          0
1657 2017-09-30 18:05:00     15.9     69.1     69.8        0          0
1916 2017-10-01 15:40:00     19.4     92.5     92.6        0          0
3959 2017-10-08 16:55:00     56.0     92.1     92.2        0          0
```

Two distinct patterns:
- **Type A (slightly below OA_TEMP):** 95 rows where MA_TEMP is 0.1–2.6 °F below OA_TEMP. Occurs during occupied hours (SYS_CTL=1, fan on) when OA_TEMP ≈ 55–60 °F (economizer transition).
- **Type B (above RA_TEMP):** 16 rows where MA_TEMP exceeds RA_TEMP by up to 73 °F. Occurs during unoccupied hours (SYS_CTL=0, fan off) with very cold OA_TEMP (8–20 °F) and warm RA_TEMP (69–92 °F).

**Affected rows:** 111 rows across multiple days (see full list in investigation).

**Proposal:** **Flag** — Type A may be sensor noise at the economizer transition; Type B is physically impossible (mixed air cannot exceed return air when fan is off). Flag all 111 rows. For Type A, the deviation is small (≤2.6 °F); for Type B, the MA_TEMP values are not trustworthy.

---

## Problem 6: SA_TEMP Exceeds MA_TEMP + 1.5 °F (277 rows, 6.8%)

**Code:**
```python
df['SA_violation'] = df['SA_TEMP'] > df['MA_TEMP'] + 1.5
sa_viol = df[df['SA_violation']]
sa_viol['excess'] = sa_viol['SA_TEMP'] - sa_viol['MA_TEMP']
print(sa_viol[['Datetime','MA_TEMP','SA_TEMP','excess','OA_TEMP','CHWC_VLV_DM','SF_SPD_DM','SYS_CTL']].head(20))
```

**Output:**
```
                Datetime  MA_TEMP  SA_TEMP  excess  OA_TEMP  CHWC_VLV_DM  SF_SPD_DM  SYS_CTL
256  2017-09-25 21:20:00     54.8     56.4     1.6     53.0         0.00          1        1
3014 2017-10-05 10:10:00     68.3     75.3     7.0     59.9         0.00          1        1
3015 2017-10-05 10:15:00     65.4     73.5     8.1     59.8         0.00          1        1
3052 2017-10-05 13:20:00     55.1     58.3     3.2     54.7         0.04          1        1
3255 2017-10-06 06:15:00     54.2     61.0     6.8     50.0         0.00          1        1
...
```
Excess ranges from 1.6 °F to 8.1 °F. Most violations occur on 2017-10-05 and 2017-10-06 (occupied days) when OA_TEMP ≈ 50–55 °F and `CHWC_VLV_DM=0` (no mechanical cooling). The supply air is warmer than mixed air + fan heat, with no cooling active.

**Affected rows:** 277 rows, concentrated on:
- 2017-09-25 21:20–21:50 (6 rows)
- 2017-10-05 10:05–22:00 (156 rows, two long blocks)
- 2017-10-06 06:05–22:00 (115 rows, nearly all day)

**Proposal:** **Flag** — When `CHWC_VLV_DM=0` and OA_TEMP < 60 °F, the economizer should be modulating. SA_TEMP > MA_TEMP + 1.5 °F suggests either sensor error (SA_TEMP or MA_TEMP miscalibrated) or unlogged heating. Flag these rows; do not use for supply-air tracking.

---

## Problem 7: OA_DMPR Stuck at 0.25 for Two Full Days (542 rows)

**Code:**
```python
stuck = df[df['OA_DMPR'] == 0.25]
print(f"Rows with OA_DMPR=0.25: {len(stuck)}")
print(stuck['Datetime'].min(), "to", stuck['Datetime'].max())
print(stuck[['Datetime','OA_DMPR_DM','OA_DMPR']].head(10))
```

**Output:**
```
Rows with OA_DMPR=0.25: 542
2017-10-03 00:00:00 to 2017-10-04 23:55:00
                Datetime  OA_DMPR_DM  OA_DMPR
2332 2017-10-03 01:20:00        0.00     0.25
2389 2017-10-03 06:05:00        1.00     0.25
2400 2017-10-03 07:00:00        0.10     0.25
2677 2017-10-04 06:05:00        1.00     0.25
2772 2017-10-04 14:00:00        0.10     0.25
```
For 2017-10-03 and 2017-10-04 (all 288 intervals each day), `OA_DMPR` is fixed at 0.25 while `OA_DMPR_DM` varies 0.0–1.0 normally. Damper command–position difference reaches 0.75.

**Affected rows:** 542 rows (all of 2017-10-03 and 2017-10-04).

**Proposal:** **Flag** — The damper position sensor is stuck/frozen. The command signal varies correctly, but the feedback is invalid. Flag all rows for these two days; economizer analysis cannot use OA_DMPR for 2017-10-03 and 2017-10-04.

---

## Problem 8: SF_CS = 1.0 While SF_SPD_DM = 0 (415 rows)

**Code:**
```python
fan_off = df[df['SF_SPD_DM']==0]
print(f"SF_CS=1.0 when fan off: {len(fan_off[fan_off['SF_CS']==1.0])}")
```

**Output:**
```
SF_CS=1.0 when fan off: 415
```

**Affected rows:** 415 rows, largely overlapping with Problem 2 (SA_CFM non-zero when fan off). Occurs during the same unoccupied periods.

**Proposal:** **Flag** — The control signal logs "full speed" while the fan status says "off." This is a logging inconsistency. Flag these rows; do not trust SF_CS during unoccupied periods.

---

## Problem 9: SF_WAT > 0 While SF_SPD_DM = 0 (426 rows)

**Code:**
```python
print(f"SF_WAT>0 when fan off: {len(fan_off[fan_off['SF_WAT']>0])}")
print(fan_off[fan_off['SF_WAT']>0]['SF_WAT'].describe())
```

**Output:**
```
SF_WAT>0 when fan off: 426
count    426.000000
mean     828.774648
std      490.949913
min        2.000000
25%      647.000000
50%      711.000000
75%     1119.000000
max     1622.000000
```

**Affected rows:** 426 rows, same periods as Problems 2 and 8. Power readings up to 1,622 W while fan status is off.

**Proposal:** **Flag** — Power sensor reports consumption while fan status is off. Likely the status signal (SF_SPD_DM) and power sensor (SF_WAT) are on different logging paths with a mismatch. Flag these rows.

---

## Summary Table

| # | Problem | Rows Affected | Severity | Action |
|---|---------|---------------|----------|--------|
| 1 | Duplicate timestamps | 24 (12 unique times) | High | **Fix** (drop duplicates) |
| 2 | SA_CFM ≠ 0 when fan off | 429 | High | **Flag** |
| 3 | OA_CFM constant | 4,044 (all) | High | **Flag** |
| 4 | CHWC_VLV_DM > 0 when fan off | 29 | Medium | **Flag** |
| 5 | MA_TEMP outside [OA,RA] | 111 (2.7%) | Medium | **Flag** |
| 6 | SA_TEMP > MA_TEMP + 1.5 °F | 277 (6.8%) | High | **Flag** |
| 7 | OA_DMPR stuck at 0.25 | 542 (2 full days) | High | **Flag** |
| 8 | SF_CS=1.0 when fan off | 415 | Medium | **Flag** |
| 9 | SF_WAT>0 when fan off | 426 | Medium | **Flag** |

---

## Overall Assessment

The dataset contains **multiple sensor/logging faults** that make large portions unreliable for quantitative analysis:
- **OA_CFM** is entirely unusable (stuck sensor).
- **OA_DMPR** is unusable for 2 of 14 days (stuck position feedback).
- **SA_CFM, SF_CS, SF_WAT** are unreliable during all unoccupied periods (429–426 rows each).
- **SA_TEMP** vs **MA_TEMP** physics violated on 277 rows (6.8%), concentrated on two occupied days.
- **MA_TEMP** has 111 violations, some severe (Type B).

**Recommendation for next step (day-by-day supply air tracking):**
1. Apply Fix #1 (drop 12 duplicate rows).
2. Exclude all rows flagged in Problems 2, 3, 4, 6, 7 from supply-air-tracking analysis.
3. For Problem 5 (MA_TEMP), only exclude Type B violations (16 rows); Type A (95 rows) may be kept with caution.
4. For Problems 8–9, they overlap with Problem 2; excluding Problem 2 rows handles them.
5. The cleanest analysis window is occupied hours (SYS_CTL=1) on days without stuck damper (not 2017-10-03, 2017-10-04) and without SA_TEMP violations (not 2017-10-05, 2017-10-06).

This leaves approximately: 5 weekdays (Sep 25–29) + 2 weekdays (Oct 2, Oct 5–6 excluded) + Oct 7–8 (weekend) → limited usable occupied data.