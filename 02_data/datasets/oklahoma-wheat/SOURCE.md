# ok_county_winter_wheat_2000-2025.csv: source

File: ok_county_winter_wheat_2000-2025.csv, 2,441,480 bytes, 7,156 data rows plus a header. SHA-256 90a4fd2aab7dc7647da528e0677e21af51f64a08e1c98bc8a7ee07ae8769e86d.

Source: USDA National Agricultural Statistics Service (NASS), Quick Stats database, crops sector bulk file qs.crops_20261105.txt.gz (1,132,568,713 bytes, last modified 2026-11-05), from https://www.nass.usda.gov/datasets/ (direct link https://www.nass.usda.gov/sites/default/files/datasets/qs.crops_20261105.txt.gz). Retrieved 2026-11-06.

Why the bulk file: the Quick Stats API needs a registered key (a request without one returns HTTP 401), and the bulk files need none. The Quick Stats web query builder gives the same rows (Program: Survey; Sector: Crops; Group: Field Crops; Commodity: Wheat; Geographic level: County; State: Oklahoma), with friendlier column headers.

The extract keeps every column of the bulk file unchanged and every row matching

    SOURCE_DESC == "SURVEY" and AGG_LEVEL_DESC == "COUNTY" and STATE_ALPHA == "OK"
    and COMMODITY_DESC == "WHEAT" and CLASS_DESC == "WINTER" and YEAR >= 2000

in the bulk file's row order. The only change is the delimiter: the bulk file is tab separated, this file is comma separated with standard CSV quoting. The bulk file is too large to ship (about 1 GB compressed).

License: public domain. Verified on NASS's own Citation Request page, https://www.nass.usda.gov/Data_and_Statistics/Citation_Request/index.php (last modified 05/04/2018, read 2026-11-06): "Most of the information available from this site is within the public domain. Public domain information on the National Agricultural Statistics Service (NASS) Web pages may be freely downloaded and reproduced. However, it is requested that in any subsequent use of this work, USDA-NASS be given appropriate acknowledgment." Quick Stats survey estimates are works of the US government (17 U.S.C. 105).

Cite as:

USDA National Agricultural Statistics Service. Quick Stats, crops sector bulk file qs.crops_20261105. Winter wheat county estimates for Oklahoma, 2000 to 2025. https://quickstats.nass.usda.gov/ (accessed 2026-11-06).
