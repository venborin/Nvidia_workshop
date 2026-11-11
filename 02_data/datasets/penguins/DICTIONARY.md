# penguins_raw.csv: data dictionary

344 rows, 17 columns. One row is one adult penguin sampled at its nest in one breeding season (2007 to 2009), near Palmer Station, Antarctica. Missing values are written as the letters NA (336 of them across the file), which pandas reads as missing (NaN) by default; a text editor shows them as NA, not as empty fields. Column names are exactly as in the file, units included where the file has them.

- studyName: sampling season, PAL0708, PAL0809 or PAL0910 (the 2007-08, 2008-09 and 2009-10 austral summers). No missing values.
- Sample Number: running sample number within a species across all three seasons (Adelie 1 to 152, Chinstrap 1 to 68, Gentoo 1 to 124). Integer, no units. No missing values.
- Species: common and Latin name. Three values, written inconsistently: "Adelie Penguin (Pygoscelis adeliae)", "Chinstrap penguin (Pygoscelis antarctica)", "Gentoo penguin (Pygoscelis papua)". The first word is a safe short name. No missing values.
- Region: Palmer LTER sampling region; always "Anvers". No missing values.
- Island: Biscoe, Dream or Torgersen. Gentoo nest only on Biscoe and Chinstrap only on Dream in this study. No missing values.
- Stage: reproductive stage at sampling; always "Adult, 1 Egg Stage". No missing values.
- Individual ID: nest and adult, for example N12A2 is adult 2 of nest 12. The same N number appears in different seasons and species, so the reference analysis identifies a nest by studyName, Species, Island and the N number together. The two adults of a nest are a mated pair. No missing values.
- Clutch Completion: "Yes" if the study nest was seen with a full clutch of two eggs, "No" otherwise (36 rows). No missing values.
- Date Egg: date the study nest was first seen with one egg, YYYY-MM-DD, from 2007-11-09 to 2009-12-01. No missing values.
- Culmen Length (mm): length of the dorsal ridge of the bill (the palmerpenguins package calls it bill_length_mm), millimetres, measured with dial calipers to 0.1 mm. 2 missing.
- Culmen Depth (mm): depth of the bill, millimetres, to 0.1 mm. 2 missing.
- Flipper Length (mm): right flipper length, millimetres, ruler to 1 mm. 2 missing.
- Body Mass (g): body mass, grams, spring scale (25 g or 50 g resolution). 2 missing. The same two birds (N2A2 Adelie, N38A2 Gentoo) are missing all four measurements.
- Sex: MALE or FEMALE, from molecular sexing of a blood sample. 11 missing (primers did not amplify or no blood).
- Delta 15 N (o/oo): nitrogen stable isotope ratio 15N/14N of red blood cells, parts per thousand (per mil) relative to atmospheric N2. Higher means feeding higher in the food web. 14 missing.
- Delta 13 C (o/oo): carbon stable isotope ratio 13C/12C of red blood cells, per mil relative to Vienna PeeDee Belemnite. 13 missing.
- Comments: free text from the field or lab, such as "Nest never observed with full clutch." or "Sexing primers did not amplify." NA (missing) for 290 rows.

Warts kept on purpose: units live in the column names, names contain spaces and parentheses, species is a long string rather than a short code, and the missing values are not all in the same rows.
