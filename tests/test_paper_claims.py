"""Assert every load-bearing number in the Fireweed paper against the committed benchmark
outputs. These are the researcher-facing "the paper's numbers are real" checks.

Each test reads the EXPECTED value from a committed JSON artifact and asserts it lands in the
band the paper states (with tolerances), so the test encodes the paper's *claim* and the JSON
provides the *evidence*. Nothing here imports `fireweed`, runs a model, or touches a network:
similarities were recomputed on one public encoder (sbert all-MiniLM-L6-v2) by the recompute
scripts, and these tests read those recomputed results plus the raw perturbation/loop outputs.

Run:  pytest -q     (optionally `python reproduce.py` first to regenerate the sbert-derived JSONs)
"""
import json
from pathlib import Path
import pytest

BENCH = Path(__file__).resolve().parent.parent / "fireweed-v16" / "bench"


def L(name: str) -> dict:
    return json.loads((BENCH / name).read_text(encoding="utf-8"))


# ── §4.1 Write-side interchangeability ────────────────────────────────────────────
def test_write_side_claim_semantic_band():
    """Paper §4.1: cross-perceiver claim-semantic 0.77–0.87 (sbert), across 4x scale + 2 families."""
    sb = L("sbert_unified_results.json")
    vals = [p["claim_semantic_sbert"] for p in sb["write_side_pairwise_sbert"]]
    assert len(vals) == 3
    for v in vals:
        assert 0.75 <= v <= 0.89, f"write-side claim-sem {v} outside stated 0.77–0.87 band"


def test_write_side_cross_persona_floor():
    """Paper §4.1: cross-persona floor ~0.29 (accounts of different people)."""
    sb = L("sbert_unified_results.json")
    assert sb["write_side_cross_persona_floor_sbert" if "write_side_cross_persona_floor_sbert" in sb
            else "write_cross_persona_floor_sbert"] == pytest.approx(0.29, abs=0.05)


def test_write_side_ceiling_is_one():
    """Paper §4.1: same-perceiver temp-0 ceiling = 1.00 (deterministic re-perception)."""
    sb = L("sbert_unified_results.json")
    assert sb["write_same_perceiver_ceiling"] == pytest.approx(1.0, abs=1e-9)


def test_write_side_headline_beats_floor():
    """The load-bearing separation: every cross-model pair sits well above the different-person floor."""
    sb = L("sbert_unified_results.json")
    floor = sb["write_cross_persona_floor_sbert"]
    for p in sb["write_side_pairwise_sbert"]:
        assert p["claim_semantic_sbert"] - floor > 0.4


# ── §4.1 Third-party (LoCoMo) replication — the external-validity check ────────────
def test_locomo_semantic_replicates_above_floor():
    """Paper §4.1/Table 2: on LoCoMo the semantic headline holds — cross-perceiver ~0.79,
    +~0.43 over a cross-PERSON floor ~0.36 (ceiling 1.0)."""
    lo = L("sbert_locomo_anchors_results.json")
    cp = lo["cross_perceiver_same_person_sbert"]["mean"]
    fl = lo["cross_person_floor_sbert"]["mean"]
    assert cp == pytest.approx(0.79, abs=0.06), f"LoCoMo cross-perceiver {cp}"
    assert fl == pytest.approx(0.36, abs=0.06), f"LoCoMo floor {fl}"
    assert cp - fl > 0.30, "LoCoMo semantic should clear its cross-person floor by a wide margin"
    assert cp >= 0.75, "LoCoMo cross-perceiver should land inside the synthetic 0.77–0.87 band"


def test_locomo_entity_j_degrades_honestly():
    """Paper §4.1: the HONEST gap — entity-Jaccard degrades on open-domain chat (mean ~0.43),
    far below the synthetic 1.0. This is a reported limitation, asserted so it can't silently 'improve'."""
    d = L("write_side_locomo_caroline_results.json")
    ent = [p["entity_jaccard"] for p in d["pairwise"]]
    mean_ent = sum(ent) / len(ent)
    assert mean_ent < 0.60, f"LoCoMo entity-J mean {mean_ent} — paper reports it degraded (~0.43)"


# ── §4.2 Read-side interchangeability ─────────────────────────────────────────────
def test_read_side_matched_above_shuffled_floor():
    """Paper §4.2: readers paraphrase but agree in meaning — matched 0.69–0.77 vs a shuffled-pair
    topical floor ~0.33, permutation p < 0.01, on two model pairs."""
    sb = L("sbert_unified_results.json")
    assert len(sb["read_side"]) == 2
    for r in sb["read_side"]:
        assert 0.66 <= r["matched"] <= 0.80, f"read matched {r['matched']}"
        assert r["floor"] == pytest.approx(0.33, abs=0.05), f"read floor {r['floor']}"
        assert r["matched"] - r["floor"] > 0.30
        assert r["perm_p"] < 0.01, f"read permutation p {r['perm_p']}"


