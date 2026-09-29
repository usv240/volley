"""The pressable privacy claim, checked for its own honesty.

The interesting result is an absence, so the check must be able to fail:
a version that could not notice a leak would be theatre.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from volley_server import MemoryStore, build_app
from volley_server.privacy_check import SENSITIVE, run_privacy_check


def test_the_day_is_accepted_and_every_text_field_is_dropped():
    r = run_privacy_check()
    assert r["status"] == 200
    assert {"transcript", "child_said", "note", "location"} <= set(r["fields_dropped"])
    assert r["strings_stored"] == ["date"]


def test_none_of_the_sensitive_strings_survive_and_the_counts_do():
    r = run_privacy_check()
    assert r["leaked"] is False
    assert {f["what"] for f in r["findings"]} == set(SENSITIVE)
    assert r["turns_stored"] == 41


def test_it_would_notice_if_a_word_got_through(monkeypatch):
    # Break the store on purpose: keep the raw row. The check must say leaked.
    from volley_server import app as app_module

    real = app_module.validate_day
    monkeypatch.setattr(app_module, "validate_day", lambda row: {**real(row), "transcript": row.get("transcript", "")})
    r = run_privacy_check()
    assert r["leaked"] is True


def test_it_is_a_sandbox_and_says_so_and_the_route_serves_it():
    r = run_privacy_check()
    assert r["sandbox"] is True and "in-memory" in r["sandbox_note"]
    served = TestClient(build_app(store=MemoryStore(), seed=False)).post("/v1/privacy-check").json()
    assert served["leaked"] is False and served["ms"] >= 0
