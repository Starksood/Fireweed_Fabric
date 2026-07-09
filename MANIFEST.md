# Verification bundle — manifest

This repository lets a researcher independently verify every load-bearing number in the paper
*"A Model-Independent Memory Substrate: Preserving an Agent's Account of a User Across LLM Swaps,
Scales, and Families"* **without** the Fireweed implementation, LM Studio, a GPU, or a network
(after the one-time sbert model download). It ships the committed raw benchmark outputs, the
recompute scripts, and a test suite that asserts the paper's numbers.

**What can and cannot be reproduced here.** *Perception* — running the perceiver/reader models over
raw turns to produce the JSON outputs — needs the closed implementation and local model serving, and
is **not** reproducible from this bundle. The *statistics over the already-captured outputs* — every
floor, ceiling, null control, cluster-robust test, the lesion, and all tables — **are** fully
recomputable here from committed data on one public encoder (sbert `all-MiniLM-L6-v2`).

Paths below are repo-relative.

## Recompute scripts — `fireweed-v16/bench/*.py`
Copied byte-for-byte from the research repo that produced the paper (diff them against any released
source to confirm no tampering). None import `fireweed`; none touch a network.
- `sbert_unify.py` — re-scores read- and write-side claim/answer similarity + floors on one encoder
  (sbert) → `sbert_unified_results.json`. The §4.1/§4.2 numbers, one scale.
- `sbert_locomo_anchors.py` — LoCoMo third-party replication: cross-perceiver claim-semantic +
  cross-person floor + ceiling → `sbert_locomo_anchors_results.json` (§4.1 / Table 2).
- `abstention_cluster_stats.py` — cluster-robust §8 re-analysis (reader sign test + question / two-way
  cluster bootstraps) → `abstention_cluster_stats.json`. The load-bearing §8 statistic.
- `judge_human_agreement.py` — judge–human agreement + Cohen's κ from the judged rows + the author's
  pre-defined labels (labels inlined for auditability) → `judge_human_agreement_results.json`.
- `make_paper_figures.py` — regenerates all tables from the JSONs → `papers/paper1_tables.md`.

## Raw + result artifacts — `fireweed-v16/bench/*.json`
Read-side (per-query model answers persisted): `cross_model_interchangeability_results.json`,
`cross_model_gemma1b_qwen4b.json`, `semantic_read_floor_results.json`,
`semantic_read_floor_gemma1b_qwen4b.json`, `read_side_permutation.json`.
Write-side + field + anchors: `write_side_served_v3_results.json` (+ `.audit.json`),
`write_side_{theo,priya,marcus}_results.audit.json` (cross-persona floor inputs),
`write_side_anchors.json`, `write_side_ceiling_results.json`, `identity_field_results.json`,
`sbert_unified_results.json`.
Third-party (LoCoMo): `write_side_locomo_caroline_results.json` (+ `.audit.json`),
`write_side_locomo_jon_results.json` (+ `.audit.json`),
`write_side_locomo_caroline_junkfilter_results.json` (+ `.audit.json` — post-junk-filter entity-J,
Table 2), `sbert_locomo_anchors_results.json`.
True ceiling (§4.1): `msc_true_ceiling_gemma_results.json` (+ `.audit.json`) — same-family pair
(gemma-1b vs gemma-4b) under temperature-0.7 sampling on an MSC-derived corpus; the non-hollow
upper reference (claim-semantic 0.92).
Perturbation battery (with null controls): `fork_divergence_results.json`,
`merge_identity_results.json`, `corrupt_resilience_results.json`, `hot_swap_demo_results.json`,
`longitudinal_substrate_results.json`.
Lesion (G3 anchor): `lesion_contrast_results.json` (+ `.audit.json` — the actual entity sets).
Structural abstention (§8) — pilot, incl. judged prose: `adversarial_fabrication_sweep.judged.json`
(rows carry `rag_prose`/`fw_prose` + judge labels), `abstention_stats.json`,
`abstention_cluster_stats.json`, `judge_human_agreement_results.json`.
Structural abstention (§8) — scaled run (the load-bearing result): `abstention_v21/` —
`abstention_v21_full.json` (all 2,400 judged rows: question, trap category, both systems' prose,
per-judge votes, final labels — recount 0 vs 154 directly), `abstention_v21_full_analysis.json`
(summary), `ensemble_judge_validation.json` (3-model ensemble vs human slice, κ = 0.882),
`adversarial_suite.jsonl` (the 1,200 generated items over 722 MSC personas).
External validity (§11): `fireweed-v16/tests/evaluations/results_longmemeval_50.json` — the
50-episode LongMemEval Engine-vs-RAG run (accuracy parity, ~2.5× lower latency).
Closed loop (§9): `stage_4_3b_iter_results.json`, `stage_4_3b_union_results.json`,
`stage_4_iter1_finetune_results.json`, `stage_4_iter2_{union,iterative}.json`,
`stage_4_control2_base_gate.json`.

## Fixtures / corpora — `fireweed-v16/data/`
- `traces/maya_v16*.jsonl` (raw turns + SFT sources), `traces/maya_v16_sft_b2.gate_report.json`.
- `longitudinal/{marcus,priya,theo}_probes.json`.
- `locomo/{conv26_caroline,conv30_jon}.jsonl` — the LoCoMo-derived focal + floor corpora (see LICENSE).
- `bench/significance_extraction.snapshot.json` — the fixed graph used by the adversarial + lesion reads.

## Numbers of record — `papers/paper1_tables.md`
The committed tables the paper cites. `python reproduce.py` regenerates this file and diffs it against
the committed copy.

## Integrity — `SHA256SUMS.txt`
SHA-256 digests for every artifact, script, and document in the bundle (the paper's Availability
section points here). Verify with:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

## Deliberately NOT included (the moat)
- `src/fireweed/**` — the substrate implementation (firewall, entity linker, resolver, pipeline,
  reader, significance/field/consolidation, decay, constitution).
- The model-running harness scripts that `import fireweed` (e.g. `run_write_side_interchangeability.py`,
  `run_lesion_contrast.py`, `run_adversarial_fabrication.py`) — described as method in the README, but
  not runnable without the implementation and not required to verify the statistics.
- The nomic/LM-Studio-dependent recompute scripts (`semantic_read_floor.py`, `semantic_rescore.py`,
  `compute_review_anchors.py`) — superseded for the paper's numbers by the sbert scripts above, and
  excluded so the bundle runs fully offline. `sbert_unify.py` covers the read-side floor on sbert.
- Model weights / LoRA adapters. (The final paper itself IS included, as `Fireweed_fabric_paper.pdf` at the repo root.)
