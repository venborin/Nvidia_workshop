#!/usr/bin/env bash
# Pack results/ into one zip to take home. results/ is never committed, so this
# is how today's figures, reports, tables and scripts leave the Codespace.
#
#   bash export.sh
#
# Then, in the file tree at the left, right-click the zip and choose Download.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
[ -d results ] && [ -n "$(ls -A results 2>/dev/null | grep -vx README.md)" ] || { echo "results/ is empty: nothing to pack yet."; exit 1; }
OUT="results-$(date +%Y-%m-%d-%H%M).zip"
python3 - "$OUT" <<'PY'
import sys, zipfile, pathlib
out = sys.argv[1]; n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(pathlib.Path("results").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            z.write(p); n += 1
print(f"{n} files")
PY
echo "Packed results/ into $OUT ($(du -h "$OUT" | cut -f1))."
echo "To download it: in the file tree at the left, right-click $OUT and choose Download."
echo "The zip is ignored by git too; delete it when it is safely on your laptop."
