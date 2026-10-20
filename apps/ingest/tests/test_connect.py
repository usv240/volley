"""`volley connect` and what `today` sends once a household is connected.

The service is replaced by a function that records every request. The
claims: connect stores the id and key and prints a link whose fragment
carries the key; `today` posts to the household's own route, with the
key in the header, and a body that holds counts and no word from the
transcript; a second connect without --again changes nothing.
"""

from __future__ import annotations

import json

from volley_ingest import cli as cli_mod
from volley_ingest.bee import BeeCli
from volley_ingest.household import Household

from test_today import NAMES, home, runner_for  # noqa: F401


def fake_service(log: list[dict]):
    def request(url: str, body: dict | None, headers: dict[str, str]) -> tuple[int, dict]:
        log.append({"url": url, "body": body, "headers": headers})
        if url.endswith("/v1/households"):
            return 200, {"household_id": "h_test1", "api_key": "vk_secret", "site_url": "https://example.test/"}
        if url.endswith("/v1/households/h_test1/days"):
            return 200, {"stored": len(body["days"])}
        return 404, {}

    return request


def test_connect_stores_the_household_and_prints_a_link_with_the_key_in_the_fragment(home, capsys, monkeypatch):
    log: list[dict] = []
    monkeypatch.setattr(cli_mod, "_request", fake_service(log))
    args = type("A", (), {"name": "ours", "api_url": None, "again": False})()
    assert cli_mod.cmd_connect(args, request=fake_service(log)) == 0
    out = capsys.readouterr().out
    h = Household.load()
    assert h.household_id == "h_test1" and h.api_key == "vk_secret"
    assert h.api_url == cli_mod.DEFAULT_API_URL
    assert h.mine_url == "https://example.test/mine/#h=h_test1&k=vk_secret"
    assert h.mine_url in out
    assert log[0]["body"] == {"name": "ours", "child_name": "Asha"}


def test_connect_twice_keeps_the_first_household_unless_asked(home, capsys):
    log: list[dict] = []
    args = type("A", (), {"name": "ours", "api_url": None, "again": False})()
    assert cli_mod.cmd_connect(args, request=fake_service(log)) == 0
    assert cli_mod.cmd_connect(args, request=fake_service(log)) == 0
    assert len(log) == 1
    assert "already connected" in capsys.readouterr().out


def test_today_posts_counts_to_the_household_route_and_no_word(home, capsys, monkeypatch):
    log: list[dict] = []
    monkeypatch.setattr(cli_mod, "_request", fake_service(log))
    args = type("A", (), {"name": "ours", "api_url": None, "again": False})()
    assert cli_mod.cmd_connect(args, request=fake_service(log)) == 0
    calls: list[list[str]] = []
    assert cli_mod.main(["today"], cli=BeeCli(runner=runner_for(calls))) == 0
    out = capsys.readouterr().out
    posts = [r for r in log if r["url"].endswith("/days")]
    assert len(posts) == 1
    post = posts[0]
    assert post["url"] == f"{cli_mod.DEFAULT_API_URL}/v1/households/h_test1/days"
    assert post["headers"] == {"x-api-key": "vk_secret"}
    body = json.dumps(post["body"])
    assert post["body"]["days"][0]["turns"] == 7
    for name in NAMES:
        assert name not in body
    for word in ("tower", "tall", "school"):
        assert word not in body.lower()
    assert "counts posted (200)" in out
    assert "see them: https://example.test/mine/#h=h_test1&k=vk_secret" in out


def test_share_prints_a_read_only_link_and_revoke_ends_it(home, capsys):
    log: list[dict] = []

    def service(url, body, headers, method="POST"):
        log.append({"url": url, "method": method, "headers": headers})
        if url.endswith("/v1/households"):
            return 200, {"household_id": "h_test1", "api_key": "vk_secret", "site_url": "https://example.test/"}
        if url.endswith("/share") and method == "POST":
            return 200, {"share_token": "vs_read", "share_url": "https://example.test/coach/#h=h_test1&s=vs_read"}
        if url.endswith("/share") and method == "DELETE":
            return 200, {"revoked": True}
        return 404, {}

    share = type("S", (), {"revoke": False})()
    assert cli_mod.cmd_share(share, request=service) == 2  # not connected yet
    cli_mod.cmd_connect(type("A", (), {"name": "ours", "api_url": None, "again": False})(), request=service)
    capsys.readouterr()
    assert cli_mod.cmd_share(share, request=service) == 0
    out = capsys.readouterr().out
    assert "https://example.test/coach/#h=h_test1&s=vs_read" in out and "vk_secret" not in out
    assert log[-1]["headers"] == {"x-api-key": "vk_secret"}
    assert cli_mod.cmd_share(type("S", (), {"revoke": True})(), request=service) == 0
    assert log[-1]["method"] == "DELETE" and "revoked" in capsys.readouterr().out
