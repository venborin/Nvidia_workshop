"""Stop 6, page recipe: an analysis for anyone with no Stop 2 analysis of their own.

Copy this file to results/analysis.py (bash catchup.sh s6 also does, when
results/ has no Stop 2 report):

    cp 06_build/page/from_reference.py results/analysis.py

Then the page recipe runs exactly as for everyone else:

    python results/analysis.py > results/analysis-output.txt
    python 06_build/page/make_page.py --title "Palmer penguins"

It reruns one shipped dataset's finished analysis (02_data/datasets/<DATASET>/
reference/analysis.py), prints what that analysis prints, and copies its
report.md and figures into results/. Change DATASET to stillwater-weather or
oklahoma-wheat for another one: the figures an earlier run copied from a
different shipped dataset are removed first, so the page shows one dataset's
charts. Any other picture already in results/figures/ is left alone and named in
a warning, because make_page.py puts every picture in that folder on the page.
"""
import shutil
import subprocess
import sys
from pathlib import Path

DATASET = "penguins"


def labs_root():
    """The labs/ folder, wherever this file is run from (results/ or 06_build/page/)."""
    for folder in Path(__file__).resolve().parents:
        if (folder / "02_data" / "datasets").is_dir():
            return folder
    raise SystemExit("Could not find 02_data/datasets/ above this file.")


def main():
    root = labs_root()
    ref = root / "02_data" / "datasets" / DATASET / "reference"
    run = subprocess.run([sys.executable, str(ref / "analysis.py")], capture_output=True, text=True, cwd=root)
    sys.stdout.write(run.stdout)
    if run.returncode != 0:
        sys.stderr.write(run.stderr)
        raise SystemExit(f"{ref / 'analysis.py'} failed (exit {run.returncode}); nothing was copied.")
    results = root / "results"
    figures = results / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    # Take out what an earlier run copied from another shipped dataset.
    mine = {f.name for f in (ref / "figures").iterdir() if f.is_file()}
    shipped = {f.name for d in (root / "02_data" / "datasets").iterdir()
               if (d / "reference" / "figures").is_dir() for f in (d / "reference" / "figures").iterdir() if f.is_file()}
    for old in figures.iterdir():
        if old.is_file() and old.name in shipped - mine:
            old.unlink()
    shutil.copy2(ref / "report.md", results / "report.md")
    for fig in (ref / "figures").iterdir():
        if fig.is_file():
            shutil.copy2(fig, figures / fig.name)
    other = sorted(f.name for f in figures.iterdir() if f.is_file() and f.name not in mine)
    if other:
        print(f"(from_reference: results/figures/ also holds {', '.join(other)}, not from {DATASET}; "
              "make_page.py will put them on the page too, so move them out first if they do not belong)", file=sys.stderr)
    print(f"(from_reference: copied {DATASET}'s report and figures into results/)", file=sys.stderr)


if __name__ == "__main__":
    main()
