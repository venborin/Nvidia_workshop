# Module 3: From documents to a table

A literature table, a coding sheet, a log of instrument runs: much of research is reading many documents and filling in the same columns for each. This module turns a folder of documents into that table, one record per document, with a sentence copied from the document beside every main claim so you can check it. The table you write here is what the afternoon's tools search.

About 65 minutes. Folder: `03_table/`. Behind? `bash catchup.sh m3`

## You will be able to

1. Turn a folder of documents into a table of records, each with evidence attached.
2. Audit three rows against their source documents.
3. Say which kind of error you found: a wrong value, a value guessed where the document says nothing, or an excerpt that does not support the claim.

## The idea

A table needs many answers per document, in the same shape every time. So the shape is written down first, in `records.py`, as a record: a fixed list of named fields (`title`, `year`, `method`, `sample_size`, `main_claim`, `excerpt`, and one column you choose), each with a one-line description the model reads.

The helper `ask_json(prompt, Record)` in `llm.py` shows the model that shape and asks for one JSON object (plain text with named values, the format most programs exchange data in). Pydantic, a Python library that checks data against a declared shape, then checks the reply. If a field is missing or the reply is not JSON, the helper sends the error back and the model gets one more try. If that fails too, `run_folder.py` tries the document once more, and if it still fails it writes a row with an `error` field instead of dropping the document. The table always has one row per file.

The right shape is not the same as the right answer. That is why every record carries an excerpt: one sentence the model must copy word for word from the document, supporting its main claim. The program can check that the sentence is really there. Only you can check that it supports the claim. For example, row 16 of the saved run that comes with the repository (`corpus/records.jsonl`), from `corpus/doc_016.txt`, where the excerpt check says yes:

```
main_claim   Artifact scores improved substantially, with the share of submissions that a second person could rerun rising from 21% to 79% and concept inventory scores increasing from a mean of 9.4 to 13.8 of 18 items.
excerpt      The share of submissions that a second person could rerun from the repository alone rose from 21 percent at the start of the module to 79 percent at the end.
```

The excerpt is real, and it backs the rise from 21 to 79 percent. Nothing in it backs the concept inventory scores: the document reports them in the next sentence, but this excerpt does not show them. Auditing means reading each value against the source and deciding which it is: right, wrong, guessed, or unsupported.

## Predict first

Here is the record (`records.py`) and one document. When the whole folder runs, which kind of error will show up first: a wrong value, a guessed value where the document says nothing, or an excerpt that does not support the claim? Write one down.

## Do it

1. Run the starter. It fills one record for `corpus/doc_001.txt` and prints it field by field, excerpt last.

   ```
   python 03_table/starter.py
   ```

   It takes a few seconds. For example:

   ```
   doc_id        doc_001
   source        corpus/doc_001.txt
   title         Free Pizza Increases Office Hours Attendance in Introductory Statistics
   year          2021
   method        experimental
   sample_size   236 students
   main_claim    Across the nine sessions, attendance averaged 7.6 students per session from the afternoon sections and 4.1 from the morning sections, an increase of 85 percent.
   custom_field  not stated
   excerpt       Across the nine sessions, attendance averaged 7.6 students per session from the afternoon sections and 4.1 from the morning sections, an increase of 85 percent.

   Is the excerpt really in the document? yes
   ```

   The last line is the program's check: the excerpt appears word for word in the document, ignoring line breaks. `custom_field` is the column you will name in Exercise 1. Its description asks for nothing in particular yet, so the model may write "not stated" there, or fill it with something from the document that it chose itself. The program, not the model, fills in `doc_id` and `source` from the file itself, so a row always points at the file it came from.

2. Open the record definition and find the fields the model was asked for, and the two lines marked `EDIT 1` and `EDIT 2` at the bottom.

   ```
   code records.py
   ```

   You should see one line per field, each with `Field(description=...)`. The descriptions are the instructions. At the bottom is your column, three lines long, for example:

   ```
   custom_field: str = Field(                                                  # EDIT 1
       description="Fill this in with what your field needs, or 'not stated'.",  # EDIT 2
   )
   ```

   Close the file without changing it for now.

3. Find the excerpt in the document yourself, so you know what the check did.

   ```
   grep -n "attendance averaged" corpus/doc_001.txt
   ```

   For example, `9:Across the nine sessions, attendance averaged 7.6 students per session ...`. Now read the whole of `corpus/doc_001.txt` and decide whether that sentence supports the claim, which two groups it compares, and whether the sample size is right.

## Checkpoint

One record on screen. Read its excerpt aloud to your pair and say whether it supports the main claim, and why.

## Exercises

1. Core: your own column. In `records.py`, change the two marked lines at the bottom and nothing else. On the `EDIT 1` line, replace only the word `custom_field` with the one thing your field would want in every row: lowercase, underscores allowed, no spaces. On the `EDIT 2` line, replace only the sentence between the double quotes, and keep it ending with `or 'not stated'`. Leave `: str = Field(`, the comma, and the closing `)` on its own line as they are. Three worked examples are in the comments just above. Edited, it looks like this:

   ```
   instrument: str = Field(                                                  # EDIT 1
       description="The main instrument or measurement technique named in the document, or 'not stated'.",  # EDIT 2
   )
   ```

   Save, then run one document:

   ```
   python 03_table/starter.py corpus/doc_007.txt
   ```

   Look for your column name in the output, and ask whether the value is what you meant by your description.

