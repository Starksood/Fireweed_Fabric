#!/usr/bin/env python3
"""Floor + ceiling anchors for the LoCoMo write-side interchangeability run, on ONE embedder
(sbert all-MiniLM-L6-v2 -- the same scale as sbert_unify.py so LoCoMo numbers are directly
comparable to the synthetic-persona headline).

Mirrors sbert_unify.py's write-side block but for the third-party LoCoMo corpus:

  * cross-perceiver claim-semantic: same person (Caroline), different perceiver models -> how
    much the substrate agrees when only the perceiver changes. This is the interchangeability
    signal (want: high).
  * cross-PERSON floor: Caroline's substrate vs a DIFFERENT LoCoMo speaker's (Jon's), holding
    the perceiver fixed -> how similar two different people's accounts look by chance/topic
    overlap. This is the discriminating floor (want: interchangeability >> floor).
  * same-perceiver ceiling: 1.0 by construction (deterministic temp-0 re-perception of the
    identical corpus through the identical model reproduces the identical claim list).

Run AFTER both LoCoMo harness runs exist:
  bench/write_side_locomo_caroline_results.audit.json
  bench/write_side_locomo_jon_results.audit.json
"""
import os
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
os.environ.setdefault("TORCH_COMPILE_DEBUG_DIR", "/tmp/torch_compile_debug")
import json
import statistics
import itertools
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

HERE = Path(__file__).parent
st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
cache = {}


def emb(t):
    if t not in cache:
        cache[t] = st.encode(t, normalize_embeddings=True)
    return cache[t]


def cos(a, b):
    return 0.0 if not a or not b else float(np.dot(emb(a), emb(b)))


def align(A, B):
    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0
    ow = lambda xs, ys: statistics.mean(max(cos(x, y) for y in ys) for x in xs)
    return (ow(A, B) + ow(B, A)) / 2


def perceiver_claims(audit_path: Path) -> dict[str, list[str]]:
    d = json.loads(audit_path.read_text())
    return {k: v["claims"] for k, v in d.items() if k != "_gold" and v.get("claims")}


car = perceiver_claims(HERE / "write_side_locomo_caroline_results.audit.json")
jon = perceiver_claims(HERE / "write_side_locomo_jon_results.audit.json")

# cross-perceiver (same person, Caroline) claim-semantic on sbert
cross_perceiver = []
for a, b in itertools.combinations(list(car), 2):
    cross_perceiver.append({"pair": f"{a} vs {b}", "claim_semantic_sbert": round(align(car[a], car[b]), 4)})
cp_mean = round(statistics.mean(p["claim_semantic_sbert"] for p in cross_perceiver), 4)

# cross-PERSON floor: Caroline vs Jon, PER perceiver (perceiver held fixed -> isolates person)
shared_models = [m for m in car if m in jon]
floor_per_model = []
for m in shared_models:
    floor_per_model.append({"perceiver": m, "claim_semantic_sbert": round(align(car[m], jon[m]), 4)})
floor_mean = round(statistics.mean(p["claim_semantic_sbert"] for p in floor_per_model), 4)

out = {
    "embedder": "sentence-transformers/all-MiniLM-L6-v2",
    "corpus": "LoCoMo (Maharana et al.) — conv-26 Caroline (focal) vs conv-30 Jon (floor)",
    "cross_perceiver_same_person_sbert": {
        "note": "Caroline's account through 3 perceivers — the interchangeability signal.",
        "pairwise": cross_perceiver,
        "mean": cp_mean,
    },
    "cross_person_floor_sbert": {
        "note": "Caroline vs Jon, perceiver held fixed — discriminating floor.",
        "per_perceiver": floor_per_model,
        "mean": floor_mean,
    },
    "same_perceiver_ceiling": 1.0,
    "margin_over_floor": round(cp_mean - floor_mean, 4),
    "synthetic_reference": {
        "note": "sbert_unify.py write-side headline for comparison",
        "cross_perceiver_claim_semantic": "0.77-0.87",
        "cross_persona_floor": 0.29,
    },
}
(HERE / "sbert_locomo_anchors_results.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