# ── §5 Lesion (non-substrate control) ─────────────────────────────────────────────
def test_lesion_entity_collapses_without_substrate():
    """Paper §5: ablating only consolidation collapses entity agreement 0.78 -> 0.10 (gap ~0.68)."""
    les = L("lesion_contrast_results.json")
    assert les["substrate_mean"]["entity_jaccard"] == pytest.approx(0.78, abs=0.05)
    assert les["naive_mean"]["entity_jaccard"] == pytest.approx(0.10, abs=0.05)
    assert les["entity_jaccard_gap"] > 0.6


def test_lesion_claim_semantic_is_tied():
    """Paper §5: raw claim similarity is ~tied (~0.88 both) — so the STRUCTURE, not the shared
    input, is what the substrate preserves across the swap."""
    les = L("lesion_contrast_results.json")
    sub = les["substrate_mean"]["claim_semantic"]
    naive = les["naive_mean"]["claim_semantic"]
    assert abs(sub - naive) < 0.05, f"claim-sem should be ~tied, got {sub} vs {naive}"


# ── §6 Perturbation battery (null controls) ───────────────────────────────────────
def test_perturbation_null_fork_is_identity():
    """Paper §6: the null-fork control (fork with no divergent experience) agrees ~1.0 — the
    divergence metric only fires on genuine divergence, not by construction."""
    fk = L("fork_divergence_results.json")
    assert fk["null_fork_agreement"]["claim_semantic"] == pytest.approx(1.0, abs=0.05)


def test_perturbation_merge_no_cross_person_contamination():
    """Paper §6: merging two DIFFERENT people's substrates yields 0.0 contamination / 0 chimera nodes
    — identities don't bleed."""
    mg = L("merge_identity_results.json")
    dp = mg["different_person"]
    assert dp["contamination_rate"] == pytest.approx(0.0, abs=1e-9)
    assert dp["chimera_nodes"] == 0


def test_perturbation_corrupt_full_recovery():
    """Paper §6: after corruption, re-exposure restores the anchor set (recovery fraction 1.0)."""
    cr = L("corrupt_resilience_results.json")
    assert cr["recovery"]["recovery_fraction"] == pytest.approx(1.0, abs=1e-9)


# ── §8 Structural abstention (cluster-robust) ─────────────────────────────────────
def test_abstention_pooled_counts_and_direction():
    """Paper §8: pooled bare-RAG 18 vs Fireweed 9 confident false assertions; all 5 readers reduce."""
    cl = L("abstention_cluster_stats.json")
    rag = sum(v["rag"] for v in cl["per_reader"].values())
    fw = sum(v["fw"] for v in cl["per_reader"].values())
    assert rag == 18 and fw == 9, f"pooled counts {rag} vs {fw}"
    assert cl["n_readers_reduced"] == "5/5"


def test_abstention_not_significant_cluster_robust():
    """Paper §8 (honest demotion): once question/reader clustering is accounted for, the effect is
    NOT significant — the bootstrap CI crosses zero and the reader sign test p ~ 0.06."""
    cl = L("abstention_cluster_stats.json")
    lo, hi = cl["question_cluster_bootstrap_reduction_ci95"]
    assert lo < 0 < hi, f"CI {lo,hi} should cross zero (paper claims not significant)"
    assert cl["reader_sign_test_p_two_sided"] == pytest.approx(0.0625, abs=0.02)


def test_judge_human_agreement_kappa():
    """Paper §8: LLM-judge validated against a human annotator — Cohen's κ ≈ 0.75, ~92% agreement."""
    jh = L("judge_human_agreement_results.json")
    assert jh["cohens_kappa"] == pytest.approx(0.75, abs=0.05)
    assert jh["agreement"] >= 0.88


# ── §9 Closed loop (supporting property) ──────────────────────────────────────────
def test_closed_loop_ood_json_validity_gain():
    """Paper §9: the canonical 3B QLoRA adapter takes OOD valid-JSON from 1/12 (base) to 12/12,
    and OOD claim-F1 from 0.00 to ~0.90 — the loop's gains live in the adapter, applied to a frozen base."""
    d = L("stage_4_3b_iter_results.json")
    before, after = d["before"]["ood"], d["after"]["ood"]
    assert before["json_valid"] == "1/12" and after["json_valid"] == "12/12", \
        f"OOD valid-JSON {before['json_valid']} -> {after['json_valid']} (paper: 1/12 -> 12/12)"
    assert before["claim_f1_mean"] == pytest.approx(0.0, abs=1e-6)
    assert after["claim_f1_mean"] == pytest.approx(0.90, abs=0.05)


# ── Integrity: the bundle stays offline / implementation-free ─────────────────────
def test_no_fireweed_import_in_scripts():
    for py in BENCH.glob("*.py"):
        src = py.read_text(encoding="utf-8")
        assert "import fireweed" not in src and "from fireweed" not in src, f"{py.name} imports fireweed"


def test_no_network_endpoints_in_scripts():
    for py in BENCH.glob("*.py"):
        src = py.read_text(encoding="utf-8")
        for bad in ("127.0.0.1", "localhost", "/v1/embeddings", "requests.post", "lmstudio"):
            assert bad not in src, f"{py.name} references {bad} — bundle must run offline"
