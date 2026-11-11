# Stop 2: Your data, analyzed and reproducible

An agent investigates a data file and shows you what is wrong with it. You check its work, and correct it where you know better. Then it writes one script that rebuilds the whole analysis.

Today everyone uses the same file, so the room can compare what each agent found. The four moves below are what you take home to your own data.

About 70 minutes, from 9:35. Requests to the agent go in the chat. Commands you run yourself go in a second terminal: open one now with the + at the top right of the terminal panel.

## Four moves, and why each one

1. Investigate before you analyze. A report built on bad data looks just as polished as one built on good data. So the agent's first job is to find what is wrong with the file, and prove it.
2. Check it yourself. The agent wrote the findings, and the code behind them. A check it did not write is the only independent evidence you have.
3. Correct it with what you know. The agent knows Python; you know the subject. When you see something it missed, give it your reason and make it test the idea.
4. Keep the script, not the chat. A chat is gone tomorrow. A script rebuilds every number next month, on new data, without the agent.

## The file, in one minute

Two weeks of readings from one air handler, the machine that cools and ventilates a floor of an office building. You do not need to be an engineer. Three facts are enough to judge what the agent finds:

- It logs one reading every 5 minutes for 14 days. That should be 14 × 288 = 4,032 rows.
- Its job is to send air into the building at 55 F. That target is called the setpoint. When the supply air is far from 55, either the weather explains it or something is broken.
- The building has Chicago weather, and every temperature is logged in degrees F.

Several things in the file are wrong. Every column is explained in `02_data/datasets/hvac-ahu/DICTIONARY.md`.

## First, from the front

The instructor gives the agent this file twice: once with "Analyze this CSV.", and once with the request you are about to send. Watch what changes.

## Do it

1. Investigate. About 20 minutes.

   In the chat, type `/new` and press Enter, to start fresh. Click `02_data/investigate.md` and read the request. Then, in the chat, type:

   ```
   Read 02_data/investigate.md and do what it says.
   ```

   It takes about two minutes. Each box is one step the agent chose. An `exec` box is a command it ran, usually Python it wrote. Notice when a result sends it to look somewhere new.

   Then click `results/findings.md`. Pick one finding and look for its four parts: the code it ran, what the code printed, which rows are affected, and what it proposes to do. Would that evidence convince a colleague?

2. Check it yourself. About 5 minutes. In the second terminal:

   ```
   python 02_data/check.py
   ```

   It prints three things. Compare each with what you know about the file:

   - The number of rows. Is it the 4,032 you expect?
   - How many rows are exact repeats.
   - The outdoor temperature for each day. Do all fourteen days look like the same city in the same season?

   Then look at the findings again. Did the agent report everything you can see here?

3. Correct it. About 5 minutes.

   If your check shows something the findings missed, tell the agent in one line, in the chat. A good correction has three parts: what you saw, what you think it is, and why. For example, on a different file, someone might type: `The pressure reads zero every night at 2:00. I think the sensor resets, because it is the same minute each night. Verify, flag those rows, and update findings.md.`

   Then watch: does the agent test your idea with code, or just agree with you? Click `results/findings.md` again. Is your correction there, with its evidence?

   If the findings already cover everything you saw, go on to step 4. Stuck? There is a hint at the bottom of this page.

4. Build the script. About 20 minutes. Click `02_data/reproduce.md` to read it. Then, in the chat:

   ```
   Read 02_data/reproduce.md and do what it says.
   ```

   When it is done, run the script yourself, in the second terminal. This is the proof that it works without the agent:

   ```
   python results/analysis.py
   ```

   Click `results/report.md` and `results/figures/tracking.png`. Then trace one number: pick a number in the report and find it in what the script printed. If it is not there, tell the agent: `Which line of output does each number in the report come from? Fix the script so every one is printed.`

## Checkpoint

Show your pair three things: one problem the agent found, with its evidence; what your own check caught, or confirmed; and `python results/analysis.py` running.

## For the debrief

- What did the agent find that you would have missed?
- What did you know that it did not?
- On your own data, what is the one number you would always check yourself?

## Extensions

1. Your own CSV, in `mine/`. Click `02_data/investigate-mine.md`, fill in the brackets, save (Cmd-S, or Ctrl-S), and send `Read 02_data/investigate-mine.md and do what it says.`
2. Make it break. Ask the agent to run the script on a copy of the file with ten rows deleted. Does the report change?

## If something goes wrong

- No `findings.md` after a few minutes: look at the chat. If the line went to a `$` prompt instead, type `openclaw chat` and send it again. If the agent only answered in words, type `Write results/findings.md now.` If it wrote `02_data/findings.md` instead, type `Move it to results/findings.md.`
- It runs `pip install`: tell it `Use the libraries already installed.`
- 429 or a timeout: the room shares one model. Wait a minute, then type `Continue.`
- The chat gets slow: type `/new`, then `Read results/findings.md and results/analysis.py, then continue.`

## A hint for step 3

Only if you are stuck. In what `check.py` printed, look at the outdoor temperature on September 30 and October 1, and remember the third fact about the file. One line that works:

```
Sep 30 and Oct 1 are in Celsius: Chicago is never 12 F in late September, and it changes at midnight. Verify, convert, and update findings.md.
```
