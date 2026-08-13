# fireweed-client

Official Python client for the **Fireweed Memory API** — durable, model-independent memory for LLM
agents. Give your agent a memory that is a deterministic, auditable knowledge graph (not a vector dump
of past prompts), and swap the underlying model any time without losing state.

The client is a thin HTTP wrapper: **it contains zero memory logic**. The substrate, grounding
firewall, and resolver run server-side — you integrate a durable memory in a few lines and never have
to build (or maintain) any of it.

## Install

Not on PyPI yet — install from source (it has one dependency, `httpx`):

```bash
git clone https://github.com/Starksood/Fireweed_Fabric.git
pip install ./Fireweed_Fabric/fireweed-client
```

> **You also need a backend.** The client is HTTP-only and there is **no public hosted endpoint yet**;
> the engine is closed-source, so self-hosting is not available either. The SDK is usable today if you
> have a key and a host (design partners) or run the backend yourself. Open an issue for access.

## Quick start

```python
from fireweed_client import FireweedClient

with FireweedClient(api_key="YOUR_KEY", base_url="https://api.fireweed.example") as fw:
    # bind a session to the person speaking in it
    maya = fw.session("user-42", speaker="Maya")

    # write experience — the server perceives it and commits only grounded facts.
    # `speaker` rewrites "I ..." to "Maya ..." so the fact anchors to a person; without it the
    # subject stays "I", which names nobody, and reads will honestly abstain.
    maya.commit("I moved to Portland last spring.")

    # deterministic retrieval (fast, no LLM) — grounded nodes
    maya.retrieve("Where does Maya live?")

    # a grounded answer, with provenance (every answer traces to memory nodes)
    ans = maya.read("What pet does Maya have?")
    print(ans["answer"], "→ grounded in", ans["provenance_node_ids"])

    # audit: every node's source turn + verbatim span + immutable timestamp
    maya.audit()

    # semantic search spans ALL of the tenant's sessions, so it stays on the client
    fw.search("pets", k=5)
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
    # one client serves every user; the session carries who is speaking
    user = fw.session(user_id, speaker=user_name)
    user.commit(user_msg)                              # remember what the user said
    ctx = user.retrieve(user_msg)["matched"]           # grounded, deterministic recall
    # ... hand `ctx` to your LangChain/LlamaIndex/custom agent as grounded memory ...
    return user.read(user_msg)["answer"]               # or let Fireweed answer, with provenance
```

## API surface

| Method | Endpoint | Notes |
|---|---|---|
| `session(session_id, speaker=None)` | — | binds a session (+speaker) so calls drop the repeated args |
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
