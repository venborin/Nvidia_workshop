# mine/

Your own material for the day goes here. Every stop works on a shipped public example if this folder is empty, so bringing anything is optional. What is worth bringing:

- One small CSV from your work, for Stop 6 or as an extension in Stop 2 (a few thousand rows is plenty), with a line about what each column means and its units. If it lives in Excel, save a copy as CSV on your laptop first.
- Two or three short research papers as PDFs, for Stop 3: ones you can select text in, not scans.
- One chart from a paper you are reading, as a PNG or JPEG, for Stop 4. A screenshot is fine; an iPhone photo needs exporting as JPEG first.

Drag the files from your laptop onto this folder in the file tree (or right-click it and choose Upload), then check them:

    python upload_check.py

Each file gets `ready` or `NOT READY`, with what it found (the columns of a CSV, whether a PDF has text the model can read, the size of an image) and, when a file will not work, why and which shipped example to use instead. Give a file three minutes at most; then use the example and come back to your own in Stop 6. A Word file becomes text with `python convert.py`; a plain `.txt` file needs nothing.

The data rule. Nothing in this folder is ever committed or pushed: it is listed in .gitignore. But it does leave your laptop: it sits in your GitHub Codespace, which is GitHub's cloud, and when a stop reads a file, its contents are sent to the model service. That is true on OpenRouter and on OSU's Cimarron cluster alike. So bring nothing you would not show that service: no unpublished results you are not free to share, no student records, nothing under an IRB protocol.

`bash catchup.sh` copies your own versions of a stop's files here, into `mine/catchup-backup-<date-time>/`, before it restores that stop, so nothing you wrote is lost.
