"""A reader for FASTA files of DNA. A tested starting point: run it, then change it.

    python 06_project/starters/fasta_tool.py

What it accepts: plain FASTA, DNA only. Each record starts with a header line
">id optional description", followed by one or more sequence lines using
A, C, G, T and N (N is an unknown base). Anything else, such as protein
sequences or other ambiguity letters, gets an error message, not a guess.
GC content is (G + C) / (A + C + G + T), so N bases do not count either way.
"""
from pathlib import Path

FASTA = Path(__file__).resolve().parent / "sample.fasta"     # or yours: Path(__file__).resolve().parents[4] / "mine" / "your_file.fasta"
DNA = set("ACGTN")


def read_fasta():
    """[(id, description, sequence)], or an error string."""
    if not FASTA.exists():
        return f"error: no file at {FASTA}"
    records, header, seq = [], None, []
    for number, line in enumerate(FASTA.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(seq)))
            header, seq = line[1:].strip(), []
            if not header:
                return f"error: the header on line {number} has no id after '>'"
        elif header is None:
            return f"error: line {number} comes before any '>' header; this does not look like FASTA"
        else:
            seq.append(line.upper())
    if header is not None:
        records.append((header, "".join(seq)))
    if not records:
        return "error: no '>' header lines; this does not look like FASTA"
    out = []
    for header, s in records:
        sid, _, desc = header.partition(" ")
        bad = sorted(set(s) - DNA)
        if bad:
            return (f"error: sequence {sid} contains {''.join(bad[:5])!r}; this reader handles DNA "
                    "(A, C, G, T, N) only")
        out.append((sid, desc.strip(), s))
    return out


def describe_sequences(name: str) -> str:
    """Describe the DNA sequences in the FASTA file: for the named sequence id, or for
    every sequence when the argument is 'all'. Returns one line per sequence with
    its id, description, length in bases and GC content as a percentage of the
    A, C, G and T bases (unknown N bases are counted in the length, not in GC)."""
    want = name.strip()
    records = read_fasta()
    if isinstance(records, str):
        return records
    out = []
    for sid, desc, s in records:
        if want not in ("all", "", "*") and sid != want:
            continue
        acgt = sum(s.count(b) for b in "ACGT")
        gc = f"GC {100 * (s.count('G') + s.count('C')) / acgt:.1f}%" if acgt else "GC not defined (no A, C, G or T)"
        n_note = f", {s.count('N')} N" if "N" in s else ""
        out.append(f"{sid}: {desc or 'no description'}; {len(s)} bases{n_note}; {gc}")
    return "\n".join(out) or f"no sequence named {name!r}; ids are {', '.join(r[0] for r in records)}"


if __name__ == "__main__":
    print(describe_sequences("all"))
    print()
    print(describe_sequences("seq_B7"))
    print()
    print(describe_sequences("nope"))
