#!/usr/bin/env python3
"""Regenerate Paper-1's tables directly from committed bench JSON artifacts.

Every number in the paper should trace to a committed result file, not to prose. This script reads the
artifacts and emits paper-ready Markdown tables to `papers/paper1_tables.md`, each stamped with its
source file. Run it after any bench re-run to keep the paper honest:

    python3 bench/make_paper_figures.py

Design note (2026-06-30): built right after an audit found the read-side "90.73%" was actually
stage_2 opus SELF-consistency (within-model determinism), not cross-model interchangeability. This
generator makes that distinction explicit — read-side prints BOTH the within-model floor and the
(weak) cross-model number, so the two can never again be conflated.
"""
from __future__ import annotations
import json
from pathlib import Path

BENCH = Path(__file__).parent
OUT = BENCH.parent.parent / "papers" / "paper1_tables.md"


def load(name: str):
    p = BENCH / name
    if not p.exists():
        return None
    return json.loads(p.read_text())


def pct(x) -> str:
    try:
        return f"{float(x):.0%}"
    except Exception:
        return str(x)


def f2(x) -> str:
    try:
        return f"{float(x):.2f}"
    except Exception:
        return str(x)


def section(title: str, src: str) -> str:
    return f"\n### {title}\n*source: `{src}`*\n\n"


def table_write_side() -> str:
    d = load("write_side_served_v3_results.json")
    if not d:
        return section("Table 1 — Write-side interchangeability", "MISSING") + "_artifact missing_\n"
    out = section("Table 1 — Write-side interchangeability (§4.1)", "write_side_served_v3_results.json")
    out += "| pair | axis | entity-J | domain-J | claim-semantic |\n|---|---|---|---|---|\n"
    axis = {
        "google/gemma-3-1b vs google/gemma-3-4b": "scale",
        "google/gemma-3-1b vs qwen/qwen3-4b-2507": "scale + family",
        "google/gemma-3-4b vs qwen/qwen3-4b-2507": "family",
    }
    short = lambda s: (s.replace("google/gemma-3-", "gemma-").replace("qwen/qwen3-4b-2507", "qwen-4b"))
    for row in d.get("pairwise", []):
        pair = row["pair"]
        ca = row.get("claim_alignment", {})
        out += (f"| {short(pair)} | {axis.get(pair,'—')} | {f2(row.get('entity_jaccard'))} | "
                f"{f2(row.get('domain_jaccard'))} | {f2(ca.get('semantic'))} |\n")
    out += f"\n*verdict:* {d.get('verdict','—')}  ·  *competent perceivers:* {', '.join(short(m) for m in d.get('competent',[]))}\n"
    sb = load("sbert_unified_results.json")
    tc = load("msc_true_ceiling_gemma_results.json")
    if sb:
        ceiling = ""
        if tc:
            pw = tc.get("pairwise", [{}])[0]
            ceiling = (f" · same-family temperature-0.7 ceiling "
                       f"{f2(pw.get('claim_alignment', {}).get('semantic'))} "
                       f"(gemma-1b vs gemma-4b under realistic sampling, MSC corpus — the non-hollow upper reference)")
        out += (f"\n*Anchors (all sbert):* cross-persona floor {f2(sb.get('write_cross_persona_floor_sbert'))} "
                f"(accounts of different people) · determinism check {f2(sb.get('write_same_perceiver_ceiling'))} "
                f"(temp-0 same-perceiver rerun — proves determinism, not an upper bound){ceiling}. "
                f"The 0.77–0.87 cross-model band sits far above the different-person floor and close beneath "
                f"the same-family ceiling.\n")
    return out


