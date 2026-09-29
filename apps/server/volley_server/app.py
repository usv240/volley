"""The Volley service.

Routes:
  GET    /healthz                             liveness
  GET    /api/resilience                      every degradation path, reported
  GET    /v1/schema                           the count fields and what each means
  POST   /v1/households                       {name, child_name?} -> household id and an API key, shown once
  GET    /v1/households/{id}                  name, child name, created; no counts
  GET    /v1/households/{id}/days             the stored counts, all that is stored
  POST   /v1/households/{id}/days             counts in, from the open-source package; the ingest target
  GET    /v1/households/{id}/week             seven days of turns and a direction
  GET    /v1/households/{id}/note?date=       one thing for tomorrow, with provenance
  DELETE /v1/households/{id}                  everything about the household, gone
  POST   /v1/privacy-check                    a day sent with a transcript attached; what survived
  POST   /v1/households/{id}/reset            re-seed the simulated household only
  /mcp                                        Model Context Protocol 2025-11-25

The API accepts counts, not text. Anyone can run the open-source
serve-return package on their own machine and post the numbers; the
transcript never leaves it. Reads of the simulated household are public;
everything else needs the household's key in X-Api-Key.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import fields as dc_fields

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from serve_return import DayCounts, HourCounts, accept, note as coach_note, pick, template
from serve_return.coach import FORBIDDEN, TARGET_TURNS_PER_HOUR

from .bedrock import MODEL_LADDER, phrase_note
from .demo import DEMO_CHILD, DEMO_HOUSEHOLD, DEMO_NAME, simulated_days
from .mcp import DISCLAIMER, register_mcp
from .store import MAX_SHORT_TEXT, MemoryStore, Store, key_hash, new_api_key

HOUR_FIELDS = tuple(f.name for f in dc_fields(HourCounts) if not f.name.startswith("_"))
DAY_FIELDS = tuple(f.name for f in dc_fields(DayCounts) if f.name not in ("hours",))
NUMERIC_DAY_FIELDS = tuple(f for f in DAY_FIELDS if f != "date")

SCHEMA = {
    "turns": "alternations between the parent and the child within five seconds, the validated count",
    "serves_adult": "exchanges the parent started",
    "serves_child": "exchanges the child started",
    "responses_within_window": "child utterances the parent answered within five seconds",
    "response_latency_median_s": "the parent's typical reply time to the child, in seconds",
    "questions_adult": "parent utterances that asked something",
    "longest_volley": "the most turns in one unbroken exchange",
    "talk_seconds_adult": "seconds the parent spoke",
    "talk_seconds_child": "seconds the child spoke",
    "utterances_adult": "parent utterances after merging runs",
    "utterances_child": "child utterances after merging runs",
    "words_discarded": "words read on the parent's machine and thrown away",
    "best_hour": "the hour with the most turns",
    "quietest_hour_with_child": "the hour with the fewest turns while the child was present",
}


def day_from_dict(d: dict) -> DayCounts:
    hours = [HourCounts(**{k: v for k, v in h.items() if k in HOUR_FIELDS}) for h in d.get("hours", [])]
    return DayCounts(hours=hours, **{k: d.get(k) for k in DAY_FIELDS})


def validate_day(row) -> dict:
    """Keep what the schema knows, refuse what is not a number, and drop
    every other field at the door, including any that could carry text."""
    if not isinstance(row, dict):
        raise HTTPException(400, "each day must be an object")
    date = row.get("date")
    if not isinstance(date, str) or len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise HTTPException(400, "date must be YYYY-MM-DD")
    if not isinstance(row.get("turns"), int):
        raise HTTPException(400, "turns must be an integer")
    clean: dict = {"date": date}
    for k in NUMERIC_DAY_FIELDS:
        v = row.get(k)
        if v is None:
            clean[k] = None if k in ("response_latency_median_s", "best_hour", "quietest_hour_with_child") else 0
        elif isinstance(v, bool) or not isinstance(v, (int, float)):
            raise HTTPException(400, f"{k} must be a number")
        else:
            clean[k] = v
    hours_in = row.get("hours") or []
    if not isinstance(hours_in, list):
        raise HTTPException(400, "hours must be a list")
    hours = []
    for h in hours_in:
        if not isinstance(h, dict) or not isinstance(h.get("hour"), int):
            raise HTTPException(400, "each hour needs an integer hour")
        hc = {}
        for k in HOUR_FIELDS:
            v = h.get(k)
            if v is None:
                hc[k] = None if k == "response_latency_median_s" else 0
            elif isinstance(v, bool) or not isinstance(v, (int, float)):
                raise HTTPException(400, f"hours.{k} must be a number")
            else:
                hc[k] = v
        hours.append(hc)
    clean["hours"] = hours
    return clean


def seed_demo(store: Store) -> int:
    if store.get_household(DEMO_HOUSEHOLD) is None:
        store.create_household(DEMO_HOUSEHOLD, DEMO_NAME, DEMO_CHILD, key_hash(secrets.token_hex(16)), simulated=True)
    rows = simulated_days()
    for r in rows:
        store.put_day(DEMO_HOUSEHOLD, r)
    return len(rows)


def week_view(days: list[dict]) -> dict:
    last = days[-7:]
    turns = [d["turns"] for d in last]
    direction = "level"
    if len(turns) >= 6:
        recent, before = sum(turns[-3:]) / 3, sum(turns[:-3]) / max(1, len(turns) - 3)
        if before > 0 and recent > before * 1.1:
            direction = "up"
        elif before > 0 and recent < before * 0.9:
            direction = "down"
    best = max(last, key=lambda d: d["turns"]) if last else None
    return {
        "days": [{"date": d["date"], "turns": d["turns"], "best_hour": d.get("best_hour")} for d in last],
        "direction": direction,
        "best_day": best["date"] if best else None,
        "target_turns_per_hour": TARGET_TURNS_PER_HOUR,
        "target_source": "LENA, Every Interaction Counts: their figure, stated as theirs",
    }


def build_app(store: Store | None = None, seed: bool = True, note_deps: dict | None = None) -> FastAPI:
    store = store or MemoryStore()
    if seed:
        seed_demo(store)

    app = FastAPI(title="Volley", version="0.1.0", docs_url="/v1/docs", openapi_url="/v1/openapi.json")
    # CORS is owned by exactly one layer: the function URL on Lambda, this
    # middleware locally. Both at once gives a browser two values.
    if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], expose_headers=["MCP-Session-Id"])
    app.state.store = store

    def household_or_404(hid: str) -> dict:
        h = store.get_household(hid)
        if h is None:
            raise HTTPException(404, "no such household")
        return h

    def require_key(request: Request, hid: str) -> None:
        key = request.headers.get("x-api-key") or ""
        if not key or store.household_id_for_key(key_hash(key)) != hid:
            raise HTTPException(401, "this household's API key is required in X-Api-Key")

    def may_read(request: Request, hid: str) -> dict:
        h = household_or_404(hid)
        if not h.get("simulated"):
            require_key(request, hid)
        return h

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "protocol": "2025-11-25", "demo_household": DEMO_HOUSEHOLD}

    @app.get("/api/resilience")
    def resilience():
        return {
            "counting": {"usesModels": False, "rationale": "The turn rule is arithmetic on times and labels. Nothing that produces a number calls a model."},
            "note": {
                "modelLadder": MODEL_LADDER,
                "onTotalFailure": "the template, which carries the same fact",
                "gate": "every digit in the note must come from the fact; forbidden words reject it",
                "enabled": os.environ.get("VOLLEY_BEDROCK") == "1",
            },
            "store": {"kind": type(store).__name__, "design": "counts by the hour; no item type can hold a transcript"},
            "privacy": {"textStored": False, "rationale": "The API accepts counts, not text. Counting runs where the transcript is."},
            "ingestion": {"paths": ["volley today (bee changed, cursor, exactly-once)", "volley today --now", "volley live (bee stream)", "a bee sync export dropped on the site"]},
        }

    @app.get("/v1/schema")
    def schema():
        return {"day": DAY_FIELDS, "hour": HOUR_FIELDS, "meaning": SCHEMA, "window_seconds": 5, "disclaimer": DISCLAIMER}

    @app.post("/v1/households")
    async def create_household(request: Request):
        body = await request.json() or {}
        name = str(body.get("name") or "").strip()[:MAX_SHORT_TEXT]
        child = (str(body.get("child_name") or "").strip() or None)
        if not name:
            raise HTTPException(400, "name is required: what you call your household")
        hid = "h_" + secrets.token_urlsafe(9)
        key = new_api_key()
        store.create_household(hid, name, child[:MAX_SHORT_TEXT] if child else None, key_hash(key))
        return {"household_id": hid, "api_key": key, "note": "the key is shown once; only its hash is stored"}

    @app.get("/v1/households/{hid}")
    def get_household(hid: str, request: Request):
        h = may_read(request, hid)
        return {k: h.get(k) for k in ("household_id", "name", "child_name", "simulated", "created")}

    @app.get("/v1/households/{hid}/days")
    def get_days(hid: str, request: Request):
        h = may_read(request, hid)
        return {"household_id": hid, "simulated": h.get("simulated", False), "days": store.list_days(hid)}

    @app.post("/v1/households/{hid}/days")
    async def post_days(hid: str, request: Request):
        household_or_404(hid)
        require_key(request, hid)
        body = await request.json()
        rows = body if isinstance(body, list) else body.get("days") if isinstance(body, dict) else None
        if not isinstance(rows, list) or not rows:
            raise HTTPException(400, 'send a list of day counts, or {"days": [...]}')
        clean = [validate_day(r) for r in rows]
        for r in clean:
            store.put_day(hid, r)
        return {"stored": len(clean), "household_id": hid, "dropped_fields": sorted({k for r in rows if isinstance(r, dict) for k in r if k not in DAY_FIELDS and k != "hours"})}

    @app.get("/v1/households/{hid}/week")
    def week(hid: str, request: Request):
        h = may_read(request, hid)
        return {"household_id": hid, "simulated": h.get("simulated", False), **week_view(store.list_days(hid))}

    @app.get("/v1/households/{hid}/note")
    def get_note(hid: str, request: Request, date: str | None = None):
        h = may_read(request, hid)
        days = store.list_days(hid)
        if not days:
            raise HTTPException(404, "no days yet")
        row = next((d for d in days if d["date"] == date), days[-1]) if date else days[-1]
        day = day_from_dict(row)
        fact = pick(day)
        floor = template(fact, h.get("child_name"))
        fact_d = {"kind": fact.kind, "hour": fact.hour, "value": fact.value, "target": fact.target}
        result = phrase_note(fact_d, h.get("child_name"), floor, lambda t: accept(t, fact), note_deps)
        record = {"date": row["date"], "fact": fact_d, **result}
        store.put_note(hid, row["date"], record)
        return {"household_id": hid, "simulated": h.get("simulated", False), **record, "disclaimer": DISCLAIMER}

    @app.delete("/v1/households/{hid}")
    def delete_household(hid: str, request: Request):
        household_or_404(hid)
        require_key(request, hid)
        store.delete_household(hid)
        return {"deleted": True}

    @app.post("/v1/privacy-check")
    def privacy_check():
        from .privacy_check import run_privacy_check

        return run_privacy_check()

    @app.post("/v1/households/{hid}/reset")
    def reset(hid: str):
        if hid != DEMO_HOUSEHOLD:
            raise HTTPException(403, "only the simulated household can be reset")
        store.delete_household(hid)
        return {"reset": True, "seeded_days": seed_demo(store)}

    @app.exception_handler(HTTPException)
    async def http_error(_req, exc: HTTPException):
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

    register_mcp(app, store, DEMO_HOUSEHOLD, note_deps)
    return app


__all__ = ["build_app", "validate_day", "seed_demo", "week_view", "day_from_dict", "FORBIDDEN", "coach_note"]
