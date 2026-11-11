# Write your own Record

In Module 3 you renamed one field. Here you write a record from scratch for a kind of document the workshop never saw: a protocol, an instrument manual, a grant abstract, a student reflection.

1. Pick ten documents of one kind and read three of them. Write down, on paper, the six to ten things you would want in a table about them. For each, decide what "not stated" should look like.
2. Open records.py and write a second class next to Record, with one Field per thing and a description written for the model, not for you. Keep every value a str. Add doc_id, source and excerpt; they are what make a row checkable.
3. Point 03_table/starter.py at your class (one import) and run it on one document. Read the excerpt first. If it is not in the document, your description for that field is asking for an inference, not a fact; rewrite it.
4. Run the folder script. Audit three rows. Count the kinds of error. Change one description and run again.

What you will find: most "model errors" are description errors. A field named "outcome" gets guesses; a field described as "the number the authors report as their main result, with its unit, copied from the text" gets facts.