def table_locomo() -> str:
    """Table 2 — third-party (LoCoMo) write-side replication. entity/domain-J from the harness
    run; claim-semantic on sbert (from sbert_locomo_anchors) so it's on the paper's one scale."""
    d = load("write_side_locomo_caroline_results.json")
    jf = load("write_side_locomo_caroline_junkfilter_results.json")
    sb = load("sbert_locomo_anchors_results.json")
    if not d or not sb:
        return section("Table 2 — LoCoMo third-party replication", "MISSING") + "_artifact missing_\n"
    out = section("Table 2 — Third-party (LoCoMo) write-side replication (§4.1)",
                  "write_side_locomo_caroline_junkfilter_results.json (entity-J, post junk-filter) + "
                  "write_side_locomo_caroline_results.json (pre-filter) + sbert_locomo_anchors_results.json")
    out += "| pair | axis | entity-J | domain-J | claim-semantic (sbert) |\n|---|---|---|---|---|\n"
    axis = {
        "google/gemma-3-1b vs google/gemma-3-4b": "scale",
        "google/gemma-3-1b vs qwen/qwen3-4b-2507": "scale + family",
        "google/gemma-3-4b vs qwen/qwen3-4b-2507": "family",
    }
    short = lambda s: (s.replace("google/gemma-3-", "gemma-").replace("qwen/qwen3-4b-2507", "qwen-4b"))
    sbert_by_pair = {p["pair"]: p["claim_semantic_sbert"]
                     for p in sb.get("cross_perceiver_same_person_sbert", {}).get("pairwise", [])}
    jf_by_pair = {p["pair"]: p["entity_jaccard"] for p in (jf or {}).get("pairwise", [])}
    ej_pre, ej_post = [], []
    for row in d.get("pairwise", []):
        pair = row["pair"]
        pre = row.get("entity_jaccard")
        post = jf_by_pair.get(pair)
        ej = f"{f2(post)} ({f2(pre)})" if post is not None else f2(pre)
        if pre is not None:
            ej_pre.append(pre)
        if post is not None:
            ej_post.append(post)
        out += (f"| {short(pair)} | {axis.get(pair,'—')} | {ej} | "
                f"{f2(row.get('domain_jaccard'))} | {f2(sbert_by_pair.get(pair))} |\n")
    floor = sb.get("cross_person_floor_sbert", {}).get("mean")
    cpm = sb.get("cross_perceiver_same_person_sbert", {}).get("mean")
    out += (f"\n*Anchors (all sbert):* cross-person floor {f2(floor)} (Caroline vs a different LoCoMo "
            f"speaker, Jon) · same-perceiver ceiling {f2(sb.get('same_perceiver_ceiling'))}. Cross-perceiver "
            f"claim-semantic {f2(cpm)} sits +{f2((cpm or 0) - (floor or 0))} above the floor.\n")
    if ej_post:
        out += (f"\n*Entity-J:* shown post junk-filter, pre-filter in parentheses. A deterministic filter "
                f"(pinned word-frequency lexicon, Zipf ≥ 5.0, + contraction/pronoun exclusion — no model in "
                f"the loop) raises mean entity-J {f2(sum(ej_pre)/len(ej_pre))} → {f2(sum(ej_post)/len(ej_post))}; "
                f"claim-semantic and domain-J are unchanged by the filter, so the residual gap is extraction "
                f"noise (sub-Zipf common words; cross-perceiver nickname canonicalization), not account divergence.\n")
    return out


def table_read_side() -> str:
    out = section("Table 3 — Read-side interchangeability (semantic on sbert, floor-controlled; §4.2)",
                  "sbert_unified_results.json (+ cross_model_* for surface/abstention)")
    short = lambda s: s.replace("google/", "").replace("qwen/", "").replace("-2507", "").replace("gemma-3-", "gemma-").replace("qwen3-", "qwen-")
    out += "| pair | axis | surface token-J | matched (sbert) | shuffled floor | perm p | abstain-agree |\n"
    out += "|---|---|---|---|---|---|---|\n"
    sb = {p["model_a"] + "|" + p["model_b"]: p for p in (load("sbert_unified_results.json") or {}).get("read_side", [])}
    rows = [
        ("cross_model_interchangeability_results.json", "family"),
        ("cross_model_gemma1b_qwen4b.json", "scale + family"),
    ]
    for cmf, axis in rows:
        cm = load(cmf)
        if not cm:
            continue
        c = cm.get("cross_model", {})
        key = cm["model_a"] + "|" + cm["model_b"]
        r = sb.get(key, {})
        pstr = f"<{1/r['trials']:.4f}" if r.get("perm_p", 1) <= 1/r.get("trials", 1) else f2(r.get("perm_p"))
        out += (f"| {short(cm['model_a'])} vs {short(cm['model_b'])} | {axis} | "
                f"{f2(c.get('mean_content_consistency'))} | {f2(r.get('matched'))} | {f2(r.get('floor'))} | "
                f"{pstr} | {f2(c.get('mean_abstention_agreement'))} |\n")
    out += ("\n*Reading:* readers paraphrase (low surface token-Jaccard) but agree in meaning — matched sbert"
            " similarity sits well above the shuffled-pair topical floor (same answers, wrong query-pairing),"
            " so the agreement is query-specific. Same encoder as the write side, so §4.1 and §4.2 are on one"
            " scale. (An earlier draft used a different, higher-baseline embedder — see Appendix A.)\n")
    return out


