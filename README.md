# Building with LLMs: a one-day hands-on workshop

What an AI agent can do for a researcher, one stop at a time. Oklahoma State University, Digital Scholarship Center, Edmon Low Library, Wednesday, November 11, 2026. Instructor: John Hassell, OU Polytechnic Institute.

You work in a GitHub Codespace: VS Code in a browser tab, on a machine GitHub runs for you. Nothing is installed on your laptop. In it, an AI agent works in your folder: it runs code on files and leaves programs that run again. The morning uses shared public examples, so the room can compare results. Your own papers are welcome in Stop 3, and the afternoon is built on your own material.

## Before the workshop: about ten minutes

You need a free GitHub account and a laptop with a current browser.

1. Make your copy. At the top of this page, click the green **Use this template** button, then **Create a new repository**. Any name is fine. It is yours.

2. Open a Codespace. On your new repository, click the green **Code** button, the **Codespaces** tab, then **Create codespace on main**. The first start takes two or three minutes.

   ![The Code button's Codespaces tab](docs/figures/01-code-menu.svg)

3. Click **Trust Folder & Continue** when VS Code asks. Until you do, no terminal can start.

   ![Click Trust Folder and Continue](docs/screenshots/A-trust-folder-and-continue.png)

4. Press Enter when the terminal asks for a key. You get the word for it on the morning. The terminal prints:

       Codespace ready; endpoint check pending.

   That line means you are done. (If you see only a line ending in `$`, type `bash setup.sh` and press Enter.)

5. Stop the Codespace at <https://github.com/codespaces>, in the **...** menu beside it. It keeps your files and restarts in seconds on the day.

## Your own material: optional

Every stop works on an example that comes with the workshop. If you would like to use your own, this is where each kind fits:

- Two or three research papers as PDFs you can select text in, not scans: Stop 3.
- A chart from a paper, as a PNG or JPEG (a screenshot is fine): Stop 4.
- A small CSV, documents you read every week, or a script of yours: Stop 6, the afternoon build.

To load them, drag them from your laptop onto the `mine` folder in the file list on the left. Then, in the terminal, run `python upload_check.py`: it says whether each file is ready.

One rule: whatever you upload is stored in your GitHub Codespace, and what the agent reads is sent to the model service. Bring nothing unpublished that you are not free to share, no student records, and nothing under an IRB protocol.

## On the morning

1. Open your Codespace at <https://github.com/codespaces>.
2. Setup starts by itself in the terminal. Type the workshop word, shown at the front of the room, and press Enter.
3. When it says `✅ OpenClaw is connected`, put the green note on the back of your laptop lid. Stop 1's page is already open, and so is the agent's chat.

## The day

| Time | Stop | Folder |
|---|---|---|
| 8:30 | Setup: the workshop word | `00_setup/` |
| 9:00 | 1. An agent builds a website for your students | `00_website/` |
| 9:35 | 2. Your data, analyzed and reproducible | `02_data/` |
| 10:45 | Break | |
| 11:00 | 3. A research question, answered from papers you can check | `03_lit/` |
| 12:15 | Lunch | |
| 1:00 | 4. A chart back into data | `04_see/` |
| 1:25 | 5. The agent repairs research code | `05_repair/` |
| 2:10 | Break | |
| 2:25 | 6. Build one thing from your week | `06_build/` |
| 4:00 | Show and tell, in pairs | |
| 4:25 | Close, and saving your work | |

Each stop is a folder, and the `README.md` in it is the whole lesson. Click it in the file list: it opens formatted, and every box of text to type has a Copy button.

Two places to type, all day. Requests to the agent go in the chat, in the terminal at the bottom. Commands you run yourself go in a second terminal: click the **+** at the top right of the terminal panel.

Behind? `bash catchup.sh s3` restores Stop 3's files so you can start there (`s2` to `s6`). Your own versions are copied to `mine/` first.

## Where your work goes

- `results/`: everything a stop makes. It is never committed, because it can hold your data. `bash export.sh` packs it into a zip to download.
- `mine/`: what you brought. Never committed.
- `site/`: the website from Stop 1. It is public on the internet, so nothing private goes in it.

## If something goes wrong

- Only a line ending in `$`, and setup never started: type `bash setup.sh`.
- "That word is not the workshop word": type it again, as shown at the front of the room. Letter case does not matter.
- No terminal at all: the **☰** menu at the top left, **Terminal**, **New Terminal**.
- The chat is gone and you see a `$` prompt: type `openclaw chat`.
- The agent is slow, or shows 429 or a timeout: the whole room shares one model. Wait a minute, then type `Continue.`
- The chat gets slow and forgetful: each stop starts with `/new` for this reason.
- Anything else: put up your pink note. Each stop's page ends with its own list, and helpers carry `00_setup/troubleshooting.md`.

![The ☰ menu, Terminal, New Terminal](docs/screenshots/F-menu-terminal-new-terminal.png)

## After the day

The workshop word stops working when the day ends. Everything you built keeps working with a key of your own: run `bash setup.sh --reset-key` and paste it. `followon/continue.md` says how to get a key and what to try next.

The day's third step is the same agent with its model on OSU's Cimarron cluster instead of at a commercial provider. Whether a Cimarron endpoint stays up after November 11 is the HPCC's decision: ask them, and ask about an account for your own work, at <https://hpcc.okstate.edu>.

## What is in the repository

- `00_setup/` to `06_build/`: one folder per stop, with its page and its helper programs.
- `corpus/papers/`: three open-access papers for Stop 3. `corpus/SOURCES.md` gives the source and license of every shipped dataset, paper and chart.
- `setup.sh`, `catchup.sh`, `export.sh`, `upload_check.py`: setup, catching up, saving your results, and checking your files.
- `llm.py` and `agent.py`: how the helpers call the model, and the agent's loop in about forty lines.
- `followon/`: for going further on your own, including the first version of this day as six modules (`followon/old-modules/`; `03_table/`, `docs.py`, `records.py` and the invented documents in `corpus/` belong to it).

## Credits and license

Original material written for this workshop. The Codespace machinery is adapted from [jhassell/asee9](https://github.com/jhassell/asee9). The datasets, papers and charts are real and public; the sixteen `corpus/doc_*.txt` documents are invented. Licensed under CC BY 4.0 (see LICENSE), except the shipped datasets and papers, which keep their own licenses.

This workshop carries no certificate. For an NVIDIA credential in this area, take the NVIDIA-Certified Associate: Generative AI LLMs (NCA-GENL) exam separately.
