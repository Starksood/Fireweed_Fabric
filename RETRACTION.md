# Retraction — the scaled abstention result (2026-08-22)

**The claim "Fireweed 0 confident false assertions vs bare RAG 154" (1,200 items / 722 personas),
described in this repository as the load-bearing scaled result, is WITHDRAWN. It measured an empty
substrate.**

You can verify this retraction yourself from files already in this repository — no access to the
closed implementation is required.

## What went wrong

The Fireweed arm of that benchmark answered every question from a substrate containing **no nodes**.
An empty graph abstains on everything, so it cannot produce a false assertion. The zero is the
absence of a measurement, not the result of one.

```bash
python3 - <<'PY'
import json
from collections import Counter
rows = json.load(open("fireweed-v16/bench/abstention_v21/abstention_v21_full.json"))["rows"]
c = Counter(r["fw_prose"].strip() for r in rows)
print("rows:", len(rows), "| distinct Fireweed answers:", len(c))
print(c.most_common(1))
PY
```

    rows: 2400 | distinct Fireweed answers: 1
    [("I don't have any information about that person or topic in memory.", 2400)]

All 2,400 rows carry the identical `entity_not_found` template, for both readers. In the private
engine repository the cause is visible directly: 721 of the 722 cached persona substrates are empty
(`"nodes": []`), and the cache is written *after* perception, so an empty snapshot means perception
produced nothing.

Additionally, every item in the adversarial suite is an "absent" trap — the correct answer to all
1,200 is *abstain*. A system that refuses everything therefore scores perfectly. The suite had no
answerable items to catch that.

## What this does and does not affect

| | Status |
|---|---|
| Fireweed 0 vs RAG 154 (scaled, §8) | **WITHDRAWN** — the Fireweed arm was absent, not sound |
| RAG's 154 confident false assertions | Stands as a measurement **of RAG** |
| §6.5 / §8 pilot: pooled RAG **18** vs Fireweed **9** | **Stands.** 60 rows, 40 distinct Fireweed answers, substrate populated. Cluster-robust CI crosses zero, sign test p≈0.06 — weak, and always reported as weak |
| Write-side interchangeability, read-side, lesion, perturbation, closed-loop | **Unaffected.** Different corpora, different harnesses, populated substrates |

The small, statistically weak result was sound. The large, load-bearing one was not.

## Why it stood for seven weeks

`tests/test_paper_claims.py::test_abstention_scaled_zero_vs_154` recounts the raw judged rows rather
than trusting a summary — which is the right discipline, and it passed, because the arithmetic of the
artifact was correct. Nothing asserted that the substrate under test was non-empty. The verification
checked the sum, not the subject.

This failure class had already been recorded twice in this project's own numbers file (a scale run
where 373 of 474 episodes had empty substrates, and a model sweep where two of three runs did), and
was fixed both times in the harness where it was found. This benchmark predates both and never
received the guard.

## What has been done

- The claim is marked INVALIDATED in the project's numbers-of-record.
- The benchmark now refuses to score when mean nodes per persona falls below a threshold, naming the
  likely cause (perceiver not loaded/reachable) and the poisoned cache to delete.
- The test above is disabled pending a valid re-run rather than left passing.

A corrected measurement requires a verified-non-empty perceiver pass and will be published with the
substrate statistics alongside it. Until then there is **no scaled abstention claim** for this system.

## Note

The premise of this project is that a record should be checkable, and that a claim without a
verifiable receipt is not a claim. That has to apply hardest to our own numbers. This retraction is
published with the evidence and the reproduction command rather than by quietly editing a table.
