# Stop 2, step 1: the investigation

## For you: what this exercise is about

You are about to hand a real data file to an AI agent: two weeks of readings, one every five minutes, from the air handler that cools and ventilates one floor of a building. Several things in the file are wrong, on purpose, the way real exported data often is.

Most people would ask an AI to "analyze this file". Here the agent investigates first. It chooses its own checks, writes and runs Python for each one, reads what comes back, and decides what to look at next. It writes down every problem it finds, with the evidence, and then it stops, before any analysis.

What this shows: an agent does real work in your folder, not just talk. It also shows the limit: it will miss things, and you, the person who knows the subject, catch them. That is step 2 and step 3.

To start, type in the chat: `Read 02_data/investigate.md and do what it says.`

## For the agent: the request

(The section above is for the person. Do what this section says.)

Read 02_data/datasets/hvac-ahu/DICTIONARY.md, then investigate 02_data/datasets/hvac-ahu/ahu_trend_2017-09-25_to_2017-10-08.csv. One row is one 5-minute reading from one air handling unit.

Later we will compare, day by day, how closely the supply air temperature follows its setpoint while the fan runs. Before that, check the data. Choose your own checks, run them, and follow up anything suspicious.

Write results/findings.md, in the results folder at the top of the repository (not in 02_data/), most important problem first. For each problem: the code you ran, what it printed, the rows affected (which days and times), and what you propose to do about it (fix, flag, or leave alone), with a reason. Keep what you observed separate from how you explain it.

Do not change the raw file. Do not clean the data or make plots yet: stop when findings.md is written, and tell me in a few lines what you found.
