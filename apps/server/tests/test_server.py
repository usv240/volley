"""The service, driven through its routes and its MCP transport.

The three promises: counts in and nothing else; the simulated household
is public and says so; no tool and no route ever returns a word of
speech. The transport tests are the same five the sibling projects
passed, because the same client bugs are waiting.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from volley_server import MCP_PROTOCOL_VERSION, MemoryStore, build_app
from volley_server.demo import DEMO_HOUSEHOLD

H = {"mcp-protocol-version": MCP_PROTOCOL_VERSION}
NAMES = ["Priya", "Arjun", "Koramangala"]


def day(date: str = "2026-09-29", turns: int = 41, extra: dict | None = None) -> dict:
    row = {
        "date": date, "turns": turns, "serves_adult": 20, "serves_child": 15, "responses_within_window": 18,
        "response_latency_median_s": 1.6, "questions_adult": 9, "longest_volley": 7, "talk_seconds_adult": 610.5,
        "talk_seconds_child": 240.0, "words_discarded": 1450, "best_hour": 18, "quietest_hour_with_child": 8,
        "hours": [
            {"hour": 8, "turns": 11, "utterances_adult": 12, "utterances_child": 9, "words_discarded": 550, "questions_adult": 2},
            {"hour": 18, "turns": 30, "utterances_adult": 40, "utterances_child": 35, "words_discarded": 900, "questions_adult": 7},
        ],
    }
    row.update(extra or {})
    return row


@pytest.fixture
def client():
    return TestClient(build_app(store=MemoryStore(), seed=True))


@pytest.fixture
def household(client):
    made = client.post("/v1/households", json={"name": "the Vanjares", "child_name": "Asha"}).json()
    return made["household_id"], made["api_key"]


def mcp(client, body, session=None):
    headers = dict(H)
    if session:
        headers["mcp-session-id"] = session
    return client.post("/mcp", json=body, headers=headers)


def session(client) -> str:
    r = mcp(client, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}})
    assert r.status_code == 200
    s = r.headers["mcp-session-id"]
    assert mcp(client, {"jsonrpc": "2.0", "method": "notifications/initialized"}, s).status_code == 202
    return s


def call(client, s, name, args=None):
    r = mcp(client, {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": name, "arguments": args or {}}}, s)
    assert r.status_code == 200
    body = r.json()
    if "error" in body:
        return body["error"]
    return json.loads(body["result"]["content"][0]["text"])


# ---- routes -----------------------------------------------------------------


def test_the_simulated_household_is_public_and_says_so(client):
    r = client.get(f"/v1/households/{DEMO_HOUSEHOLD}/days")
    assert r.status_code == 200
    body = r.json()
    assert body["simulated"] is True and len(body["days"]) == 14
    assert all(isinstance(d["turns"], int) for d in body["days"])


def test_a_household_gets_a_key_once_and_reads_need_it(client, household):
    hid, key = household
    assert client.get(f"/v1/households/{hid}/days").status_code == 401
    r = client.get(f"/v1/households/{hid}/days", headers={"x-api-key": key})
    assert r.status_code == 200 and r.json()["days"] == []
    assert client.get(f"/v1/households/{hid}", headers={"x-api-key": key}).json()["child_name"] == "Asha"


def test_post_days_keeps_the_schema_and_drops_text_at_the_door(client, household):
    hid, key = household
    sent = day(extra={"transcript": " ".join(NAMES), "note": NAMES[0], "child_said": "I want the red one"})
    sent["hours"][0]["text"] = NAMES[1]
    r = client.post(f"/v1/households/{hid}/days", json={"days": [sent]}, headers={"x-api-key": key})
    assert r.status_code == 200
    assert set(r.json()["dropped_fields"]) == {"transcript", "note", "child_said"}
    stored = client.get(f"/v1/households/{hid}/days", headers={"x-api-key": key}).json()["days"][0]
    blob = json.dumps(stored)
    for name in NAMES + ["red one"]:
        assert name not in blob
    assert [k for k, v in stored.items() if isinstance(v, str)] == ["date"]
    assert stored["turns"] == 41 and stored["hours"][1]["turns"] == 30


def test_post_days_refuses_a_bad_row(client, household):
    hid, key = household
    assert client.post(f"/v1/households/{hid}/days", json={"days": [{"date": "yesterday", "turns": 3}]}, headers={"x-api-key": key}).status_code == 400
    assert client.post(f"/v1/households/{hid}/days", json={"days": [day(extra={"turns": "many"})]}, headers={"x-api-key": key}).status_code == 400
    assert client.post(f"/v1/households/{hid}/days", json={"days": [day()]}, headers={"x-api-key": "wrong"}).status_code == 401


def test_week_and_note_for_the_simulated_household(client):
    week = client.get(f"/v1/households/{DEMO_HOUSEHOLD}/week").json()
    assert len(week["days"]) == 7 and week["direction"] in ("up", "down", "level")
    assert week["target_turns_per_hour"] == 40 and "LENA" in week["target_source"]
    note = client.get(f"/v1/households/{DEMO_HOUSEHOLD}/note").json()
    assert note["source"] == "template" and note["fact"]["kind"] in ("quiet_hour", "slow_replies", "few_questions", "best_hour")
    assert "Asha" in note["text"]
    for word in ("delay", "behind", "risk", "percentile"):
        assert word not in note["text"].lower()


def test_the_note_uses_bedrock_when_the_phrasing_obeys_the_fact():
    def create(system, user, model):
        if "quiet_hour" in user or "best_hour" in user:
            import re

            hour = re.search(r"hour: (\d+):00 \(([^)]+)\)", user)
            value = re.search(r"value: (\S+)", user).group(1)
            return f"Around {hour.group(2)} you and Asha traded {value} turns. Tomorrow, ask one question then."
        return "Something without numbers."

    app = build_app(store=MemoryStore(), seed=True, note_deps={"create_text": create, "models": ["m1"], "enabled": True})
    note = TestClient(app).get(f"/v1/households/{DEMO_HOUSEHOLD}/note").json()
    assert note["source"] == "bedrock" and note["model"] == "m1"


def test_a_model_that_invents_a_number_is_overruled():
    app = build_app(store=MemoryStore(), seed=True, note_deps={"create_text": lambda s, u, m: "You did 999 turns and are in the 90th percentile.", "models": ["m1"], "enabled": True})
    note = TestClient(app).get(f"/v1/households/{DEMO_HOUSEHOLD}/note").json()
    assert note["source"] == "template"
    assert note["attempts"][0]["ok"] is False


def test_delete_removes_everything_and_reset_is_demo_only(client, household):
    hid, key = household
    client.post(f"/v1/households/{hid}/days", json={"days": [day()]}, headers={"x-api-key": key})
    assert client.delete(f"/v1/households/{hid}", headers={"x-api-key": key}).json()["deleted"] is True
    assert client.get(f"/v1/households/{hid}", headers={"x-api-key": key}).status_code == 404
    assert client.post(f"/v1/households/{hid}/reset").status_code == 403
    assert client.post(f"/v1/households/{DEMO_HOUSEHOLD}/reset").json()["seeded_days"] == 14


def test_schema_and_resilience_say_what_the_service_is(client):
    schema = client.get("/v1/schema").json()
    assert schema["window_seconds"] == 5 and "turns" in schema["meaning"]
    res = client.get("/api/resilience").json()
    assert res["counting"]["usesModels"] is False and res["privacy"]["textStored"] is False


# ---- MCP transport ------------------------------------------------------------


def test_initialize_issues_a_session_and_the_protocol(client):
    r = mcp(client, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}})
    assert r.status_code == 200 and r.json()["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert r.headers["mcp-session-id"]


def test_missing_unknown_and_bad_version(client):
    assert mcp(client, {"jsonrpc": "2.0", "id": 2, "method": "ping"}).status_code == 400
    assert mcp(client, {"jsonrpc": "2.0", "id": 2, "method": "ping"}, "nope").status_code == 404
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}, headers={"mcp-protocol-version": "1999-01-01"})
    assert r.status_code == 400


def test_batches_are_refused_and_notifications_are_accepted(client):
    assert mcp(client, [{"jsonrpc": "2.0", "id": 1, "method": "ping"}]).status_code == 400
    s = session(client)
    assert mcp(client, {"jsonrpc": "2.0", "method": "notifications/initialized"}, s).status_code == 202


def test_a_session_from_one_instance_is_valid_on_another(client):
    """On Lambda the next request may land on a fresh instance. The id
    is signed, so a second app built from nothing accepts it; an id
    nobody signed is still refused."""
    from fastapi.testclient import TestClient

    from volley_server.app import build_app

    s = session(client)
    other = TestClient(build_app())
    r = other.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "ping"}, headers={**H, "mcp-session-id": s})
    assert r.status_code == 200, r.text
    forged = other.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "ping"}, headers={**H, "mcp-session-id": "0123456789abcdef.000000000000000000000000"})
    assert forged.status_code == 404


def test_get_405_and_delete_lifecycle(client):
    assert client.get("/mcp").status_code == 405
    s = session(client)
    assert client.delete("/mcp", headers={"mcp-session-id": s, "content-type": "application/json"}).status_code == 204
    assert client.delete("/mcp", headers={"mcp-session-id": s}).status_code == 404
    assert mcp(client, {"jsonrpc": "2.0", "id": 3, "method": "ping"}, s).status_code == 404


def test_lists_seven_tools_and_one_returns_no_data(client):
    s = session(client)
    r = mcp(client, {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}, s)
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert len(names) == 7 and "what_volley_counts" in names
    explained = call(client, s, "what_volley_counts")
    assert explained["data"] is None and "five seconds" in explained["rule"]


def test_the_tools_answer_a_parents_questions(client):
    s = session(client)
    today = call(client, s, "how_was_our_talking_today")
    assert today["simulated"] is True and isinstance(today["turns"], int)
    one = call(client, s, "one_thing_for_tomorrow")
    assert one["source"] == "template" and one["fact"]["kind"]
    week = call(client, s, "week_trend")
    assert len(week["days"]) == 7
    best = call(client, s, "best_hour_this_week")
    assert isinstance(best["hour"], int)
    settings = call(client, s, "household_settings")
    assert settings["child_name"] == "Asha"


def test_record_day_needs_the_key_and_drops_text(client, household):
    hid, key = household
    s = session(client)
    denied = call(client, s, "record_day", {"household_id": hid, "api_key": "wrong", "day": day()})
    assert "api_key" in denied["message"]
    stored = call(client, s, "record_day", {"household_id": hid, "api_key": key, "day": day(extra={"transcript": NAMES[0]})})
    assert stored["stored"] == "2026-09-29" and stored["dropped_fields"] == ["transcript"]
    private = call(client, s, "how_was_our_talking_today", {"household_id": hid})
    assert "api_key" in private["message"]
    mine = call(client, s, "how_was_our_talking_today", {"household_id": hid, "api_key": key})
    assert mine["turns"] == 41


def test_no_tool_ever_returns_a_word_of_speech(client, household):
    hid, key = household
    client.post(f"/v1/households/{hid}/days", json={"days": [day(extra={"transcript": " ".join(NAMES)})]}, headers={"x-api-key": key})
    s = session(client)
    args = {"household_id": hid, "api_key": key}
    for name in ("how_was_our_talking_today", "one_thing_for_tomorrow", "week_trend", "best_hour_this_week", "household_settings", "what_volley_counts"):
        out = json.dumps(call(client, s, name, args if name != "what_volley_counts" else {}))
        for word in NAMES:
            assert word not in out, (name, word)


def test_unknown_tool_and_method(client):
    s = session(client)
    assert "Unknown tool" in call(client, s, "nothing")["message"]
    r = mcp(client, {"jsonrpc": "2.0", "id": 5, "method": "resources/list"}, s)
    assert r.json()["error"]["code"] == -32601


def test_a_share_reads_the_counts_and_can_do_nothing_else(client, household):
    """What a parent hands a home visitor: the days, the week and the note,
    read-only, revocable, and useless for any other household."""
    hid, key = household
    client.post(f"/v1/households/{hid}/days", json={"days": [day()]}, headers={"x-api-key": key})
    assert client.post(f"/v1/households/{hid}/share").status_code == 401
    made = client.post(f"/v1/households/{hid}/share", headers={"x-api-key": key}).json()
    token = made["share_token"]
    assert token.startswith("vs_") and "delete anything" in made["cannot"]
    s = {"x-share-token": token}

    assert client.get(f"/v1/households/{hid}/days", headers=s).json()["days"][0]["turns"] == 41
    assert client.get(f"/v1/households/{hid}/week", headers=s).status_code == 200
    assert client.get(f"/v1/households/{hid}/note", headers=s).status_code == 200

    # Read-only: the token is not a key anywhere that writes.
    assert client.post(f"/v1/households/{hid}/days", json={"days": [day("2026-09-30")]}, headers=s).status_code == 401
    assert client.post(f"/v1/households/{hid}/share", headers=s).status_code == 401
    assert client.delete(f"/v1/households/{hid}/share", headers=s).status_code == 401
    assert client.delete(f"/v1/households/{hid}", headers=s).status_code == 401

    # Bound to its own household.
    other = client.post("/v1/households", json={"name": "next door"}).json()["household_id"]
    assert client.get(f"/v1/households/{other}/days", headers=s).status_code == 401

    # A new share replaces the old; revoking ends the last.
    newer = client.post(f"/v1/households/{hid}/share", headers={"x-api-key": key}).json()["share_token"]
    assert client.get(f"/v1/households/{hid}/days", headers=s).status_code == 401
    assert client.get(f"/v1/households/{hid}/days", headers={"x-share-token": newer}).status_code == 200
    assert client.delete(f"/v1/households/{hid}/share", headers={"x-api-key": key}).json()["revoked"] is True
    assert client.get(f"/v1/households/{hid}/days", headers={"x-share-token": newer}).status_code == 401


def test_deleting_the_household_ends_its_share(client, household):
    hid, key = household
    token = client.post(f"/v1/households/{hid}/share", headers={"x-api-key": key}).json()["share_token"]
    client.delete(f"/v1/households/{hid}", headers={"x-api-key": key})
    assert client.get(f"/v1/households/{hid}/days", headers={"x-share-token": token}).status_code == 404


def test_a_note_is_phrased_once_per_fact_and_again_when_the_counts_change():
    """Every page view asks for the note; Bedrock is asked once per fact."""
    calls = []

    def create(system, user, model):
        calls.append(user)
        return "Keep going."

    store = MemoryStore()
    client = TestClient(build_app(store=store, seed=False, note_deps={"create_text": create, "models": ["m1"], "enabled": True}))
    made = client.post("/v1/households", json={"name": "ours"}).json()
    hid, k = made["household_id"], {"x-api-key": made["api_key"]}
    client.post(f"/v1/households/{hid}/days", json={"days": [day()]}, headers=k)
    first = client.get(f"/v1/households/{hid}/note", headers=k).json()
    for _ in range(3):
        assert client.get(f"/v1/households/{hid}/note", headers=k).json()["text"] == first["text"]
    assert len(calls) == 1
    client.post(f"/v1/households/{hid}/days", json={"days": [day(turns=12, extra={"best_hour": 8, "hours": [
        {"hour": 8, "turns": 12, "utterances_adult": 12, "utterances_child": 9, "words_discarded": 550, "questions_adult": 2}]})]}, headers=k)
    client.get(f"/v1/households/{hid}/note", headers=k)
    assert len(calls) == 2


def test_a_kept_note_that_fails_a_newer_rule_is_phrased_again():
    calls = []

    def create(system, user, model):
        calls.append(user)
        return "Tomorrow, ask one question at that hour."

    store = MemoryStore()
    client = TestClient(build_app(store=store, seed=False, note_deps={"create_text": create, "models": ["m1"], "enabled": True}))
    made = client.post("/v1/households", json={"name": "ours"}).json()
    hid, k = made["household_id"], {"x-api-key": made["api_key"]}
    client.post(f"/v1/households/{hid}/days", json={"days": [day()]}, headers=k)
    first = client.get(f"/v1/households/{hid}/note", headers=k).json()
    kept = store.get_note(hid, first["date"])
    store.put_note(hid, first["date"], {**kept, "text": "A lovely hour. Keep it exactly so."})
    again = client.get(f"/v1/households/{hid}/note", headers=k).json()
    assert again["text"] != "A lovely hour. Keep it exactly so." and len(calls) == 2


def test_the_week_plan_names_three_things_and_keeps_to_the_counts():
    seen = []

    def create(system, user, model):
        seen.append(user)
        if model == "bad":
            return "Around six you had 99 turns.\nGreat.\nWeekend: relax."
        return ("Around seven in the evening is your best hour: ask Asha about her day then.\n"
                "Around four in the afternoon, try naming what you are doing together.\n"
                "At the weekend, try one meal where Asha tells the story.")

    c = TestClient(build_app(store=MemoryStore(), seed=True, note_deps={"create_text": create, "models": ["bad", "good"], "enabled": True}))
    plan = c.get(f"/v1/households/{DEMO_HOUSEHOLD}/plan").json()
    assert plan["source"] == "bedrock" and plan["model"] == "good" and len(plan["lines"]) == 3
    assert plan["attempts"][0]["ok"] is False
    assert "turns a day" in seen[0] and "Asha" in seen[0]
    # Kept: asking again does not call the model again.
    c.get(f"/v1/households/{DEMO_HOUSEHOLD}/plan")
    assert len(seen) == 2


def test_the_week_plan_floor_needs_no_model():
    c = TestClient(build_app(store=MemoryStore(), seed=True))
    plan = c.get(f"/v1/households/{DEMO_HOUSEHOLD}/plan").json()
    assert plan["source"] == "template" and len(plan["lines"]) == 3
