"""fireweed-client — the official thin HTTP client for the Fireweed Memory API.

By design this SDK contains **zero deterministic memory logic** — the substrate, resolver, firewall,
and grounding all live behind the API. The client only authenticates, calls endpoints, retries
transient failures, and raises clean errors. That is the whole point: developers integrate a durable,
model-independent memory in a few lines without ever seeing (or being able to reproduce) the engine.
"""
from __future__ import annotations
import time
from typing import Any

import httpx

__all__ = ["FireweedClient", "FireweedError"]


class FireweedError(Exception):
    """Raised for a non-2xx API response. `status` and `detail` carry the server's message."""

    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"[{status}] {detail}")


class FireweedClient:
    """Client for the Fireweed Memory API.

        with FireweedClient(api_key="...", base_url="https://api.fireweed.example") as fw:
            fw.commit("session-1", "I moved to Portland and adopted a tabby cat.")
            print(fw.read("session-1", "Where does the user live?")["answer"])
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000",
                 timeout: float = 30.0, max_retries: int = 2, transport: httpx.BaseTransport | None = None):
        self.max_retries = max_retries
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout,
                                    headers={"X-API-Key": api_key}, transport=transport)

    # -- transport with retry on transient failures (network / 5xx) --
    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        last: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.request(method, path, **kwargs)
            except httpx.TransportError as e:
                last = e
            else:
                if resp.status_code < 500:
                    return resp
                last = FireweedError(resp.status_code, _detail(resp))
            if attempt < self.max_retries:
                time.sleep(0.2 * (2 ** attempt))         # exponential backoff
        if isinstance(last, FireweedError):
            raise last
        raise FireweedError(0, f"connection failed: {last}")

    def _json(self, method: str, path: str, **kwargs) -> Any:
        resp = self._request(method, path, **kwargs)
        if resp.status_code >= 400:
            raise FireweedError(resp.status_code, _detail(resp))
        return resp.json()

    # -- endpoints (mirror the API 1:1; no logic) --
    def health(self) -> dict:
        return self._json("GET", "/v1/health")

    def commit(self, session_id: str, text: str, source_id: str | None = None,
               speaker: str | None = None) -> dict:
        """Write experience into memory (perceive -> deterministic decide -> commit).

        Pass `speaker` for first-person input: "I moved to Portland" is rewritten to
        "<speaker> moved to Portland" before perception, so the fact anchors to that person and
        becomes answerable. Without it the subject stays "I", which names nobody — the fact is
        stored and retrievable but reads will honestly abstain.
        """
        return self._json("POST", "/v1/memory/commit",
                          json={"session_id": session_id, "text": text, "source_id": source_id,
                                "speaker": speaker})

    def retrieve(self, session_id: str, query: str) -> dict:
        """Deterministic retrieval — grounded nodes, no LLM. Fast."""
        return self._json("POST", "/v1/memory/retrieve",
                          json={"session_id": session_id, "query": query})

    def read(self, session_id: str, question: str, provider: str | None = None,
             model: str | None = None) -> dict:
        """Grounded answer. `provider`/`model` hot-swap the reader (local/anthropic/openai) — the
        memory is unchanged, only the transient model."""
        return self._json("POST", "/v1/memory/read",
                          json={"session_id": session_id, "question": question,
                                "provider": provider, "model": model})

    def search(self, query: str, k: int = 10) -> dict:
        """Semantic search across all of the tenant's sessions."""
        return self._json("POST", "/v1/memory/search", json={"query": query, "k": k})

    def audit(self, session_id: str) -> dict:
        """Provenance per node: turn-link + verbatim span + immutable timestamps + firewall decision."""
        return self._json("GET", f"/v1/memory/{session_id}/audit")

    def sessions(self) -> list[str]:
        return self._json("GET", "/v1/memory/sessions")["sessions"]

    def export(self, session_id: str) -> bytes:
        """Download the portable, sovereign snapshot blob for a session."""
        resp = self._request("GET", f"/v1/memory/{session_id}/export")
        if resp.status_code >= 400:
            raise FireweedError(resp.status_code, _detail(resp))
        return resp.content

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FireweedClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def _detail(resp: httpx.Response) -> str:
    try:
        return resp.json().get("detail", resp.text)
    except Exception:
        return resp.text or f"HTTP {resp.status_code}"