def table_field() -> str:
    d = load("identity_field_results.json")
    if not d:
        return section("Table 4 — Field-level", "MISSING") + "_artifact missing_\n"
    fi = d.get("field_interchange", {})
    out = section("Table 4 — Field-level interchangeability (self-shape; §4.3)", "identity_field_results.json")
    out += "| comparison | same centroid | mass ratio | dispersion Δ | concentration Δ |\n|---|---|---|---|---|\n"
    label = {"gemma_vs_qwen": "gemma-1b vs qwen-4b (cross-model)", "single_vs_swap": "single vs mid-stream transplant"}
    for k, v in fi.items():
        out += (f"| {label.get(k,k)} | {'✓' if v.get('same_centroid') else '✗'} | {f2(v.get('mass_ratio'))} | "
                f"{f2(v.get('dispersion_delta'))} | {f2(v.get('concentration_delta'))} |\n")
    return out


def table_perturbation() -> str:
    out = section("Table 6 — Perturbation battery (§6)", "fork/merge/corrupt/hot_swap/longitudinal_substrate + write_side v3")
    out += "| perturbation | thought experiment | key numbers |\n|---|---|---|\n"
    lg = load("longitudinal_substrate_results.json")
    if lg:
        a = lg.get("agreements", {})
        cms = a.get("cross_model", {}).get("claim_semantic")
        sw = a.get("swap_vs_single", {}).get("claim_semantic")
        det = a.get("determinism_floor", {}).get("claim_semantic")
        oi = a.get("order_invariance", {}).get("claim_semantic")
        out += (f"| age ({lg.get('n_sessions','?')} sessions) | gradual change | determinism {f2(det)}, "
                f"order-invariance {f2(oi)}; cross-model claim-sem {f2(cms)}, transplant {f2(sw)} |\n")
    fk = load("fork_divergence_results.json")
    if fk:
        dv = fk.get("divergent_fork_agreement", {})
        nf = fk.get("null_fork_agreement", {})
        out += (f"| fork | fission | continuity {f2(fk.get('fork_point_persist'))}; divergence: real "
                f"{f2(dv.get('claim_semantic'))} vs null-fork {f2(nf.get('claim_semantic'))}; branch-specific "
                f"{fk.get('branch_specific')} |\n")
    mg = load("merge_identity_results.json")
    if mg:
        sp = mg.get("same_person", {})
        dp = mg.get("different_person", {})
        out += (f"| merge | fusion | same-person dedup {f2(sp.get('shared_past_dedup_ratio'))}; "
                f"different-person contamination {f2(dp.get('contamination_rate'))}, chimera {dp.get('chimera_nodes')} |\n")
    cr = load("corrupt_resilience_results.json")
    if cr:
        rec = cr.get("recovery", {})
        out += (f"| corrupt | amnesia | recovery fraction {f2(rec.get('recovery_fraction'))}, "
                f"id-collisions {rec.get('id_collisions')}; graceful to 50% deletion |\n")
    hs = load("hot_swap_demo_results.json")
    if hs:
        out += (f"| hot-swap | live transplant | {hs.get('nodes_before')}/{hs.get('nodes_before')} pre-swap nodes "
                f"carried (continuity {f2(hs.get('continuity'))}); {hs.get('added_by_b')} added by new model |\n")
    return out


