# Paper 1 — tables (auto-generated from committed bench artifacts)

*Regenerate with `python3 bench/make_paper_figures.py`. Every number traces to a source file stamped under its table. Do not hand-edit.*


### Table 1 — Write-side interchangeability (§4.1)
*source: `write_side_served_v3_results.json`*

| pair | axis | entity-J | domain-J | claim-semantic |
|---|---|---|---|---|
| gemma-1b vs gemma-4b | scale | 1.00 | 0.85 | 0.77 |
| gemma-1b vs qwen-4b | scale + family | 1.00 | 1.00 | 0.87 |
| gemma-4b vs qwen-4b | family | 1.00 | 0.85 | 0.83 |

*verdict:* ✓✓ STRONG (entity-J 1.00, domain-J 0.90, claim-lex 0.69)  ·  *competent perceivers:* gemma-1b, gemma-4b, qwen-4b

*Anchors (all sbert):* cross-persona floor 0.29 (accounts of different people) · determinism check 1.00 (temp-0 same-perceiver rerun — proves determinism, not an upper bound) · same-family temperature-0.7 ceiling 0.92 (gemma-1b vs gemma-4b under realistic sampling, MSC corpus — the non-hollow upper reference). The 0.77–0.87 cross-model band sits far above the different-person floor and close beneath the same-family ceiling.


### Table 2 — Third-party (LoCoMo) write-side replication (§4.1)
*source: `write_side_locomo_caroline_junkfilter_results.json (entity-J, post junk-filter) + write_side_locomo_caroline_results.json (pre-filter) + sbert_locomo_anchors_results.json`*

| pair | axis | entity-J | domain-J | claim-semantic (sbert) |
|---|---|---|---|---|
| gemma-1b vs gemma-4b | scale | 0.40 (0.31) | 0.71 | 0.73 |
| gemma-1b vs qwen-4b | scale + family | 0.67 (0.57) | 0.86 | 0.83 |
| gemma-4b vs qwen-4b | family | 0.50 (0.42) | 0.86 | 0.81 |

*Anchors (all sbert):* cross-person floor 0.36 (Caroline vs a different LoCoMo speaker, Jon) · same-perceiver ceiling 1.00. Cross-perceiver claim-semantic 0.79 sits +0.43 above the floor.

*Entity-J:* shown post junk-filter, pre-filter in parentheses. A deterministic filter (pinned word-frequency lexicon, Zipf ≥ 5.0, + contraction/pronoun exclusion — no model in the loop) raises mean entity-J 0.43 → 0.52; claim-semantic and domain-J are unchanged by the filter, so the residual gap is extraction noise (sub-Zipf common words; cross-perceiver nickname canonicalization), not account divergence.


### Table 3 — Read-side interchangeability (semantic on sbert, floor-controlled; §4.2)
*source: `sbert_unified_results.json (+ cross_model_* for surface/abstention)`*

| pair | axis | surface token-J | matched (sbert) | shuffled floor | perm p | abstain-agree |
|---|---|---|---|---|---|---|
| qwen-4b vs gemma-4b | family | 0.20 | 0.77 | 0.34 | <0.0005 | 0.94 |
| gemma-1b vs qwen-4b | scale + family | 0.18 | 0.69 | 0.33 | <0.0005 | 0.78 |

*Reading:* readers paraphrase (low surface token-Jaccard) but agree in meaning — matched sbert similarity sits well above the shuffled-pair topical floor (same answers, wrong query-pairing), so the agreement is query-specific. Same encoder as the write side, so §4.1 and §4.2 are on one scale. (An earlier draft used a different, higher-baseline embedder — see Appendix A.)


### Table 4 — Field-level interchangeability (self-shape; §4.3)
*source: `identity_field_results.json`*

| comparison | same centroid | mass ratio | dispersion Δ | concentration Δ |
|---|---|---|---|---|
| gemma-1b vs qwen-4b (cross-model) | ✓ | 0.53 | 0.11 | 0.15 |
| single vs mid-stream transplant | ✓ | 0.68 | 0.04 | 0.09 |


### Table 5 — Lesion: substrate vs naive-append across a perceiver swap (§5)
*source: `lesion_contrast_results.json`*

| cross-perceiver agreement | substrate | naive-append | Δ |
|---|---|---|---|
| entity-Jaccard | 0.78 | 0.10 | +0.68 |
| domain-Jaccard | 0.90 | 0.30 | +0.59 |
| claim-semantic | 0.88 | 0.89 | -0.01 |
| claim-lexical | 0.66 | 0.68 | -0.02 |

