# Stop 5: The agent repairs research code

`05_repair/analysis.py` is a short script that once reproduced a published table of penguin measurements. It no longer runs. You hand it to the agent, and it runs the script, reads the error, fixes it, and keeps going until an independent check says the numbers match the published ones. Then you find out whether you understand what it changed.

About 45 minutes, from 1:25, with two demonstrations from the front at the end. Requests to the agent go in the chat; commands you run yourself go in the second terminal.

## You will be able to

- Have an agent repair a broken script against a check it did not write.
- Read what it changed, and say why each change was needed.
- Name the kind of fault that gives no error message.

## Why

Research code rots. A library drops a function the script used. The script expects a folder that exists only on its author's laptop. Someone adds a filter to try something and never removes it. The first two fail loudly. The third runs cleanly and gives a different answer, which is the dangerous kind.

An agent is good at the loud kind. What keeps it honest on the quiet kind is a check it cannot edit: `05_repair/check_expected.py` runs the script and compares its output with the published numbers in `05_repair/EXPECTED.md`.

## If the instructor says Cimarron is up

Only if the whole room is told to move together: click `05_repair/CIMARRON.md` and follow it before you start. Otherwise skip this.

## Do it

1. Run it yourself first, in the second terminal, and read the error:

   ```
   python 05_repair/analysis.py
   ```

2. Hand it over. In the chat, type `/new` and press Enter. Then:

   ```
   Run python 05_repair/analysis.py, reproduce the failure, fix the code, then run python 05_repair/check_expected.py until it passes. Explain the change in one paragraph.
   ```

   Watch the loop: run, error, edit, run again.

3. Check it yourself, in the second terminal:

   ```
   python 05_repair/check_expected.py
   ```

   It should end with `PASS`. Then read what the agent changed:

   ```
   git diff HEAD -- 05_repair/
   ```

   Lines starting with `-` were removed and lines starting with `+` were added. (If it ends with `:`, press the space bar for more and `q` to leave.) The check itself and `EXPECTED.md` should not appear in the diff: the agent must fix the script, not the check.

4. Find the quiet fault. One of the changes fixed a line that ran without any error and gave wrong numbers. Write down which line it was, and what it did to the count of each species. If this were your script, what one check would you add?

## Checkpoint

The check prints PASS, the check file is unchanged, and you can tell your pair what each change fixed.

## Extensions

1. Ask the agent to add the median body mass per species. There is no published number for that: how would you check it?
2. Ask the agent to write a test for the quiet fault, so it fails if anyone adds that filter again.
3. A script of your own with a known problem, from `mine/`: the same request, with a number you know is right as the check.

## Then, from the front

Two demonstrations: the same task given to five models with their names hidden, and the same work on OSU's Cimarron cluster. The check you just used is how you would try a smaller, cheaper model on your own work: same task, same check, and measure how often it passes.

## If something goes wrong

- The agent edits `check_expected.py` or `EXPECTED.md` to make the check pass: that is the failure this stop is about. In the second terminal, `git checkout HEAD -- 05_repair/check_expected.py 05_repair/EXPECTED.md` puts them back. Then tell it: `Do not change the check or the expected numbers. Fix analysis.py.`
- It stops without running the check: type `Now run python 05_repair/check_expected.py.`
- It installs an older pandas: tell it `Use the installed pandas; change the code.` and ask a helper to put the workshop's version back.
- Start over: `bash catchup.sh s5` in the second terminal restores the broken script.
