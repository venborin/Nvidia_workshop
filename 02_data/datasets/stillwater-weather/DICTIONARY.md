# stillwater_daily_2021-2025.csv: data dictionary

1,824 rows, 20 columns. One row is one calendar day at one station, Stillwater Regional Airport (GHCN-Daily station USW00003965), from 2021-01-01 to 2025-12-31. Requested in US standard units, so temperatures are in degrees Fahrenheit, precipitation and snow in inches and wind in miles per hour; the column names do not say so. A missing value is an empty field (read as NaN by pandas). Two calendar days, 2025-07-11 and 2025-07-12, have no row at all.

- STATION: GHCN-Daily station identifier, always USW00003965.
- NAME: station name, always "STILLWATER REGIONAL AIRPORT, OK US".
- LATITUDE: decimal degrees north, 36.16238.
- LONGITUDE: decimal degrees east (negative is west), -97.08931.
- ELEVATION: station elevation in metres (not feet), 292.8.
- DATE: local calendar day, YYYY-MM-DD.
- AWND: average daily wind speed, miles per hour. 3 missing.
- PRCP: precipitation for the day, inches, to 0.01. 8 missing. A trace (too little to measure) is recorded as 0.00 with T as the first character of PRCP_ATTRIBUTES (178 days), so 0.00 does not always mean nothing fell.
- SNOW: snowfall, inches. Blank on 1,747 days, including the whole February 2021 snowstorm, and 0.0 on every day where it is present (one of them flagged T for trace): this airport station does not measure snowfall reliably. Do not use it.
- SNWD: snow depth, inches. Blank on 1,778 days; same caution as SNOW.
- TMAX: maximum temperature for the day, degrees F, whole degrees. 1 missing.
- TMIN: minimum temperature for the day, degrees F, whole degrees. 2 missing.
- WSF2: fastest 2-minute wind speed for the day, miles per hour. 2 missing.
- *_ATTRIBUTES (one after each value column): comma-separated flags for that value, in the order measurement flag, quality flag, source flag, and for PRCP a fourth field with the observation time (2400, the day ends at midnight). Empty when the value is missing. Values seen in this file:
  - measurement flag: empty (none) or T (trace of precipitation or snow).
  - quality flag: empty in every row here, meaning the value passed NOAA's quality checks.
  - source flag: W (WBAN/ASOS summary of the day from NCEI's Integrated Surface Data), 1 (National Weather Service CF6 daily climate summary), Z (a value added or replaced after an official NCEI investigation; one row).

Warts kept on purpose: units are nowhere in the file, flags live in a separate text column per value, a trace is stored as zero, two days are missing as whole rows rather than blank values, and the snow columns look usable but are not.

Full flag definitions: the GHCN-Daily readme, https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt (section III).
