# Fireweed — paper verification bundle

Independent verification for the paper **"A Model-Independent Memory Substrate: Preserving an Agent's
Account of a User Across LLM Swaps, Scales, and Families."**

The paper's thesis is a systems claim: a **deterministic memory substrate**, not the language model,
is the durable object — so when you swap the model, the system's *account of a user* survives. This
repo lets you check that the numbers behind that claim are real, from committed benchmark outputs,
**without** the Fireweed implementation, LM Studio, a GPU, or (after one model download) a network.

> **Scope, stated up front.** *Perception* — running the perceiver/reader models over raw turns to
> produce the JSON outputs — requires the closed implementation and local model serving and is **not**
> reproducible here. What **is** fully reproducible is every *statistic over the already-captured
> outputs*: the floors, the ceiling, the null controls, the cluster-robust tests, the lesion, and all
> tables — recomputed on one public sentence encoder (`sentence-transformers/all-MiniLM-L6-v2`). The
> implementation (`src/fireweed/**`) is deliberately not included; see [MANIFEST.md](MANIFEST.md).

## Quickstart

```bash
pip install -r requirements.txt     # sentence-transformers, numpy, pytest (CPU torch pulled in transitively)
python reproduce.py                 # recompute all tables from committed JSON; diff vs papers/paper1_tables.md
pytest -q                           # assert each paper number with tolerances
```

`reproduce.py` prints **PASS** when the regenerated `papers/paper1_tables.md` is byte-identical to the
committed copy. `pytest` is the authoritative per-claim gate (tolerances absorb tiny float drift across
sentence-transformers/torch builds). The first run downloads the ~80 MB sbert model from Hugging Face
and caches it; every run after that is offline.

## What each paper claim rests on

Every number traces to a committed JSON; the recompute script turns raw outputs into the reported
statistic. (Similarities are all on one encoder so read- and write-side numbers are comparable.)

| Paper claim | Number | Artifact | Recompute |
|---|---|---|---|
| **§4.1 Write-side interchangeability** — different perceivers, same account | claim-semantic **0.77–0.87** vs **0.29** cross-persona floor; same-family temp-0.7 ceiling **0.92** (determinism check 1.00) | `write_side_served_v3_results.audit.json`, `write_side_{theo,priya,marcus}_results.audit.json`, `msc_true_ceiling_gemma_results.json` | `sbert_unify.py` → `sbert_unified_results.json` |
| **§4.1 Third-party replication (LoCoMo)** — the external-validity check | semantic **0.79**, **+0.43** over a **0.36** cross-person floor; entity-J degrades to **0.43**, deterministic junk filter recovers **0.52** | `write_side_locomo_{caroline,jon}_results*.json`, `write_side_locomo_caroline_junkfilter_results.json` | `sbert_locomo_anchors.py` → `sbert_locomo_anchors_results.json` |
| **§4.2 Read-side interchangeability** — readers paraphrase but agree in meaning | matched **0.69–0.77** vs shuffled-pair floor **~0.33**, permutation **p < 0.001** | `cross_model_interchangeability_results.json`, `cross_model_gemma1b_qwen4b.json` | `sbert_unify.py` |
| **§5 Lesion (non-substrate control)** — structure comes from consolidation | entity-J **0.78 → 0.10** (gap +0.68); claim-semantic **tied ~0.88** | `lesion_contrast_results.json` (+ `.audit.json`) | read directly |
| **§6 Perturbation battery** — null controls | null-fork agreement **1.0**; cross-person merge contamination **0.0**; corruption recovery fraction **1.0** | `fork_divergence_results.json`, `merge_identity_results.json`, `corrupt_resilience_results.json` | read directly |
| **§8 Structural abstention — pilot** (honest demotion) | pooled RAG **18** vs Fireweed **9** (5/5 readers reduce), but cluster-robust CI **[-0.05, 0.38] crosses zero**, sign test **p≈0.06** | `adversarial_fabrication_sweep.judged.json` | `abstention_cluster_stats.py` → `abstention_cluster_stats.json` |
| **§8 Structural abstention — at scale** (the load-bearing result) | **0 vs 154** confident false assertions over **1,200** items / **722** MSC personas / 2 readers (2,400 opportunities per config); both readers → 0 | `abstention_v21/abstention_v21_full.json` (raw judged rows) | recounted by `tests/test_paper_claims.py::test_abstention_scaled_zero_vs_154` |
| **§8 Scaled-run judge validation** | ensemble (3 models) Cohen's **κ = 0.882**, agreement **96%** | `abstention_v21/ensemble_judge_validation.json` | read directly |
| **§8 Judge validation** | Cohen's **κ ≈ 0.75**, agreement **92%** | `adversarial_fabrication_sweep.judged.json` + inlined author labels | `judge_human_agreement.py` |
| **§9 Closed loop** (supporting) | OOD valid-JSON **1/12 → 12/12**, claim-F1 **0.00 → 0.90** | `stage_4_3b_iter_results.json` | read directly |
| **§11 LongMemEval (n=50)** — parity + latency | accuracy **0.42 vs 0.48** (inside binomial noise), mean latency **6.7s vs 16.5s** (~2.5×), max **13.9s vs 241s** | `tests/evaluations/results_longmemeval_50.json` | read directly |

