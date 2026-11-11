# Stop 1: An agent builds a website for your students

You ask an agent, in one sentence, for a small website on something you teach. You watch it work. Then you check the pages, because you know the topic better than the model does.

About 35 minutes, from 9:00. You type in the OpenClaw chat, in the terminal at the bottom.

## You will be able to

- Hand a small job to an agent and follow what it does, step by step.
- Find something it got wrong on a topic you teach, and get it fixed with one rule.

## Two things to know first

An agent is a loop. It sends your request to a model, the model asks for a tool (write a file, run a command, fetch a web page), the agent runs it and sends back the result, and this repeats until the job is done. OpenClaw prints a box for every tool call, so you can watch the loop.

The `site/` folder is public. Anyone with its address can open it while your Codespace runs, and it is published to a permanent address by itself. Put nothing private in it.

## Before you start

Write down three things a beginner must get right about your topic, on paper or in a note. Mark the one you would most hate to see wrong.

Pick a narrow topic and a group of students: not "thermodynamics" but "reading a phase diagram, for second-year chemistry majors". The example below uses buffer pH; use yours.

## Do it

1. Find the chat. It is already open in the terminal at the bottom. If you see a `$` prompt instead, type `openclaw chat`.

2. Hand it over. Type one request with your topic and your students, and press Enter:

   ```
   Build site/: three short pages teaching buffer pH to first-year chemistry students.
   ```

   Watch the boxes. Which files does it write? Does any box fetch a web page? If none does, everything on the pages came from the model's memory. A build takes a few minutes this morning, since the whole room shares one model. Do not type again until it answers.

3. Open the site. The agent's last lines give two addresses. Cmd-click (Ctrl-click on Windows) the live one. The permanent one shows a 404 until it is published, usually a minute or two (see The permanent address, below, if it stays that way). Click through every page and compare it with your three things:

   - Did it teach your three things, and the one you marked?
   - Is any number, unit, formula or step wrong?

   Write down the one thing it got wrong or made up. If you find nothing wrong, write the claim you checked hardest and how you know it is right.

4. Ask where the numbers came from:

   ```
   List every numeric claim on the site and say whether a tool call fetched its source.
   ```

   Compare its answer with the boxes you watched. A number is backed by a source only if a box fetched that source.

5. Give it a rule. Turn what you found into one rule for every page, in your own words:

   ```
   New rule: give the units of every quantity that has them, and say so when a quantity has none, such as pH. Fix every page.
   ```

   Refresh the site. Is the error gone, and is everything else still right?

## Checkpoint

Your address shows the agent's pages. Show your pair the one thing it got wrong and the rule you gave it, or the claim you checked and how you checked it.

## Extensions

1. Find the passage that covers the thing you marked and read it to your pair. Right, right but incomplete, or wrong?

2. Ask for sources, then open two of them yourself. Does each page exist, and does it say what the site claims?

   ```
   New rule: every fact cites a public source.
   ```

3. Ask for a quiz, then ask `Which quiz answers did you verify?` and work one question yourself.

   ```
   Add a five-question quiz with answers.
   ```

## The permanent address

You do nothing: about a minute after `site/` stops changing, it is published to `https://<your GitHub name>.github.io/<your repository>/`. To see whether it worked, in a second terminal (the + on the terminal panel):

```
cat ~/.osu-llm-workshop-pages-status
```

`PUBLISHED` means it is out. `NOT PUBLISHED` gives the reason on the same line; ask a helper. `ONE STEP LEFT` means GitHub Pages needs turning on once: open the link it prints (or the repository's Settings, then Pages), set Source to Deploy from a branch, choose `gh-pages` and `/ (root)`, and click Save. Pages needs a public repository on a free account.

## If something goes wrong

- The site says "This site is empty for now": refresh, or click the `site` folder in the Explorer to see what the agent wrote. If its pages are somewhere else, tell it: `Put the pages in site/ at the top of the repository.`
- The address does not open: in the Ports tab, right-click port 8000, Port Visibility, Public.
- An error such as 429, 503 or a timeout: the room shares one model. Wait a minute, then type `Continue.`
- The agent starts a web server: tell it `Stop that server. site/ is already served.`
- OpenClaw says it is not connected: type `/exit`, then `bash setup.sh --openclaw`.

When you are done, `/exit` closes the chat; `openclaw chat` opens it again, and your site stays.
