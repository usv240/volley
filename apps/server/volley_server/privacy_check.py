"""The privacy claim, shown working rather than asserted.

One request sends a day to the real intake route with everything a
transcript could carry attached: a full transcript field, the child's
words, names, a doctor, an address, an account number, and a text field
inside every hour. It then reads back what the store kept and searches
the stored row for every one of those strings.

Real: `build_app`, the production `POST /v1/households/{id}/days` route,
its `validate_day`, the store's `put_day`, and the `GET` that reads it
back, driven through FastAPI's TestClient with a real household and key.

Not real: the store. A fresh MemoryStore per request, so a visitor
pressing the button cannot write into the deployed table, and the
transcript sent here is never anywhere but this process. The page says so.
"""

from __future__ import annotations

import time
from typing import Any

SENSITIVE = {
    "a name": "Priya",
    "the child's words": "I want the red one",
    "a doctor": "Dr. Mehta",
    "a family member": "my brother Arjun",
    "an address": "14 Larkspur Lane",
    "an account number": "4472 9910",
    "a place": "Koramangala",
}

TRANSCRIPT = (
    "Priya, what did you build? I want the red one. We can ask Dr. Mehta on Tuesday, "
    "and my brother Arjun is driving from 14 Larkspur Lane. The bank rang about "
    "account 4472 9910. Then we walked to Koramangala."
)


def _day_with_text() -> dict[str, Any]:
    return {
        "date": "2026-09-29",
        "turns": 41,
        "serves_adult": 20,
        "serves_child": 15,
        "responses_within_window": 18,
        "response_latency_median_s": 1.6,
        "questions_adult": 9,
        "longest_volley": 7,
        "talk_seconds_adult": 610.5,
        "talk_seconds_child": 240.0,
        "words_discarded": 1450,
        "best_hour": 18,
        "quietest_hour_with_child": 8,
        "hours": [
            {"hour": 18, "turns": 30, "utterances_adult": 40, "utterances_child": 35, "words_discarded": 900, "text": TRANSCRIPT},
            {"hour": 8, "turns": 11, "utterances_adult": 12, "utterances_child": 9, "words_discarded": 550, "note": SENSITIVE["a name"]},
        ],
        "transcript": TRANSCRIPT,
        "child_said": SENSITIVE["the child's words"],
        "note": f"Saw {SENSITIVE['a doctor']}",
        "location": SENSITIVE["a place"],
    }


def run_privacy_check(app=None) -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from .app import build_app
    from .store import MemoryStore

    started = time.perf_counter()
    app = app or build_app(store=MemoryStore(), seed=False)
    client = TestClient(app)
    created = client.post("/v1/households", json={"name": "privacy check", "child_name": "Asha"}).json()
    hid, key = created["household_id"], created["api_key"]
    sent = _day_with_text()
    posted = client.post(f"/v1/households/{hid}/days", json={"days": [sent]}, headers={"x-api-key": key})
    stored = client.get(f"/v1/households/{hid}/days", headers={"x-api-key": key}).json()
    row = stored["days"][0] if stored.get("days") else {}
    blob = str(row)
    findings = [{"what": what, "value": value, "found": value in blob} for what, value in SENSITIVE.items()]
    strings_left = [k for k, v in row.items() if isinstance(v, str)]
    return {
        "sandbox": True,
        "sandbox_note": "a fresh in-memory store for this request; nothing written to the deployed table",
        "route": f"POST /v1/households/{{id}}/days -> GET /v1/households/{{id}}/days",
        "status": posted.status_code,
        "fields_sent": sorted(sent.keys()),
        "fields_dropped": posted.json().get("dropped_fields", []),
        "fields_stored": sorted(row.keys()),
        "strings_stored": strings_left,
        "findings": findings,
        "leaked": any(f["found"] for f in findings),
        "turns_stored": row.get("turns"),
        "ms": round((time.perf_counter() - started) * 1000, 1),
    }
