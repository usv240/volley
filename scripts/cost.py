"""What one family costs to run for a month, at AWS list prices, from measured usage.

    python scripts/cost.py

Every input is either an AWS list price or something measured on the
deployed stack, and each says which. The usage pattern is stated, and it
is generous: the parent opens their page every day, a coach opens the
shared page every week, every view downloads the whole site as if
nothing were cached, and the AWS free tier is ignored. Writes
docs/cost.json, which the evidence and the Devpost quote.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# AWS Price List API (pricing:GetProducts), us-east-1, read 2026-10-20.
PRICE = {
    "dynamodb_write_unit": 0.625 / 1e6,       # on-demand, per write request unit
    "dynamodb_read_unit": 0.125 / 1e6,        # on-demand, per read request unit
    "lambda_request": 0.20 / 1e6,             # x86, per request
    "lambda_gb_second": 0.0000166667,         # x86, first tier
    "bedrock_input_token": 3.30 / 1e6,        # Claude Sonnet 4.6, us. cross-region profile
    "bedrock_output_token": 16.50 / 1e6,
    "cloudfront_gb": 0.085,                   # United States, first 10 TB
    "cloudfront_request": 0.01 / 1e4,         # HTTPS, United States
}

# Measured on the deployed stack, 2026-10-20.
MEASURED = {
    "lambda_memory_gb": 0.5,                  # the function's configuration
    "lambda_avg_seconds": 0.471,              # CloudWatch REPORT lines, 14 days, 79 invocations; includes cold starts and Bedrock waits
    "note_input_tokens": 239,                 # one real note on the deployed model
    "note_output_tokens": 35,
    "page_api_requests": 4,                   # /mine and /coach: household, days, week, note (headless browser)
    "page_cdn_requests": 14,
    "page_cdn_bytes": 594_325,
}

# The pattern, per family, per 30-day month.
USAGE = {"days_posted": 30, "parent_views": 30, "coach_views": 4, "notes_phrased": 30}


def day_bytes() -> int:
    """The largest day in the committed simulated household: full days,
    every hour present, so larger than the one-hour day on the real Bee."""
    demo = json.loads((REPO / "apps/web/src/data/demo.json").read_text(encoding="utf-8"))
    return max(len(json.dumps(d)) for d in demo["days"])


def month() -> dict:
    b = day_bytes()
    write_units_per_day = math.ceil(b / 1024)
    month_of_days_kb = USAGE["days_posted"] * b / 1024
    # Eventually consistent reads: half a unit per 4 KB.
    read_query = max(0.5, math.ceil(month_of_days_kb / 4) * 0.5)
    read_small = 0.5
    # A view: household (meta + key or share lookup), days, week, note (stored note + days).
    reads_per_view = (read_small * 2) + (read_small + read_query) * 2 + (read_small * 2 + read_query)
    views = USAGE["parent_views"] + USAGE["coach_views"]
    requests = USAGE["days_posted"] + views * MEASURED["page_api_requests"]

    dynamodb = (USAGE["days_posted"] * write_units_per_day + USAGE["notes_phrased"]) * PRICE["dynamodb_write_unit"] \
        + views * reads_per_view * PRICE["dynamodb_read_unit"]
    lam = requests * (PRICE["lambda_request"] + MEASURED["lambda_memory_gb"] * MEASURED["lambda_avg_seconds"] * PRICE["lambda_gb_second"])
    bedrock = USAGE["notes_phrased"] * (MEASURED["note_input_tokens"] * PRICE["bedrock_input_token"]
                                        + MEASURED["note_output_tokens"] * PRICE["bedrock_output_token"])
    cdn = views * (MEASURED["page_cdn_bytes"] / 1e9 * PRICE["cloudfront_gb"] + MEASURED["page_cdn_requests"] * PRICE["cloudfront_request"])
    parts = {"dynamodb": dynamodb, "lambda": lam, "bedrock": bedrock, "cloudfront": cdn}
    total = sum(parts.values())
    return {
        "per_family_per_month_usd": round(total, 4),
        "cents": round(100 * total, 1),
        "families_per_dollar_month": int(1 / total),
        "parts_usd": {k: round(v, 5) for k, v in parts.items()},
        "usage": USAGE,
        "measured": {**MEASURED, "day_bytes": b},
        "prices": "AWS Price List API, us-east-1, 2026-10-20; free tier ignored",
        "not_counted": "the Bee (49.99 dollars once, the family's) and the family's own computer, where the counting runs",
    }


if __name__ == "__main__":
    m = month()
    (REPO / "docs/cost.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(f"{m['cents']} cents per family per month ({m['families_per_dollar_month']} families per dollar)")
    for k, v in m["parts_usd"].items():
        print(f"  {k:10} ${v:.5f}")