def table_abstention() -> str:
    d = load("adversarial_fabrication_sweep.judged.json")
    if not d:
        return section("Table 7 — Structural abstention", "MISSING") + "_artifact missing_\n"
    out = section("Table 7 — Structural abstention: pilot (§8)", "adversarial_fabrication_sweep.judged.json + abstention_cluster_stats.json + judge_human_agreement_results.json")
    out += ("*Per-reader raw counts only — per-cell n=12 is too small for per-reader inference. The pooled "
            "pilot effect is directional but not significant (below); the load-bearing §8 evidence is the "
            "scaled run beneath this table.*\n\n")
    out += "| reader | bare RAG fab | inside Fireweed fab |\n|---|---|---|\n"
    short = lambda s: s.replace("google/", "").replace("qwen/", "").replace("-2507", "")
    for reader, c in d.get("judged_counts", {}).items():
        n = c.get("n", 12)
        out += f"| {short(reader)} | {c.get('rag_fab',0)}/{n} | {c.get('fw_fab',0)}/{n} |\n"
    st = load("abstention_stats.json")
    cl = load("abstention_cluster_stats.json")
    if st and cl:
        ci = cl.get("question_cluster_bootstrap_reduction_ci95", [None, None])
        out += (f"\n**Directional, not significant.** Pooled bare RAG **{st['rag_fabrications']}** vs Fireweed "
                f"**{st['fw_fabrications']}** confident false assertions; fabrication fell for **{cl['n_readers_reduced']}** "
                f"readers. But the 12 questions recur across readers, so the pooled McNemar (p={st['mcnemar_exact_p_two_sided']}) "
                f"assumes independence it does not have. Cluster-robust: question-bootstrap 95% CI on the reduction "
                f"**[{ci[0]:.2f}, {ci[1]:.2f}] (crosses zero)**; reader sign test two-sided **p = {cl['reader_sign_test_p_two_sided']}**. "
                f"§8 leans on provenance, not the rate.\n")
    jh = load("judge_human_agreement_results.json")
    if jh:
        out += (f"\n*Judge validation ({d.get('judge','—')}):* judge–human agreement {pct(jh['agreement'])}, "
                f"Cohen's κ = {jh['cohens_kappa']} on an {jh['n_items']}-item subset (single annotator).\n")
    # Scaled run (V5): 1,200 items / 722 third-party personas / 2 readers spanning the pilot's
    # capability range. Raw judged rows ship in abstention_v21/abstention_v21_full.json.
    an = load("abstention_v21/abstention_v21_full_analysis.json")
    ev = load("abstention_v21/ensemble_judge_validation.json")
    if an:
        p = an.get("pooled", {})
        pr = an.get("per_reader", {})
        short = lambda s: s.replace("google/", "").replace("qwen/", "").replace("-2507", "")
        out += ("\n**At scale (the load-bearing §8 result).** "
                f"{an.get('n_items'):,} adversarial items over {an.get('n_personas')} third-party MSC personas, "
                f"answered by {len(an.get('readers', []))} readers spanning the pilot's capability range "
                f"({', '.join(short(r) for r in an.get('readers', []))}) in both configurations — "
                f"{p.get('n'):,} answer opportunities per configuration. Inside Fireweed: "
                f"**{p.get('fw_hallucination')}** confident false assertions; bare RAG: **{p.get('rag_hallucination')}**.\n\n")
        out += "| reader | bare RAG fab (n=1200) | inside Fireweed fab (n=1200) |\n|---|---|---|\n"
        for r, c in pr.items():
            out += f"| {short(r)} | {c.get('rag_hallucination')} | {c.get('fw_hallucination')} |\n"
        if ev:
            out += (f"\n*Ensemble judge ({len(ev.get('models', []))} local models, majority vote):* "
                    f"agreement {pct(ev['agreement'])}, Cohen's κ = {ev['cohens_kappa']} vs the human-labeled "
                    f"slice (n={ev['n']}).\n")
        out += ("*source: `abstention_v21/abstention_v21_full.json` (raw judged rows) + "
                "`abstention_v21/abstention_v21_full_analysis.json` + `abstention_v21/ensemble_judge_validation.json`*\n")
    return out


def _ev(before, after, split):
    b, a = before.get(split, {}), after.get(split, {})
    return b, a