*models:* gemma-3-1b, gemma-3-4b, qwen3-4b  ·  *verdict:* ✓✓ SUBSTRATE PRESERVES, NAIVE DOES NOT — canonicalization/resolution is what carries the account across the swap

*Reading:* identical perception; only the deterministic consolidation is ablated. The naive store's **entity/domain structure collapses** across the swap (0.10/0.30) where the substrate canonicalizes to one set (0.78/0.90); raw claim similarity is tied — so what the substrate uniquely preserves is the canonical entity/domain structure, not the surface text.


### Table 6 — Perturbation battery (§6)
*source: `fork/merge/corrupt/hot_swap/longitudinal_substrate + write_side v3`*

| perturbation | thought experiment | key numbers |
|---|---|---|
| age (14 sessions) | gradual change | determinism 1.00, order-invariance 1.00; cross-model claim-sem 0.82, transplant 0.91 |
| fork | fission | continuity 0.67; divergence: real 0.82 vs null-fork 1.00; branch-specific True |
| merge | fusion | same-person dedup 0.64; different-person contamination 0.00, chimera 0 |
| corrupt | amnesia | recovery fraction 1.00, id-collisions 0; graceful to 50% deletion |
| hot-swap | live transplant | 18/18 pre-swap nodes carried (continuity 1.00); 31 added by new model |


### Table 7 — Structural abstention: pilot (§8)
*source: `adversarial_fabrication_sweep.judged.json + abstention_cluster_stats.json + judge_human_agreement_results.json`*

*Per-reader raw counts only — per-cell n=12 is too small for per-reader inference. The pooled pilot effect is directional but not significant (below); the load-bearing §8 evidence is the scaled run beneath this table.*

| reader | bare RAG fab | inside Fireweed fab |
|---|---|---|
| gemma-3-1b | 6/12 | 4/12 |
| gemma-3-4b | 4/12 | 3/12 |
| qwen3-1.7b | 4/12 | 1/12 |
| qwen3-4b | 1/12 | 0/12 |
| liquid/lfm2.5-1.2b | 3/12 | 1/12 |

**Directional, not significant.** Pooled bare RAG **18** vs Fireweed **9** confident false assertions; fabrication fell for **5/5** readers. But the 12 questions recur across readers, so the pooled McNemar (p=0.049) assumes independence it does not have. Cluster-robust: question-bootstrap 95% CI on the reduction **[-0.05, 0.38] (crosses zero)**; reader sign test two-sided **p = 0.0625**. §8 leans on provenance, not the rate.

*Judge validation (qwen/qwen3-4b-2507):* judge–human agreement 92%, Cohen's κ = 0.747 on an 24-item subset (single annotator).

**At scale (the load-bearing §8 result).** 1,200 adversarial items over 722 third-party MSC personas, answered by 2 readers spanning the pilot's capability range (gemma-3-1b, qwen3-4b) in both configurations — 2,400 answer opportunities per configuration. Inside Fireweed: **0** confident false assertions; bare RAG: **154**.

| reader | bare RAG fab (n=1200) | inside Fireweed fab (n=1200) |
|---|---|---|
| gemma-3-1b | 117 | 0 |
| qwen3-4b | 37 | 0 |

*Ensemble judge (3 local models, majority vote):* agreement 96%, Cohen's κ = 0.882 vs the human-labeled slice (n=24).
*source: `abstention_v21/abstention_v21_full.json` (raw judged rows) + `abstention_v21/abstention_v21_full_analysis.json` + `abstention_v21/ensemble_judge_validation.json`*


### Appendix B — Closing the loop (§9)
*source: `stage_4_3b_iter/union + stage_4_iter1_finetune + stage_4_iter2_* + stage_4_control2_base_gate`*

**Canonical 3B (Qwen2.5-3B QLoRA, iterative, epochs=8):**

| metric | base | + adapter |
|---|---|---|
| OOD valid-JSON | 1/12 | 12/12 |
| OOD claim-F1 | 0.00 | 0.90 |
| general canary hit-rate | 12/12 | 12/12 |
| general JSON-leak | 0/12 | 0/12 |

**0.5B pilot:** held-out loss 3.24 → 0.92; claim JSON 0/3 → 3/3.

**Sequencing control (0.5B, step-matched) — union ≥ iterative:**

| mode | OOD valid-JSON | OOD claim-F1 |
|---|---|---|
| union (train-once) | 12/12 | 1.00 |
| iterative | 10/12 | 0.83 |

**Perception-bootstrapping control:** base model self-harvest 0/12 kept (pass rate 0.00); the iterated adapter passes 12/12 (`maya_v16_sft_b2.gate_report.json`).
