#!/usr/bin/env bash
# Behind? Restore one stop's files from the repository, then start there.
#
#   bash catchup.sh s2      restores 02_data/ (and so on for s3, s4, s5, s6)
#   bash catchup.sh s6      also, if results/ has no Stop 2 analysis yet, puts in
#                           results/analysis.py, which reruns a shipped dataset's
#                           finished analysis, so the page recipe has one to build from
#
# The old six modules, now in followon/old-modules/, restore the same way:
#   bash catchup.sh m4      restores followon/old-modules/04_tool/, and copies in
#                           the saved records table if yours has no usable rows
#
# Before anything is restored, the files about to be replaced are copied to
# mine/catchup-backup-<date-time>/, so nothing you wrote is lost. It never
# touches .env, mine/ (apart from that backup), results/ (apart from adding a
# missing report for s6), or your edits to records.py.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLD=followon/old-modules
# DIR is the folder; NEEDS are other files it imports; TABLE=1 when it searches
# the Module 3 records table.
TABLE=0
case "${1:-}" in
  s2) DIR=02_data;  NEEDS="" ;;
  s3) DIR=03_lit;   NEEDS="" ;;
  s4) DIR=04_see;   NEEDS="" ;;
  s5) DIR=05_repair; NEEDS="" ;;
  s6) DIR=06_build; NEEDS="03_lit/pdfask.py 03_lit/lit.py" ;;
  m1) DIR=$OLD/01_tour;    NEEDS="" ;;
  m2) DIR=$OLD/02_prompts; NEEDS="" ;;
  m3) DIR=03_table;        NEEDS="" ;;
  m4) DIR=$OLD/04_tool;    NEEDS=""; TABLE=1 ;;
  m5) DIR=$OLD/05_agent;   NEEDS="$OLD/04_tool/tools.py"; TABLE=1 ;;
  m6) DIR=$OLD/06_project; NEEDS="$OLD/04_tool/tools.py $OLD/05_agent/tools.py"; TABLE=1 ;;
  *) echo "usage: bash catchup.sh s2|s3|s4|s5|s6   (the old modules: m1 to m6)"; exit 2 ;;
esac
cd "$ROOT"

mkdir -p mine
BACKUP="$(mktemp -d "mine/catchup-backup-$(date +%Y%m%d-%H%M%S)-XXXX")"   # unique, even twice in a second
for item in "$DIR" $NEEDS llm.py agent.py docs.py; do
  [ -e "$item" ] || continue
  mkdir -p "$BACKUP/$(dirname "$item")"
  cp -R "$item" "$BACKUP/$item"
done
echo "Your current files are copied to $BACKUP/ first."

# shellcheck disable=SC2086
# From HEAD, not the index, so an edit the agent staged with git add is undone too.
git checkout HEAD -- "$DIR" $NEEDS llm.py agent.py docs.py

# The table the old afternoon modules search. A row is usable when it has a
# doc_id and recorded no error (the same rule the Module 4 search uses). With no
# usable row, the saved table is copied in, and an unusable one is kept beside it.
if [ "$TABLE" = 1 ] && ! python3 - 03_table/records.jsonl <<'PYEOF' 2>/dev/null
import json, sys
for line in open(sys.argv[1]):
    try:
        row = json.loads(line)
    except ValueError:
        continue
    if isinstance(row, dict) and row.get("doc_id") and "error" not in row:
        sys.exit(0)
sys.exit(1)
PYEOF
then
  if [ -s 03_table/records.jsonl ]; then
    KEEP="03_table/records.unusable-$(date +%Y%m%d-%H%M%S)-$$.jsonl"
    mv 03_table/records.jsonl "$KEEP"
    echo "Your table had no usable rows; it is kept as $KEEP."
  fi
  cp corpus/records.jsonl 03_table/records.jsonl
  echo "Saved table copied to 03_table/records.jsonl."
fi

# Stop 6's page recipe builds from Stop 2's analysis: results/analysis.py, its
# report and its figures. With none yet, install an analysis that reruns the
# finished penguins one (06_build/page/from_reference.py) and run it once.
if [ "${1:-}" = s6 ] && [ ! -s results/analysis.py ]; then
  if [ -s results/report.md ]; then
    echo "results/report.md is there but results/analysis.py is not: finish Stop 2's prompt three (02_data/reproduce.md) first,"
    echo "or move results/report.md aside and run bash catchup.sh s6 again to use the finished penguins analysis."
  else
    mkdir -p results
    cp 06_build/page/from_reference.py results/analysis.py
    python3 results/analysis.py > results/analysis-output.txt 2>/dev/null || true
    echo "No Stop 2 analysis in results/ yet: results/analysis.py now reruns the finished penguins analysis,"
    echo "and its report, figures and printed output are in results/."
  fi
fi
echo "$DIR restored from the repository. Your .env, mine/ and records.py are untouched."
echo "Next: open $DIR/README.md."