2. Core: the whole folder. Run all sixteen documents. Each row prints as it lands, and the end says how many excerpts were found word for word.

   ```
   python 03_table/run_folder.py
   ```

   It takes a few minutes with the whole room on one endpoint. If it is very slow, press Ctrl+C and copy the saved run instead: `python 03_table/run_folder.py --saved`. The saved run has a column named `custom_field`, not yours. The table is `03_table/records.jsonl`: one JSON record per line, in file order, so row 3 is `doc_003`.

3. Core: audit rows 3, 7 and 12. Put each row beside its source:

   ```
   python 03_table/audit.py 3 7 12
   ```

   For each row, open the file it names (row 3 is `corpus/doc_003.txt`) and check every value, your column included. Mark each row as right, wrong value, guessed (a value where the document says nothing), or unsupported excerpt (the sentence is real but does not back the claim). If a row has more than one problem, write the first one you found. Compare with your pair and with your prediction.

4. Core: the evidence page. Turn the table into a web page with every row beside its document:

   ```
   python 03_table/viewer.py
   ```

   It writes two pages and says where. For example:

   ```
   Private page, all 16 rows, with document text. It stays in your Codespace:
     03_table/evidence.html
     To open it: right-click it in the Explorer, choose Download, and open the file.
   Public page, 16 of 16 rows, on your website:
     site/evidence/index.html
     Live now:  https://<your-codespace>-8000.app.github.dev/evidence/
     Permanent: https://<owner>.github.io/<repo>/evidence/

   The public page is published: anyone with the live address can read it now, and it goes on GitHub Pages within a minute.
   ```

   The public copy is in `site/`, so it is on your website the moment it is written. It holds only rows from `corpus/`, the sample documents. `--public-mine` adds rows from `mine/` with their values and excerpts, never their documents. Open the live address. Click a column header to sort, type in the box to filter, and click a row to read its document with the excerpt highlighted. Values that say "not stated" and rows with an `error` field are marked so they stand out. The excerpt backs `main_claim` and nothing else; every other value is the model's reading, which the line at the top of the page says too.

   Each row carries two labels. "Excerpt found in source" is the program's check, the same one `audit.py` makes. "Checked by a person" is yours. When you have audited a row, mark it, then make the pages again:

   ```
   python 03_table/audit.py --mark 3
   python 03_table/viewer.py
   ```

   `--mark` prints the row as usual, then adds its source file to `03_table/checked.txt`, once, with a short fingerprint of its claim and excerpt; if a rerun changes what the row says, the mark no longer applies. Row 3 now says yes.

5. Stretch (optional): the silent document. `corpus/doc_013.txt` states no year and no sample size. Run the starter on it:

   ```
   python 03_table/starter.py corpus/doc_013.txt
   ```

   Look at `year`, `sample_size` and your own column. Did the model write "not stated", or did it fill something in? If it filled something in, find where in the document it could have come from.

6. Stretch (optional): your own documents. If you put files in `mine/` during the pre-work, convert them and run the folder script on them, then audit the first rows:

   ```
   python convert.py
   python 03_table/run_folder.py mine
   python 03_table/audit.py 1 2 3
   ```

   A row number past the end of the table just says `no such row`. Look at which columns come back "not stated" for your kind of document, and whether your own column earns its place. This replaces the table with your documents' rows; to go back to the sample table, run `python 03_table/run_folder.py --saved`.

7. Stretch (optional): what the excerpt does not back. On the evidence page, type `not stated` in the filter box. For each row still showing, open its document and decide whether the document is really silent there. Then clear the filter, click the row with the longest `main_claim`, and read the highlighted sentence against the claim, part by part. Which parts does the excerpt back, and which does it not? Mark each row you finish with `python 03_table/audit.py --mark N`, run `python 03_table/viewer.py` again, and compare how many rows say yes to "excerpt found in source" with how many say yes to "checked by a person".

## What you have now

- `03_table/records.jsonl`: one record per document, each with an excerpt. Modules 4 and 5 search this table, whichever documents it holds.
- `records.py` with your own column, which carries into every later run.
- The evidence page: `03_table/evidence.html` for you, and a public copy of the `corpus/` rows at your site address under `evidence/`.
- `run_folder.py`, the script most people take home: point it at a folder of text files and it writes a table with evidence attached.
- A habit: before you trust a row, read the excerpt against the source, and check that "not stated" appears where the document is silent.

## If something goes wrong

- `Is the excerpt really in the document? NO, check it`. The model changed a word or a symbol while copying, for example "7.3 cm" for "7.3 centimeters". The program did not crash; this is a finding. Open the source, find the nearest sentence, and judge the row as you would any other.
- An error right after you edit `records.py`, such as `SyntaxError` or `NameError`. One of the three lines lost its shape: a missing quote, comma or bracket, or a space in the name. Compare it with the example in Exercise 1, or put the file back with `git checkout records.py` and edit again.
- A row in the table that has an `error` field, such as `"error": "AuthenticationError: Error code: 401 ..."`. The folder script tried that document twice and both tries failed. A reply that was not valid JSON gets one automatic repair inside each try; a network or key problem does not. The row is kept so the count stays right, and the afternoon's tools skip it. Run `python 03_table/starter.py corpus/doc_NNN.txt` on that document to see the full error, or run the folder again. A 401 on every row means the key: `bash setup.sh --reset-key`.
- `No .txt files in mine` from `run_folder.py mine`. Run `python convert.py` first; it writes the `.txt` files the script reads.
- The afternoon's tools show your own documents, or the old placeholder column, when you wanted something else. They read whatever is in `03_table/records.jsonl`. Run `python 03_table/run_folder.py` for the sample corpus with your column, or `--saved` for the saved table.
