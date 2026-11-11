# The workshop's datasets

Four public datasets, used in Stop 2 and later. Each folder has the raw file, DICTIONARY.md (what each column means, its units, how missing values look) and SOURCE.md (where it came from, the license, how to cite it).

- hvac-ahu: two weeks of 5-minute trend data from one building air handling unit: temperatures, fan, damper and valve commands, five zones. Simulated by Lawrence Berkeley National Laboratory for the U.S. Department of Energy's fault detection research, excerpted for this workshop. Several things in it are wrong, and finding them is the exercise; the answers are shown from the front at the end of the stop. CC BY 4.0.
- penguins: 344 adult penguins from three species near Palmer Station, Antarctica, 2007 to 2009. Bill, flipper and body measurements, sex, blood isotopes. CC0.
- stillwater-weather: daily high and low temperature, precipitation and wind at Stillwater Regional Airport, 2021 to 2025, from NOAA. Public domain.
- oklahoma-wheat: winter wheat yield, acres and production for every published Oklahoma county, 2000 to 2025, from USDA NASS. Public domain.

Stop 2 uses the air handler (`02_data/investigate.md`). The other three are used later in the day (Stops 5 and 6) and are here for practice; `02_data/investigate-mine.md` is a prompt you can fill in for any of them, or for your own file.

The last three are the raw files as their sources give them, warts included. Each of their reference/ folders holds a completed run to compare yours against once you have your own: analysis.py rebuilds the figures and report.md from the raw file, and extension.py runs the one rehearsed inferential model for that dataset and writes extension.md. Look after you have tried, not before. From the labs/ folder:

    python 02_data/datasets/penguins/reference/analysis.py
    python 02_data/datasets/penguins/reference/extension.py
