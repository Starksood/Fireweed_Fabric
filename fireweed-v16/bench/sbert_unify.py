#!/usr/bin/env python3
"""Re-score read-side AND write-side claim/answer similarity on ONE embedder (sbert, all-MiniLM-L6-v2),
so §4.1 and §4.2 are on a single scale (addresses Draft-V3 review point 2). Recomputes: read-side
matched/shuffled-floor/permutation-p over the persisted per-query answers; write-side pairwise
claim-semantic and the cross-persona floor from the audit claim lists. Writes sbert_unified_results.json.
"""
import os; os.environ.setdefault("TORCHDYNAMO_DISABLE","1")
import json, random, statistics, itertools
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
st=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
cache={}
def emb(t):
    if t not in cache: cache[t]=st.encode(t, normalize_embeddings=True)
    return cache[t]
def cos(a,b):
    if not a or not b: return 0.0
    return float(np.dot(emb(a),emb(b)))
def align(A,B):
    if not A and not B: return 1.0
    if not A or not B: return 0.0
    ow=lambda xs,ys: statistics.mean(max(cos(x,y) for y in ys) for x in xs)
    return (ow(A,B)+ow(B,A))/2

# ---- READ side (sbert) matched / shuffled floor / permutation ----
def read_pair(cmf, trials=2000, seed=1):
    d=json.loads(Path(cmf).read_text())
    ps=[p for p in d['per_query'] if not p.get('a_abstained') and not p.get('b_abstained')]
    A=[p['a_answer'] for p in ps]; B=[p['b_answer'] for p in ps]; n=len(ps)
    matched=statistics.mean(cos(A[i],B[i]) for i in range(n))
    rng=random.Random(seed); shuf=[]; ge=0
    for _ in range(trials):
        pm=list(range(n)); rng.shuffle(pm)
        if any(pm[i]==i for i in range(n)): pm=pm[1:]+pm[:1]
        m=statistics.mean(cos(A[i],B[pm[i]]) for i in range(n)); shuf.append(m)
        if m>=matched: ge+=1
    return {"model_a":d['model_a'],"model_b":d['model_b'],"n_pairs":n,
            "matched":round(matched,4),"floor":round(statistics.mean(shuf),4),
            "perm_p":round((ge+1)/(trials+1),4),"trials":trials}
read=[read_pair("cross_model_interchangeability_results.json"), read_pair("cross_model_gemma1b_qwen4b.json")]

# ---- WRITE side (sbert): pairwise claim-sem + cross-persona floor ----
def claims(aud):
    d=json.loads(Path(aud).read_text())
    for k,v in d.items():
        if k!='_gold' and v.get('claims'): return v['claims']
    return []
v3=json.loads(Path("write_side_served_v3_results.audit.json").read_text())
persA={k:v['claims'] for k,v in v3.items() if k!='_gold' and v.get('claims')}
pw=[]
for a,b in itertools.combinations(list(persA),2):
    pw.append({"pair":f"{a} vs {b}","claim_semantic_sbert":round(align(persA[a],persA[b]),4)})
personas={'maya':'write_side_served_v3_results.audit.json','theo':'write_side_theo_results.audit.json',
          'priya':'write_side_priya_results.audit.json','marcus':'write_side_marcus_results.audit.json'}
cl={p:claims(f) for p,f in personas.items() if Path(f).exists()}
cross=[align(cl[a],cl[b]) for a,b in itertools.combinations(cl,2)]

out={"embedder":"sentence-transformers/all-MiniLM-L6-v2",
     "read_side":read,
     "write_side_pairwise_sbert":pw,
     "write_cross_persona_floor_sbert":round(statistics.mean(cross),4),
     "write_same_perceiver_ceiling":1.0,
     "note":"All claim-semantic re-scored on ONE embedder (sbert) so read and write are on one scale."}
json.dump(out, open("sbert_unified_results.json","w"), indent=2)
print(json.dumps(out,indent=2))
