"""The MCP server must answer its own website, and nothing else's.

The site's origin is not in the code; the stack passes it in through
VOLLEY_ALLOWED_ORIGINS. So the test that a right caller is let in sets
that variable the way the stack does, and the test that a wrong caller
is kept out runs with it set too, so neither can pass by the variable
being empty.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from volley_server import MemoryStore, build_app, is_allowed_origin

SITE = "https://example-site.cloudfront.net"


@pytest.fixture(autouse=True)
def allowlist(monkeypatch):
    monkeypatch.setenv("VOLLEY_ALLOWED_ORIGINS", f"{SITE}, http://localhost:3000")


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://127.0.0.1:8791", "https://127.0.0.1", "http://[::1]:5173", SITE, SITE + "/"])
def test_callers_that_must_be_allowed(origin: str) -> None:
    assert is_allowed_origin(origin)


@pytest.mark.parametrize("origin", ["https://evil.example", "http://localhost.evil.example:3000", "https://example-site.cloudfront.net.evil.example", "null"])
def test_callers_that_must_be_refused(origin: str) -> None:
    assert not is_allowed_origin(origin)


def test_the_site_can_initialize_and_a_stranger_cannot() -> None:
    client = TestClient(build_app(store=MemoryStore(), seed=False))
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "site", "version": "1"}}}
    assert client.post("/mcp", json=body, headers={"origin": SITE}).status_code == 200
    assert client.post("/mcp", json=body, headers={"origin": "https://evil.example"}).status_code == 403
