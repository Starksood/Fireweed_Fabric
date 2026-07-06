"""SDK tests via httpx.MockTransport — no backend required (the SDK has zero backend dependency).

Asserts the client forms the right requests (path, auth header, body), parses responses, raises clean
errors, and retries transient failures.
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fireweed_client import FireweedClient, FireweedError  # noqa: E402

API_KEY = "test-key"


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("X-API-Key") == API_KEY          # auth on every call
    p = request.url.path
    body = json.loads(request.content) if request.content else {}
    if p == "/v1/health":
        return httpx.Response(200, json={"status": "ok", "engine": "fireweed-v16", "providers": ["local"]})
    if p == "/v1/memory/commit":
        return httpx.Response(200, json={"tenant_id": "t", "session_id": body["session_id"], "admitted": 2})
    if p == "/v1/memory/retrieve":
        return httpx.Response(200, json={"tenant_id": "t", "session_id": body["session_id"],
                                         "query": body["query"], "matched": [{"node_id": "n1"}],
                                         "latency_ms": 1.1})
    if p == "/v1/memory/read":
        return httpx.Response(200, json={"tenant_id": "t", "session_id": body["session_id"],
                                         "question": body["question"], "answer": "Portland",
                                         "abstained": False, "provenance_node_ids": ["n1"],
                                         "model_used": f"{body.get('provider') or 'default'}",
                                         "latency_ms": 900.0})
    if p == "/v1/memory/search":
        return httpx.Response(200, json={"tenant_id": "t", "query": body["query"],
                                         "hits": [{"session": "s1", "node_id": "n1", "claim": "x",
                                                   "score": 0.9}], "latency_ms": 5.0})
    if p == "/v1/memory/sessions":
        return httpx.Response(200, json={"tenant_id": "t", "sessions": ["s1", "s2"]})
    if p.endswith("/audit"):
        return httpx.Response(200, json={"tenant_id": "t", "session_id": "s1", "n_nodes": 1,
                                         "records": [{"node_id": "n1"}], "latency_ms": 0.5})
    if p.endswith("/export"):
        return httpx.Response(200, content=b"SNAPSHOT_BYTES",
                              headers={"content-type": "application/octet-stream"})
    return httpx.Response(404, json={"detail": "not found"})


@pytest.fixture()
def client():
    with FireweedClient(api_key=API_KEY, base_url="http://api",
                        transport=httpx.MockTransport(_handler)) as c:
        yield c


def test_health(client):
    assert client.health()["status"] == "ok"


def test_commit_retrieve_read(client):
    assert client.commit("s1", "I moved to Portland.")["admitted"] == 2
    r = client.retrieve("s1", "where?")
    assert r["matched"][0]["node_id"] == "n1" and r["latency_ms"] == 1.1
    a = client.read("s1", "where does the user live?")
    assert a["answer"] == "Portland" and a["provenance_node_ids"] == ["n1"]


def test_read_hot_swap_provider_passed_through(client):
    assert client.read("s1", "q", provider="anthropic", model="claude-sonnet-5")["model_used"] == "anthropic"


def test_search_sessions_audit_export(client):
    assert client.search("pet", k=3)["hits"][0]["score"] == 0.9
    assert client.sessions() == ["s1", "s2"]
    assert client.audit("s1")["n_nodes"] == 1
    assert client.export("s1") == b"SNAPSHOT_BYTES"


def test_error_raises_fireweed_error():
    def unauth(_req):
        return httpx.Response(401, json={"detail": "invalid or missing X-API-Key"})
    with FireweedClient(api_key="bad", base_url="http://api",
                        transport=httpx.MockTransport(unauth)) as c:
        with pytest.raises(FireweedError) as ei:
            c.retrieve("s1", "x")
    assert ei.value.status == 401 and "X-API-Key" in ei.value.detail


def test_retries_on_5xx_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)          # no real backoff in tests
    calls = {"n": 0}

    def flaky(_req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"detail": "warming up"})
        return httpx.Response(200, json={"status": "ok", "engine": "e", "providers": []})
    with FireweedClient(api_key=API_KEY, base_url="http://api", max_retries=2,
                        transport=httpx.MockTransport(flaky)) as c:
        assert c.health()["status"] == "ok"
    assert calls["n"] == 2                                       # retried once, then succeeded
