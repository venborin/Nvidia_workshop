# Stop 4: A chart back into data

A model that can see reads a chart and gives you back the numbers behind it, as a table. Then you check the table against the data the chart was drawn from. You will find one chart where it is good enough to use, and one where a complete, confident table is wrong.

About 25 minutes, from 1:00. No chat in this stop: you run commands in the second terminal and click pictures in the Explorer.

## You will be able to

- Get the data out of a chart image as a table.
- Measure how far the numbers are from the truth.
- Say which kinds of chart you would trust this on.

## Why

Researchers read numbers off published figures by hand when a paper gives a chart but not its data. A model does it in one request. How well depends on the chart, so every shipped chart comes with the data it was drawn from, and `compare.py` measures the error. The model here is NVIDIA Nemotron 3.5 Super VL, which reads images; a request takes ten to forty seconds.

A chart is a measurement you can extract. A micrograph, a gel or a photo is not: a number the model gives you from one of those is a guess.

## Do it

1. From memory first. In the second terminal, type the command that reruns this morning's analysis, without looking it up. Did it rebuild the report? If you cannot remember it, it is in step 4 of Stop 2's page (`02_data/README.md`): write it down. (No script from Stop 2? Run `python 02_data/datasets/penguins/reference/analysis.py` instead.)

2. Read a chart. In the Explorer, open `04_see`, then `charts`, and click `penguin_bars.png` to look at it. Then, in the second terminal:

   ```
   python 04_see/see.py 04_see/charts/penguin_bars.png --extract
   ```

   It saves the table as `results/seen/penguin_bars.csv`.

3. Check it against the truth:

   ```
   python 04_see/compare.py 04_see/charts/penguin_bars.png results/seen/penguin_bars.csv
   ```

   It prints an error table. How to read it:

   - The first row is the x axis. `matched`, on every row, says how many of the chart's points the model read (3/3 is all of them). `extra` counts points the model gave that the chart does not have.
   - Then one row for each set of bars or points, and one for each set of error bars. `mean_err` and `max_err` are the average and largest error, in the chart's own units. `pct_range` is the average error as a percent of the data's range.

   Click `results/seen/penguin_bars-compare.png`: the original, the replot, and both together. Is about one percent good enough for what you would use these numbers for?

4. Now the hard one, the same two commands on a chart with hundreds of overlapping points:

   ```
   python 04_see/see.py 04_see/charts/dense_overlap.png --extract
   python 04_see/compare.py 04_see/charts/dense_overlap.png results/seen/dense_overlap.csv
   ```

   Read the error table, then click `results/seen/dense_overlap-compare.png`. Where does the model follow the points, and where does it draw a line of its own? The table looks just as complete as the first one. Only the check shows the difference.

## Checkpoint

Show your pair the two comparison pictures, and say in one sentence which charts you would trust this on and which not.

## Extensions

1. Your own chart. Drag a PNG or JPEG onto `mine/`, then run the same two commands with its name. There is no truth file, so the replot beside the original is your check.
2. Ask a plain question: `python 04_see/see.py 04_see/charts/co2_line.png "What is on each axis, with units?"`
3. Let the agent judge. Click `04_see/judge.md` to read it. In the chat, type `/new`, then `Read 04_see/judge.md and do what it says.` Compare its verdict with the error table it printed.
4. All six shipped charts, ranked: `python 04_see/smoke_test.py` (a few minutes).

## If something goes wrong

- It is slow, or says it is trying again: the model thinks at length and the whole room is asking. Let it run.
- The model is down: saved results are in `04_see/saved/`. Click `penguin_bars-compare.png` and `dense_overlap-compare.png` there; that is the checkpoint.
- "The reply is not a table": nothing was saved. Run the `--extract` command again.
- A series or a category shows as not read (`0/3 matched`): the model left it out or renamed it. Run `--extract` again.
- "Stop 4 needs OpenRouter": run `bash 00_setup/switch_backend.sh openrouter`, then the command again.
- The replot looks wrong only because of its scale: add `--yscale log` to the compare command if the original has a logarithmic axis.
