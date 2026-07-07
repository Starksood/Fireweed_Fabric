# Fireweed swap demo (Streamlit)

The 60-second demo: chat with an agent, watch its memory form as a **deterministic, auditable graph**,
then **hot-swap the model** (OpenAI ↔ Anthropic ↔ local) and see the memory — and the answer's
provenance — stay identical. *The model is a transient tenant; the substrate is the sovereign state.*

## Run

```bash
pip install streamlit fireweed-client        # or run from this repo (sys.path handles it)

# 1. start the backend (private repo), e.g. with LM Studio serving the local models:
#    uvicorn app:build_default_app --factory --port 8000

# 2. run the demo:
streamlit run fireweed-client/demo/streamlit_app.py
```

Then, in the browser:
1. **Commit** a fact ("I moved to Portland and adopted a tabby cat named Pekoe.") → watch the grounded
   nodes appear on the right, each with its source turn + verbatim span + timestamp (the audit panel).
2. **Ask** a question → get a grounded answer with `provenance_node_ids`.
3. **🔄 Prove model-independence** → the same question is answered by every provider; the table shows the
   wording differs but the **provenance is identical** — the thesis, made visible.

## What it demonstrates

- **Auditable memory** — every answer traces to specific nodes; every node traces to its turn.
- **Model-independence** — swap the reader; the substrate and grounding don't move.
- **Deterministic speed** — retrieval is ~1 ms; the seconds are purely the LLM.
- **Sovereignty** — the session exports as a portable snapshot blob (backend `/export`).

The SDK contains zero memory logic; the engine stays server-side. The demo proves the system works
without revealing how.
