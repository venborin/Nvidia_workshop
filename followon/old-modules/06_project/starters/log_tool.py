"""A parser for one potentiostat log layout. A tested starting point.

    python 06_project/starters/log_tool.py

What it accepts: a text log with one reading per line and five columns
separated by spaces, in this order:

    time  channel  potential_V  current_uA  flag
    00:02:30  CH1   0.050    40.98   sat

Lines starting with # are comments. Potential and current must be numbers.
The flag is "ok" or a short word such as "sat" (saturated: the reading hit
the top of the instrument's range) or "drift". A line in any other layout is
skipped and counted, never silently dropped. Your instrument's log will
probably differ: change the column order in the one marked line.
"""
import math
from pathlib import Path

LOG = Path(__file__).resolve().parent / "sample.log"       # or yours: Path(__file__).resolve().parents[4] / "mine" / "your_file.log"


def log_summary(channel: str) -> str:
    """Summarize the potentiostat log for one channel (CH1, CH2) or 'all'. Returns,
    per channel, the number of readings, the potential range in volts, the
    maximum current in microamps, and any rows flagged other than ok, plus a
    count of lines that were not in the expected layout."""
    if not LOG.exists():
        return f"error: no file at {LOG}"
    want = channel.strip().upper()
    per, skipped = {}, []
    for number, line in enumerate(LOG.read_text().splitlines(), start=1):
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        try:
            t, ch, v, i, flag = parts                  # the layout: change this line for yours
            v, i = float(v), float(i)
            if not (math.isfinite(v) and math.isfinite(i)):
                raise ValueError
        except ValueError:
            skipped.append(number)
            continue
        if want not in ("ALL", "", "*") and ch.upper() != want:
            continue
        d = per.setdefault(ch, {"n": 0, "v": [], "i": [], "flags": []})
        d["n"] += 1
        d["v"].append(v)
        d["i"].append(i)
        if flag != "ok":
            d["flags"].append(f"{t} {flag}")
    note = (f"\nnote: skipped {len(skipped)} line(s) not in the layout time channel potential current flag "
            f"(first: line {skipped[0]})") if skipped else ""
    if not per:
        return f"no channel named {channel!r} in the lines read{note}"
    return "\n".join(
        f"{ch}: {d['n']} readings; potential {min(d['v']):+.3f} to {max(d['v']):+.3f} V; "
        f"max current {max(d['i']):.2f} uA; flagged: {', '.join(d['flags']) or 'none'}"
        for ch, d in sorted(per.items())) + note


if __name__ == "__main__":
    print(log_summary("all"))
    print()
    print(log_summary("CH2"))
    print()
    print(log_summary("CH9"))
