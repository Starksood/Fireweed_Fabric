# Fireweed

> 🛑 **Retraction (2026-08-22).** The scaled abstention result — *"0 vs 154"* — is **withdrawn**: it measured an empty substrate. See [`RETRACTION.md`](RETRACTION.md), which includes a command you can run against this repository to confirm it. The §6.5 pilot result and every other measurement here are unaffected.

**A deterministic, model-independent memory substrate for LLM agents.** The memory is the durable
object; the model is a transient, swappable tenant. The model proposes, deterministic code decides —
so a committed fact traces to the source span it came from, and retrieval abstains instead of
answering from evidence it does not have.

*Stated precisely, because the looser version was wrong:* on the **document** path a claim may not
assert more than its cited span, and that is enforced and tested. The **conversational** path
resolves subjects from context and rewords by design, and does not carry that guarantee.

There are two things in this repo, for two different readers:

| I want to… | Go to |
|---|---|
| **Build with Fireweed** — durable agent memory over HTTP | [`fireweed-client/`](fireweed-client/) — the Python SDK + a runnable demo |
| **Check the research** — reproduce the paper's numbers | [Verify the paper's numbers](#verify-the-papers-numbers), below |

## Build with Fireweed

```python
from fireweed_client import FireweedClient

with FireweedClient(api_key="YOUR_KEY", base_url="https://your-fireweed-host") as fw:
    maya = fw.session("user-42", speaker="Maya")
    maya.commit("I moved to Portland last spring.")
    ans = maya.read("Where does Maya live?")
    print(ans["answer"], "→ grounded in", ans["provenance_node_ids"])
```

The SDK is a **thin HTTP client with zero memory logic** — the substrate, resolver, and firewall run
server-side. See [`fireweed-client/README.md`](fireweed-client/README.md) for the full API, the
model hot-swap story (same memory, different vendor, identical provenance), and a Streamlit demo.

> **Status — read before you `pip install`.** The client talks to a Fireweed backend, and **there is
> no public hosted endpoint yet**; the engine is not open source, so you cannot self-host it either.
> Today the SDK is usable if you have been given a key and a host (design partners), or you are
> running the backend yourself. If you want access, open an issue. We would rather say this plainly
> than ship a package that 404s against every URL you try.

## Verify the paper's numbers

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21278302.svg)](https://doi.org/10.5281/zenodo.21278301)

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

### Quickstart

```bash
pip install -r requirements.txt     # sentence-transformers, numpy, pytest (CPU torch pulled in transitively)
python reproduce.py                 # recompute all tables from committed JSON; diff vs papers/paper1_tables.md
pytest -q                           # assert each paper number with tolerances
```

`reproduce.py` prints **PASS** when the regenerated `papers/paper1_tables.md` is byte-identical to the
committed copy. `pytest` is the authoritative per-claim gate (tolerances absorb tiny float drift across
sentence-transformers/torch builds). The first run downloads the ~80 MB sbert model from Hugging Face
and caches it; every run after that is offline.

### What each paper claim rests on

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
| ~~**§8 Structural abstention — at scale**~~ | 🛑 **RETRACTED 2026-08-22 — measured an empty substrate.** All 2,400 rows carry one identical abstention string; the Fireweed arm was absent, not sound. RAG's 154 stands as a measurement of RAG. | [`RETRACTION.md`](RETRACTION.md) — includes a reproduction you can run on this repo | test disabled pending a valid re-run |
| **§8 Scaled-run judge validation** | ensemble (3 models) Cohen's **κ = 0.882**, agreement **96%** | `abstention_v21/ensemble_judge_validation.json` | read directly |
| **§8 Judge validation** | Cohen's **κ ≈ 0.75**, agreement **92%** | `adversarial_fabrication_sweep.judged.json` + inlined author labels | `judge_human_agreement.py` |
| **§9 Closed loop** (supporting) | OOD valid-JSON **1/12 → 12/12**, claim-F1 **0.00 → 0.90** | `stage_4_3b_iter_results.json` | read directly |
| **§11 LongMemEval (n=50)** — parity + latency | accuracy **0.42 vs 0.48** (inside binomial noise), mean latency **6.7s vs 16.5s** (~2.5×), max **13.9s vs 241s** | `tests/evaluations/results_longmemeval_50.json` | read directly |

`pytest` asserts each of these (see [tests/test_paper_claims.py](tests/test_paper_claims.py)). Where a
claim is an *honest limitation* — LoCoMo entity-J degrading, the abstention effect not surviving
clustering — the test asserts the *limitation*, so it can't silently drift into an overclaim.

### How the raw outputs were produced (method, not runnable here)

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

### Layout

```
fireweed-client/             the public Python SDK (+ demo) — the product surface
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

MIT for the SDK (`fireweed-client/`) and the evaluation/recompute code (see [LICENSE](LICENSE)).
The Fireweed engine itself is **not** included in this repo and is not open source. Benchmark outputs and fixtures are
released for verification; third-party datasets retain their own licenses — in particular the LoCoMo
corpora under `fireweed-v16/data/locomo/` derive from **LoCoMo** (Maharana et al., ACL 2024) and are
subject to that dataset's terms.

## Citation

If you use this work, please cite the archived release (the concept DOI always resolves to the latest version):

```bibtex
@misc{sood2026fireweed,
  title  = {A Model-Independent Memory Substrate: Preserving an Agent's Account
            of a User Across LLM Swaps, Scales, and Families},
  author = {Sood, Sanyam},
  year   = {2026},
  doi    = {10.5281/zenodo.21278301},
  url    = {https://doi.org/10.5281/zenodo.21278301},
  note   = {Paper and verification bundle, v1.0.0 (version DOI: 10.5281/zenodo.21278302)}
}
```
