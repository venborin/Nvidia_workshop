# A saved run of the research question

What `Read 03_lit/question.md and do what it says.` produced on November 8, 2026, with NVIDIA Nemotron 3 Ultra, on the three shipped cover-crop papers, with the first version of the prompt. The prompt was tightened afterwards (table lines as quotes, flag only what cannot be fixed, at most three searches), partly because of what this run did. Use it when the model service is slow or down: click these files in the Explorer and do the "check one row" and "read the answer" steps of Stop 3 on them.

- `values.csv`: 29 reported values, each with its quote, page and conditions. Click it to see the columns in colour.
- `check-log.txt`: the tally of each check the agent ran. The first two runs failed all 23 rows; then 12 passed and 11 were flagged; then six rows from a new search were added and one fixed. (The checker now also logs every row's verdict; this run predates that.)
- `answer.md`: the agent's answer. Its search found a 19-year study (Tautges et al. 2019) in which cover crops raised carbon in the top 30 cm but the full 2 m profile lost carbon, so sampling depth can flip the sign of the effect.
- `sources.bib`: the searched paper the table uses (Tautges et al. 2019), its DOI checked in Crossref. `refs.bib` and `lit-search.json` are the agent's last search, which was not a useful one: it typed a DOI as a search query.
- `papers/`: the text the agent read, page by page (the same text `03_lit/pages.py` prints). Checking the file below also saves Tautges's abstract, the text its `doi:` rows are checked against, as `results/papers/doi_10.1111_gcb.14762.txt`.

Check it yourself, in a second terminal: `python 03_lit/check_values.py 03_lit/saved/values.csv`. Today's checker reports 17 pass, 11 flagged and 1 fail.

It is a real run, not a cleaned-up one, and it has three lessons in it.

1. Flags with the wrong reason. Nine of the eleven flagged rows (Zheng's table values) fail because their quotes are not in the paper word for word, but the agent's note says they were flagged because a concentration cannot be converted without bulk density. The flag got them past the check with a reason that is not the real one. Read every flagged row's failure beside its note.

2. A malformed row. Line 30 (the Tautges warning about shallow sampling) has ten fields, not eleven: the conversion field is missing, so `flagged` sits under conversion, the agent's explanation sits under status, and note is empty. The checker of November 8 passed it; today's checker fails it, because a row whose fields are out of place cannot be trusted, flagged or not. The file is kept as the agent wrote it.

3. A misreading in the answer. `answer.md` says Gentsch found "no detectable stock difference despite concentration increases", and rejects "concentration increase = stock increase" on that basis. Page 4 of the paper (`papers/gentsch2024cover.txt`, section 3.1) says something else: concentrations and stocks in the topsoil both rose from 2015 to 2020, in every treatment, fallow included; what showed no significant difference was cover crops against fallow in 2020. The answer mixed a change over time with a difference between treatments. The Gentsch rows it cites (lines 2 to 4) pass the check, which is the point: the checks confirm where a quote is and that its numbers agree, not that the reading of it is right.
