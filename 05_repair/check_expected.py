"""Check analysis.py against the published species means.

Run from the labs/ folder:

    python 05_repair/check_expected.py

It runs analysis.py the way you would (from labs/), reads the table it prints,
and compares every number with the published value in EXPECTED.md. It prints
PASS or FAIL and exits 0 or 1. It never changes analysis.py.

To check a different script, give its path: python 05_repair/check_expected.py my_copy.py
"""
import math
import subprocess
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parent.parent
SCRIPT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else LABS / "05_repair" / "analysis.py"

# Published in the palmerpenguins README, "Examples" (see EXPECTED.md).
# Tolerance is half a unit in the last printed digit.
EXPECTED = {
    "Adelie":    {"n": 152, "bill_length_mm": 38.8, "bill_depth_mm": 18.3, "flipper_length_mm": 190, "body_mass_g": 3701},
    "Chinstrap": {"n": 68,  "bill_length_mm": 48.8, "bill_depth_mm": 18.4, "flipper_length_mm": 196, "body_mass_g": 3733},
    "Gentoo":    {"n": 124, "bill_length_mm": 47.5, "bill_depth_mm": 15.0, "flipper_length_mm": 217, "body_mass_g": 5076},
}
TOLERANCE = {"n": 0, "bill_length_mm": 0.05, "bill_depth_mm": 0.05, "flipper_length_mm": 0.5, "body_mass_g": 0.5}


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


def run():
    try:
        done = subprocess.run([sys.executable, str(SCRIPT)], cwd=LABS, capture_output=True,
                              text=True, timeout=120)
    except subprocess.TimeoutExpired:
        fail(f"{SCRIPT.name} did not finish within 120 seconds")
    if done.returncode != 0:
        lines = [l for l in done.stderr.strip().splitlines() if l.strip()]
        fail(f"{SCRIPT.name} did not run. Its last error line: {lines[-1] if lines else '(none)'}")
    return done.stdout


def parse(stdout):
    lines = stdout.splitlines()
    header = next((l.split() for l in lines if l.split()[:1] == ["species"]), None)
    if header is None or len(header) < 6:
        fail("the output format changed: expected a header line 'species n bill_length_mm ...' "
             "and then one line per species (EXPECTED.md says what the check reads)")
    repeated = sorted({h for h in header if header.count(h) > 1})
    if repeated:
        fail(f"the header names a column twice ({', '.join(repeated)}); each column must appear once")
    found = {}
    start = next(i for i, l in enumerate(lines) if l.split()[:1] == ["species"])
    for line in lines[start + 1:]:
        parts = line.split()
        if len(parts) != len(header):
            if parts and parts[0] in EXPECTED:
                fail(f"the row for {parts[0]} has {len(parts)} fields and the header has {len(header)}: {line.strip()}")
            continue
        name = parts[0]
        try:
            values = {h: float(v) for h, v in zip(header[1:], parts[1:])}
        except ValueError:
            if name in EXPECTED:
                fail(f"could not read the numbers in: {line.strip()}")
            continue                      # not a table row
        if name not in EXPECTED:
            fail(f"the table has a row for an unexpected species '{name}': {line.strip()}")
        if name in found:
            fail(f"the table has two rows for {name}; each species must appear once")
        bad = [h for h, v in values.items() if not math.isfinite(v)]
        if bad:
            fail(f"{name}: {', '.join(bad)} is not a finite number ({line.strip()})")
        found[name] = values
    if not found:
        fail("the output format changed: no line per species under the header "
             "(EXPECTED.md says what the check reads)")
    return found


def main():
    found = parse(run())
    problems, checked = [], 0
    for species, want in EXPECTED.items():
        got = found.get(species)
        if got is None:
            problems.append(f"{species}: no row in the output")
            continue
        for column, value in want.items():
            if column not in got:
                problems.append(f"{species}: no column {column}")
                continue
            checked += 1
            if abs(got[column] - value) > TOLERANCE[column]:
                problems.append(f"{species} {column}: got {got[column]:g}, published {value:g} (tolerance {TOLERANCE[column]:g})")
    if problems:
        print("\n".join(problems))
        fail(f"{len(problems)} value(s) do not match the published table")
    print(f"PASS: all {checked} values match the published table")


if __name__ == "__main__":
    main()
