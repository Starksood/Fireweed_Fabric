#!/usr/bin/env python3
"""Cluster-robust re-analysis of the §8 fabrication effect (addresses Draft-V3 review point 1).

The pooled McNemar test in an earlier draft assumed independent pairs, but the 57 items are 5 readers ×
12 SHARED questions — clustered on both axes. This recomputes the effect with cluster-aware methods:
a reader-level sign test (assumption-light) and cluster bootstraps that resample questions (and questions
+ readers) rather than items. Writes abstention_cluster_stats.json. Reads only the judged rows.
"""
import json, random
from math import comb
from pathlib import Path

rows = json.load(open("adversarial_fabrication_sweep.judged.json"))["rows"]
readers = sorted({r['reader'] for r in rows})
qs = sorted({r['q'] for r in rows})
fab = lambda v: 1 if v == 'assert' else 0
valid = lambda r: r.get('rag_judged') in ('assert', 'decline')

per_reader = {}
for rd in readers:
    rr = [r for r in rows if r['reader'] == rd and valid(r)]
    rag = sum(fab(r['rag_judged']) for r in rr); fw = sum(fab(r['fw_judged']) for r in rr)
    per_reader[rd] = {"rag": rag, "fw": fw, "reduced": fw < rag}
n_red = sum(v['reduced'] for v in per_reader.values()); n_rd = len(readers)
sign_p = min(1.0, 2 * sum(comb(n_rd, i) for i in range(n_red, n_rd + 1)) / (2 ** n_rd))

by_q = {q: [r for r in rows if r['q'] == q and valid(r)] for q in qs}
rng = random.Random(0)
def boot(resample_readers):
    ds = []
    for _ in range(10000):
        sq = [rng.choice(qs) for _ in qs]
        sr = [rng.choice(readers) for _ in readers] if resample_readers else readers
        rag = fw = n = 0
        for q in sq:
            for r in by_q[q]:
                if r['reader'] in sr:
                    rag += fab(r['rag_judged']); fw += fab(r['fw_judged']); n += 1
        if n: ds.append((rag - fw) / n)
    ds.sort(); return [round(ds[250], 4), round(ds[9750], 4)]

out = {"per_reader": per_reader, "n_readers_reduced": f"{n_red}/{n_rd}",
       "reader_sign_test_p_two_sided": round(sign_p, 4),
       "question_cluster_bootstrap_reduction_ci95": boot(False),
       "twoway_cluster_bootstrap_reduction_ci95": boot(True),
       "note": "McNemar over pooled items assumes independence, VIOLATED (5 readers x 12 shared questions). "
               "Effect directional across all readers, modest, not significant under cluster resampling."}
Path("abstention_cluster_stats.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
