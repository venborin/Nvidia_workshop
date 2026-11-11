# Stop 6: ideas by field

Examples to start from in Stop 6 (`06_build/README.md`), if none of its three recipes is already your week.

Each says what it runs on: shipped (in the repository now), your files (the PDFs or CSV you brought), or later (a file you would have to fetch first). The recipe 1 tool reads PDF, `.txt` and `.md`, so save tool output as `.txt`. The ones marked "own idea" need a helper's yes that they fit in an hour. Everything you feed them follows the day's rule: nothing you are not free to send to the model.

Building systems and HVAC:
- A trend-log screener, from your Stop 2 script (own idea, close to recipe 2; shipped). Ask the agent to make `results/analysis.py` take any trend export as an argument and write what is wrong with it, each problem with the rows that show it. Unseen input: one week cut from the air-handler file. Bad input: the same file with two columns renamed.
- A methods table over papers on your system type (recipe 1; your files): climate zone, system, control strategy, and the savings claimed, each with its quote and page.

Molecular simulation:
- A methods table over papers you cite (recipe 1; your files): force field, water model, timestep, ensemble, simulation length.
- A run checker (own idea; later): an energy series exported as text (a GROMACS `.xvg`, or a LAMMPS thermo table) becomes plots of energy, temperature, pressure and density over time, with a run that blew up or never settled flagged. Bad input: the same file cut off halfway.

Microbial genomics:
- A methods table over papers (recipe 1; your files): sequencing platform, assembler, coverage, annotation pipeline.
- A genome QC table (recipe 1; later): QUAST or CheckM reports saved as `.txt` become one table of contigs, N50, completeness and contamination, each value with the line it came from.

Computing and research computing:
- A cluster usage page (recipe 2; later): Slurm `sacct` output saved as CSV. Two steps: the agent writes the analysis as in Stop 2, then the page shows use by partition, failed jobs and their reasons, and queue wait, with every number one the script printed. Leave user names out of the file.
- A ticket or interview coder (recipe 1's interview mode; shipped, or later your own): support tickets or transcripts become category, software, cause and resolution, each code with the sentence it rests on. Start on the shipped interviews; with your own, invented or anonymized text only, never names.
- A frozen-answer check for a script of yours (own idea, from Stop 5; your files): pin its published numbers in an expected file, then let the agent upgrade or tidy the script until the check passes, and read the diff yourself. Only for a small script that runs in seconds.

Anyone:
- A literature digest on your own topic (recipe 3; shipped): your query saved in the script.
- A reference checker (own idea, from Stop 3; shipped, then your own): a `.bib` file, or a `.txt` list with one reference per line, becomes `results/refs-check.csv`: each reference as printed, its DOI, the title and first author the tool passed on, and the state and reason from `lit.verify` in `03_lit/lit.py`, the only source of the verdict (`lit.verify` says verified only when it is given both the title and the first author). Start: `Make 06_build/refs/check_refs.py: for a .bib or .txt list of references, write results/refs-check.csv with one row per reference, its DOI, the title and first author it passed, and the state and reason from lit.verify in 03_lit/lit.py, called with the DOI, the title and the first author. Run it on 03_lit/saved/refs.bib.` Build its sample only from that file: an agent asked for a sample may write references that do not exist. Unseen input: five references copied from a paper your partner cites. Bad input: three references, one real, one with a digit of its DOI changed, one made up. The real one must say verified; the other two must not (missing, or mismatched if the changed DOI happens to belong to another paper).
- A funding-call table (recipe 1; later, a solicitation PDF downloads in a minute): deadline, page limit, budget cap, eligibility and required sections, each with its quote and page.
- A data dictionary maker (own idea, from Stop 2; your CSV, or a shipped dataset with its `DICTIONARY.md`): each column's type, missing count, range and suspicious values, all computed by pandas, and its meaning and unit from `ask_json` in `llm.py`, with the notes sentence it quoted, or "unknown". Unseen input: `02_data/datasets/stillwater-weather/` with its `DICTIONARY.md`. Bad input: the penguins file with a row of units under the header, blank under the text columns. pandas reads it without complaint, as text, so the tool must notice and write no dictionary.