`pytest` asserts each of these (see [tests/test_paper_claims.py](tests/test_paper_claims.py)). Where a
claim is an *honest limitation* — LoCoMo entity-J degrading, the abstention effect not surviving
clustering — the test asserts the *limitation*, so it can't silently drift into an overclaim.

## How the raw outputs were produced (method, not runnable here)

The committed JSONs come from the closed Fireweed pipeline. For provenance, the method:

- **Perception (write side).** Each raw turn is passed to a perceiver LLM (gemma-3-1b, gemma-3-4b,
  qwen3-4b-2507 via a local server) under the production prompt; the model *proposes* structured
  claims, and deterministic code *decides* what commits (a verbatim-evidence guard, an entity linker,
  and a resolver). Swapping only the perceiver and comparing the resulting substrates is the write-side
  interchangeability test. The persisted claim/entity/domain lists are in the `*_results.audit.json`
  files here — enough to recompute all agreement metrics.
- **Reading (read side).** A fixed snapshot is queried; different reader LLMs answer the same probes.
  The per-query answers are persisted in `cross_model_*` and re-embedded here.
- **Lesion.** Perception is held identical across three perceivers while only the deterministic
  consolidation is ablated (substrate vs naive-append store) — isolating what the substrate contributes.
- **Perturbation battery.** Fork / merge / corrupt / hot-swap / longitudinal experiments, each paired
  with a null control (e.g. a fork with no divergent experience must agree ~1.0).
- **Abstention & loop.** An adversarial distractor set is answered by bare RAG vs the Fireweed pipeline
  with the same reader models, judged by an LLM validated against a human annotator; the closed-loop
  numbers are from a QLoRA adapter over a frozen base.

The scripts that drive these models (`run_write_side_interchangeability.py`, `run_lesion_contrast.py`,
`run_adversarial_fabrication.py`, …) `import fireweed` and are **not** shipped — they are not needed to
verify the statistics, which is the point of this bundle.

## Layout

```
reproduce.py                 one-command recompute + table diff
tests/test_paper_claims.py   pytest: assert each paper number (tolerances)
MANIFEST.md                  full include/exclude list + provenance
papers/paper1_tables.md      the tables the paper cites (numbers of record)
fireweed-v16/bench/          recompute scripts (*.py) + raw/result outputs (*.json)
fireweed-v16/data/           fixtures: maya traces, longitudinal probes, LoCoMo corpora
```

The `fireweed-v16/bench/` path mirrors the research repo so the recompute scripts run byte-identical to
the ones that produced the paper — verify with a diff against any released source.

## License

MIT for the evaluation/recompute code (see [LICENSE](LICENSE)). Benchmark outputs and fixtures are
released for verification; third-party datasets retain their own licenses — in particular the LoCoMo
corpora under `fireweed-v16/data/locomo/` derive from **LoCoMo** (Maharana et al., ACL 2024) and are
subject to that dataset's terms.
