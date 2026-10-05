"""The same Bedrock ladder the server's note uses, as a Strands router.

VOLLEY_MODEL_IDS (comma-separated) or VOLLEY_MODEL_ID name the rungs;
otherwise the server's default ladder. Strands' FallbackStrategy tries
them in order and drops a rung that keeps failing below the healthy
ones, which is what the server's hand-written ladder does per call.
The region follows AWS_REGION and defaults to the one the stack is in.
"""

from __future__ import annotations

import os

from strands.models import BedrockModel
from strands.models.routing import FallbackStrategy, ModelRouter, RoutingCandidate

DEFAULT_LADDER = [
    "us.anthropic.claude-sonnet-4-6",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
]


def ladder(env=None) -> list[str]:
    env = os.environ if env is None else env
    explicit = env.get("VOLLEY_MODEL_IDS")
    if explicit:
        rungs = [m.strip() for m in explicit.split(",") if m.strip()]
        if rungs:
            return rungs
    preferred = (env.get("VOLLEY_MODEL_ID") or "").strip()
    return ([preferred] if preferred else []) + [m for m in DEFAULT_LADDER if m != preferred]


def bedrock_router(env=None) -> ModelRouter:
    env = os.environ if env is None else env
    region = env.get("AWS_REGION") or env.get("AWS_DEFAULT_REGION") or "us-east-1"
    candidates = [
        RoutingCandidate(BedrockModel(model_id=m, region_name=region, temperature=0.2, max_tokens=600), name=m)
        for m in ladder(env)
    ]
    return ModelRouter(candidates, strategy=FallbackStrategy())
