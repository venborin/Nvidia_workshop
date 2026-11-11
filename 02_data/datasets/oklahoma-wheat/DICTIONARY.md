# ok_county_winter_wheat_2000-2025.csv: data dictionary

7,156 rows, 39 columns, in NASS Quick Stats' own long format: one row is one statistic (yield, acres planted, acres harvested or production) for one Oklahoma county, one production practice and one harvest year. To get one row per county-year, filter and pivot on SHORT_DESC. Every value is stored as text. A missing value is an empty field; there are no NASS suppression codes such as (D) in this extract. Harvest years run 2000 to 2025, and 2024 is absent: NASS announced in April 2024 that it was discontinuing county estimates for crops for budget reasons, and county estimates are present again for 2025.

The columns that vary, and matter:

- SHORT_DESC: what the row measures, with units. Twelve values: for all production practices, "WHEAT, WINTER - YIELD, MEASURED IN BU / ACRE", "WHEAT, WINTER - ACRES PLANTED", "WHEAT, WINTER - ACRES HARVESTED", "WHEAT, WINTER - PRODUCTION, MEASURED IN BU"; and the same four with ", IRRIGATED" or ", NON-IRRIGATED" after WINTER (2000 to 2009 only).
- STATISTICCAT_DESC: YIELD, AREA PLANTED, AREA HARVESTED or PRODUCTION.
- UNIT_DESC: BU / ACRE (bushels per harvested acre), ACRES, or BU (bushels; a bushel of wheat is 60 pounds).
- PRODN_PRACTICE_DESC: ALL PRODUCTION PRACTICES, IRRIGATED or NON-IRRIGATED. The last two split the first and must not be added to it.
- YEAR: harvest year (winter wheat is sown in autumn and harvested the next May to July).
- VALUE: the number, as text with thousands separators, for example "10,289,000". Yield has at most one decimal place (older years are whole bushels); acres and bushels are whole numbers.
- CV_%: coefficient of variation of the estimate, percent. Filled in for 948 rows, all from 2020 on; empty otherwise.
- COUNTY_NAME: county, upper case. "OTHER (COMBINED) COUNTIES" (within a district) and "OTHER COUNTIES" (statewide, 2020 on) are not counties but pools of counties NASS did not publish separately.
- COUNTY_CODE: three-digit county code; 998 marks the combined rows above (688 rows).
- COUNTY_ANSI: county FIPS code within the state, three digits; empty on the combined rows.
- ASD_CODE and ASD_DESC: agricultural statistics district (crop reporting district): 10 Panhandle, 20 West Central, 30 Southwest, 40 North Central, 50 Central, 60 South Central, 70 Northeast, 80 East Central, 90 Southeast. Code 99 with an empty name is the statewide "OTHER COUNTIES" pool.
- LOCATION_DESC: state, district and county in one string, for example "OKLAHOMA, CENTRAL, POTTAWATOMIE".
- LOAD_TIME: when NASS loaded the row into Quick Stats, YYYY-MM-DD HH:MM:SS. Not a measurement.

Columns that are constant in this extract: SOURCE_DESC (SURVEY), SECTOR_DESC (CROPS), GROUP_DESC (FIELD CROPS), COMMODITY_DESC (WHEAT), CLASS_DESC (WINTER), UTIL_PRACTICE_DESC (ALL UTILIZATION PRACTICES), DOMAIN_DESC (TOTAL), DOMAINCAT_DESC (NOT SPECIFIED), AGG_LEVEL_DESC (COUNTY), STATE_ANSI and STATE_FIPS_CODE (40), STATE_ALPHA (OK), STATE_NAME (OKLAHOMA), COUNTRY_CODE (9000), COUNTRY_NAME (UNITED STATES), FREQ_DESC (ANNUAL), BEGIN_CODE and END_CODE (00), REFERENCE_PERIOD_DESC (YEAR), WATERSHED_CODE (00000000). Always empty: REGION_DESC, ZIP_5, WATERSHED_DESC, CONGR_DISTRICT_CODE, WEEK_ENDING.

Warts kept on purpose: long format, numbers as text with commas, a practice breakdown that double counts if summed, pooled pseudo-counties, a missing year, and a falling number of published counties (68 to 75 a year to 2007, 38 to 55 from 2008), so averages across counties change partly because the set of counties changes.

Quick Stats column definitions: https://quickstats.nass.usda.gov/api (the table of column names and their definitions on that page).
