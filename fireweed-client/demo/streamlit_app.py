"""Fireweed swap demo — make the math visible.

Chat with an agent whose memory is a deterministic, auditable graph (not a vector dump). Watch the
grounded nodes form as you talk, then HOT-SWAP the model (OpenAI ↔ Anthropic ↔ local) and see the
memory — and the answer's provenance — stay identical. The model is a transient tenant; the substrate
is the sovereign state.

    pip install streamlit fireweed-client        # or run from this repo
    # start the backend (private repo): uvicorn app:build_default_app --factory --port 8000
    streamlit run fireweed-client/demo/streamlit_app.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st

# import the local SDK without needing `pip install` (demo lives beside the package)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fireweed_client import FireweedClient, FireweedError  # noqa: E402

PROVIDERS = {
    "local (LM Studio)": ("local", "qwen/qwen3-4b-2507"),
    "OpenAI": ("openai", "gpt-4o-mini"),
    "Anthropic": ("anthropic", "claude-sonnet-5"),
}

st.set_page_config(page_title="Fireweed — swap demo", page_icon="🔥", layout="wide")
st.title("🔥 Fireweed — the memory has a model, not the other way around")

# ── connection ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Connection")
    base_url = st.text_input("Backend URL", value="http://localhost:8000")
    api_key = st.text_input("API key", value="dev-key-tenant-a", type="password")
    session_id = st.text_input("Session", value="demo")
    st.header("Reader model")
    provider_label = st.selectbox("Provider (hot-swappable)", list(PROVIDERS))
    provider, model = PROVIDERS[provider_label]
    st.caption("Swapping the model never touches the memory — prove it with the button below.")

client = FireweedClient(api_key=api_key, base_url=base_url)


def _online() -> bool:
    try:
        client.health()
        return True
    except Exception:
        return False


if not _online():
    st.error(f"Backend not reachable at {base_url}. Start it (private repo): "
             "`uvicorn app:build_default_app --factory --port 8000`, then reload.")
    st.stop()

col_chat, col_mem = st.columns([1, 1])

# ── left: write experience, ask questions ─────────────────────────────────────
with col_chat:
    st.subheader("1. Tell the agent about yourself")
    msg = st.text_input("Say something", value="I moved to Portland and adopted a tabby cat named Pekoe.",
                        key="msg")
    if st.button("Commit to memory", type="primary"):
        try:
            r = client.commit(session_id, msg)
            st.success(f"Perceived → {r['admitted']} grounded fact(s) committed.")
        except FireweedError as e:
            st.error(str(e))

    st.subheader("2. Ask a question")
    q = st.text_input("Question", value="Where do I live and what pet do I have?", key="q")
    if st.button("Answer (current model)"):
        try:
            a = client.read(session_id, q, provider=provider, model=model)
            st.markdown(f"**Answer** ({a['model_used']}, {a['latency_ms']:.0f} ms): {a['answer']}")
            st.caption(f"grounded in nodes: {', '.join(a['provenance_node_ids']) or '(abstained)'}")
        except FireweedError as e:
            st.error(str(e))

    # THE showcase — same question, every provider, provenance compared
    st.subheader("3. 🔄 Prove model-independence")
    if st.button("Answer with ALL providers and compare provenance"):
        rows, provs = [], []
        for label, (pv, md) in PROVIDERS.items():
            try:
                a = client.read(session_id, q, provider=pv, model=md)
                rows.append({"model": a["model_used"], "answer": a["answer"],
                             "provenance": tuple(a["provenance_node_ids"])})
                provs.append(tuple(a["provenance_node_ids"]))
            except FireweedError as e:
                rows.append({"model": f"{pv}", "answer": f"⚠ {e.detail}", "provenance": ()})
        st.table(rows)
        real = [p for p in provs if p]
        if real and len(set(real)) == 1:
            st.success("✅ Same provenance across every model — the substrate is the durable state; "
                       "the model is interchangeable. Wording differs, grounding does not.")
        elif real:
            st.warning("Provenance differed — inspect which model retrieved differently.")

# ── right: the memory graph forming + provenance ──────────────────────────────
with col_mem:
    st.subheader("The memory (deterministic graph)")
    try:
        nodes = client.retrieve(session_id, q)["matched"]
        st.metric("Grounded nodes matched", len(nodes))
        for n in nodes:
            st.markdown(f"- **{n['claim']}**  \n  `{n['node_id']}` · {', '.join(n['domains'])} · "
                        f"score {n['score']}")
    except FireweedError as e:
        st.error(str(e))

    with st.expander("🔎 Audit — every memory traces to its turn"):
        try:
            recs = client.audit(session_id)["records"]
            st.dataframe([{"claim": r["claim"], "turn": r["source_turn_id"],
                           "span": r["source_span"], "stored_at": r["stored_at"],
                           "firewall": r["firewall_decision"]} for r in recs],
                         use_container_width=True)
        except FireweedError as e:
            st.error(str(e))

st.caption("Retrieval is deterministic (~1 ms); the seconds are the LLM. Export the session as a "
           "portable, signed snapshot — the sovereign entity — from the backend's /export endpoint.")
