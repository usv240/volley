"""Importable app for uvicorn locally and Mangum on Lambda.

    uvicorn volley_server.main:app --port 8791

The store is chosen by environment: VOLLEY_TABLE selects DynamoDB,
otherwise memory, which reseeds the simulated household on each start.
"""

from __future__ import annotations

import os

from .app import build_app
from .store import DynamoStore, MemoryStore

table = os.environ.get("VOLLEY_TABLE")
store = DynamoStore(table) if table else MemoryStore()
app = build_app(store=store)
