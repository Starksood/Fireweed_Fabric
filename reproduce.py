#!/usr/bin/env python3
"""One-command reproduction driver for the Fireweed paper verification bundle.

Runs the offline recompute scripts (sbert for every embedding; no LM Studio, no GPU, no
`fireweed` import) over the committed raw benchmark outputs, then regenerates the paper's
tables and diffs them against the committed `papers/paper1_tables.md` (the numbers of record).

    python reproduce.py

The recompute scripts are copied byte-for-byte from the research repo that produced the paper
(`fireweed-v16/bench/`), so a reviewer can diff them against any released source and confirm no
tampering. They read/write relative to `fireweed-v16/bench/`, so we run each with that as cwd.

Order matters: sbert_unify and sbert_locomo_anchors regenerate the JSONs that make_paper_figures
consumes, so make_paper_figures runs last.

Exit code 0 = regenerated tables are byte-identical to the committed reference. Non-zero = a diff
(inspect it; small 2-decimal float drift across sentence-transformers versions is possible — the
authoritative, tolerance-based gate is `pytest`).
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BENCH = ROOT / "fireweed-v16" / "bench"
TABLES = ROOT / "papers" / "paper1_tables.md"

# Recompute order: producers of intermediate JSONs first, table-builder last.
STEPS = [
    "sbert_unify.py",              # -> sbert_unified_results.json (read+write claim-sem on one encoder)
    "sbert_locomo_anchors.py",     # -> sbert_locomo_anchors_results.json (LoCoMo floor/ceiling)
    "abstention_cluster_stats.py", # -> abstention_cluster_stats.json (cluster-robust §8)
    "judge_human_agreement.py",    # -> judge_human_agreement_results.json (judge–human kappa)
    "make_paper_figures.py",       # -> papers/paper1_tables.md (all tables, last)
]


def run(script: str) -> None:
    print(f"\n=== {script} ===", flush=True)
    res = subprocess.run([sys.executable, script], cwd=str(BENCH))
    if res.returncode != 0:
        print(f"\n✗ {script} failed (exit {res.returncode})")
        sys.exit(2)


def main() -> int:
    if not TABLES.exists():
        print(f"✗ missing reference {TABLES}")
        return 2
    reference = TABLES.read_text(encoding="utf-8")  # committed numbers of record

    for s in STEPS:
        run(s)

    regenerated = TABLES.read_text(encoding="utf-8")  # make_paper_figures just overwrote it
    print("\n" + "=" * 70)
    if regenerated == reference:
        print("✓ PASS — regenerated papers/paper1_tables.md is byte-identical to the committed reference.")
        print("  Every table number traces to a committed JSON. Run `pytest` for the tolerance-based")
        print("  per-claim assertions.")
        # restore the committed bytes verbatim (they are identical; keeps git clean)
        TABLES.write_text(reference, encoding="utf-8")
        return 0

    print("✗ DIFF — regenerated tables differ from the committed reference:")
    import difflib
    diff = difflib.unified_diff(reference.splitlines(), regenerated.splitlines(),
                                fromfile="committed", tofile="regenerated", lineterm="")
    for line in diff:
        print("  " + line)
    print("\nSmall 2-decimal drift can come from a different sentence-transformers/torch build.")
    print("The authoritative check is `pytest` (tolerance-based). Restoring committed reference.")
    TABLES.write_text(reference, encoding="utf-8")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
