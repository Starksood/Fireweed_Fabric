# fireweed-client

Official Python client for the **Fireweed Memory API** — durable, model-independent memory for LLM
agents. Give your agent a memory that is a deterministic, auditable knowledge graph (not a vector dump
of past prompts), and swap the underlying model any time without losing state.

The client is a thin HTTP wrapper: **it contains zero memory logic**. The substrate, grounding
firewall, and resolver run server-side — you integrate a durable memory in a few lines and never have
to build (or maintain) any of it.

## Install

```bash
pip install fireweed-client
```

## Quick start

```python
from fireweed_client import FireweedClient

with FireweedClient(api_key="YOUR_KEY", base_url="https://api.fireweed.example") as fw:
    # write experience — the server perceives it and commits only grounded facts
    # `speaker` anchors first-person facts to a person; without it "I" names nobody and reads abstain.
    fw.commit("user-42", "I moved to Portland last spring.", speaker="Maya")

    # deterministic retrieval (fast, no LLM) — grounded nodes
    fw.retrieve("user-42", "Where does the user live?")

    # a grounded answer, with provenance (every answer traces to memory nodes)
    ans = fw.read("user-42", "What pet does the user have?")
    print(ans["answer"], "→ grounded in", ans["provenance_node_ids"])

    # semantic search across ALL of this user's sessions
    fw.search("pets", k=5)

    # audit: every node's source turn + verbatim span + immutable timestamp
    fw.audit("user-42")
```

## Vendor independence (hot-swap the model, keep the memory)

The memory is the durable object; the model is a transient, swappable tenant. Answer the same
question with different providers — the substrate and the answer's provenance are unchanged:

```python
fw.read("user-42", "Where do I live?", provider="openai",    model="gpt-4o-mini")
fw.read("user-42", "Where do I live?", provider="anthropic", model="claude-sonnet-5")
fw.read("user-42", "Where do I live?", provider="local")     # your own hosted model
```

## Use it as an agent's memory (LangChain-style loop)

```python
fw = FireweedClient(api_key="YOUR_KEY")

def agent_turn(user_id: str, user_name: str, user_msg: str) -> str:
    # `speaker` anchors the user's first-person facts ("I moved to Portland") to them
    fw.commit(user_id, user_msg, speaker=user_name)    # remember what the user said
    ctx = fw.retrieve(user_id, user_msg)["matched"]    # grounded, deterministic recall
    # ... hand `ctx` to your LangChain/LlamaIndex/custom agent as grounded memory ...
    reply = fw.read(user_id, user_msg)["answer"]       # or let Fireweed answer, with provenance
    return reply
```

## API surface

| Method | Endpoint | Notes |
|---|---|---|
| `health()` | `GET /v1/health` | |
| `commit(session, text, source_id=None, speaker=None)` | `POST /v1/memory/commit` | perceive → decide → commit; `speaker` anchors first-person facts |
| `retrieve(session, query)` | `POST /v1/memory/retrieve` | deterministic, fast, grounded nodes |
| `read(session, question, provider=None, model=None)` | `POST /v1/memory/read` | grounded answer + provenance + model hot-swap |
| `search(query, k=10)` | `POST /v1/memory/search` | cross-session semantic search |
| `audit(session)` | `GET /v1/memory/{session}/audit` | provenance per node (turn-link + timestamps) |
| `sessions()` | `GET /v1/memory/sessions` | |
| `export(session)` | `GET /v1/memory/{session}/export` | the portable, sovereign snapshot |

Errors raise `FireweedError` (with `.status` and `.detail`); transient 5xx/network failures are retried
with backoff.