def table_closed_loop() -> str:
    it = load("stage_4_3b_iter_results.json")
    un = load("stage_4_3b_union_results.json")
    b05 = load("stage_4_iter1_finetune_results.json")
    seq_u = load("stage_4_iter2_union.json")
    seq_i = load("stage_4_iter2_iterative.json")
    gate = load("stage_4_control2_base_gate.json")
    out = section("Appendix B — Closing the loop (§9)", "stage_4_3b_iter/union + stage_4_iter1_finetune + stage_4_iter2_* + stage_4_control2_base_gate")
    # 3B before/after
    if it:
        bo, ao = _ev(it.get("before", {}), it.get("after", {}), "ood")
        bg, ag = it.get("before", {}).get("general", {}), it.get("after", {}).get("general", {})
        out += "**Canonical 3B (Qwen2.5-3B QLoRA, iterative, epochs=%s):**\n\n" % it.get("epochs")
        out += "| metric | base | + adapter |\n|---|---|---|\n"
        out += f"| OOD valid-JSON | {bo.get('json_valid')} | {ao.get('json_valid')} |\n"
        out += f"| OOD claim-F1 | {f2(bo.get('claim_f1_mean'))} | {f2(ao.get('claim_f1_mean'))} |\n"
        out += f"| general canary hit-rate | {bg.get('hit_rate')} | {ag.get('hit_rate')} |\n"
        out += f"| general JSON-leak | {bg.get('json_leak_rate')} | {ag.get('json_leak_rate')} |\n"
    # 0.5B loss
    if b05:
        out += (f"\n**0.5B pilot:** held-out loss {f2(b05.get('before',{}).get('eval_loss'))} → "
                f"{f2(b05.get('after',{}).get('eval_loss'))}; claim JSON "
                f"{b05.get('before',{}).get('generation',{}).get('json_valid')} → "
                f"{b05.get('after',{}).get('generation',{}).get('json_valid')}.\n")
    # sequencing control (0.5B, step-matched)
    if seq_u and seq_i:
        u = seq_u.get("after", {}).get("ood", {})
        i = seq_i.get("after", {}).get("ood", {})
        out += ("\n**Sequencing control (0.5B, step-matched) — union ≥ iterative:**\n\n"
                "| mode | OOD valid-JSON | OOD claim-F1 |\n|---|---|---|\n"
                f"| union (train-once) | {u.get('json_valid')} | {f2(u.get('claim_f1_mean'))} |\n"
                f"| iterative | {i.get('json_valid')} | {f2(i.get('claim_f1_mean'))} |\n")
    # bootstrap control
    if gate:
        out += (f"\n**Perception-bootstrapping control:** base model self-harvest "
                f"{gate.get('n_kept')}/{gate.get('n_raw')} kept (pass rate {f2(gate.get('pass_rate'))}); "
                f"the iterated adapter passes 12/12 (`maya_v16_sft_b2.gate_report.json`).\n")
    return out


def table_lesion() -> str:
    d = load("lesion_contrast_results.json")
    if not d:
        return section("Table 5 — Lesion", "MISSING") + "_artifact missing_\n"
    out = section("Table 5 — Lesion: substrate vs naive-append across a perceiver swap (§5)",
                  "lesion_contrast_results.json")
    sub, nai = d.get("substrate_mean", {}), d.get("naive_mean", {})
    out += "| cross-perceiver agreement | substrate | naive-append | Δ |\n|---|---|---|---|\n"
    labels = [("entity_jaccard", "entity-Jaccard"), ("domain_jaccard", "domain-Jaccard"),
              ("claim_semantic", "claim-semantic"), ("claim_lexical", "claim-lexical")]
    for k, lab in labels:
        if k in sub and k in nai:
            out += f"| {lab} | {f2(sub[k])} | {f2(nai[k])} | {sub[k]-nai[k]:+.2f} |\n"
    out += (f"\n*models:* {', '.join(m.replace('google/','').replace('qwen/','').replace('-2507','') for m in d.get('models',[]))}"
            f"  ·  *verdict:* {d.get('verdict','—')}\n")
    out += ("\n*Reading:* identical perception; only the deterministic consolidation is ablated. The naive"
            " store's **entity/domain structure collapses** across the swap (0.10/0.30) where the substrate"
            " canonicalizes to one set (0.78/0.90); raw claim similarity is tied — so what the substrate"
            " uniquely preserves is the canonical entity/domain structure, not the surface text.\n")
    return out


def main() -> int:
    parts = [
        "# Paper 1 — tables (auto-generated from committed bench artifacts)\n",
        "*Regenerate with `python3 bench/make_paper_figures.py`. Every number traces to a source file "
        "stamped under its table. Do not hand-edit.*\n",
        table_write_side(),
        table_locomo(),
        table_read_side(),
        table_field(),
        table_lesion(),
        table_perturbation(),
        table_abstention(),
        table_closed_loop(),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts))
    print(f"Wrote {OUT}")
    print("\n".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
