"""How the Bee labels speakers on this account: a tally, nothing else.

    python harness/bee/unknown_tally.py

Reads every conversation the Bee CLI lists, counts utterances by the
speaker label the device gave them, and writes the counts to
harness/bee/unknown_tally.json. The words are read and dropped; no text,
no conversation title and no time leaves this script. It is the evidence
behind "every utterance is Unknown", which was prose until now.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "apps" / "ingest"))

from volley_ingest.bee import normalize_conversation  # noqa: E402


def bee(args: str) -> dict | None:
    """One CLI call. A reply that is not JSON (a rate limit, a transient
    error) is retried once, then skipped and counted as such."""
    for _ in range(2):
        out = subprocess.run("bee " + args, shell=True, capture_output=True).stdout.decode("utf-8", "replace")
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            continue
    return None


def main() -> int:
    # The list is paged, at most 100 a call; follow the cursor to the end.
    rows: list[dict] = []
    cursor = None
    while True:
        page = bee("conversations list --limit 100 --json" + (f" --cursor {cursor}" if cursor else ""))
        if page is None:
            break
        rows.extend(page.get("conversations", page) if isinstance(page, dict) else page)
        cursor = page.get("next_cursor") if isinstance(page, dict) else None
        if not cursor:
            break
    labels: Counter[str] = Counter()
    sessions = 0
    skipped = 0
    for c in rows:
        raw = bee(f"conversations get {c['id']} --json")
        if raw is None:
            skipped += 1
            continue
        us = normalize_conversation(raw)
        if not us:
            continue
        sessions += 1
        for u in us:
            labels[u.speaker or "(none)"] += 1
    total = sum(labels.values())
    result = {"date": date.today().isoformat(), "cli": "@beeai/cli", "sessions_with_utterances": sessions,
              "utterances": total, "by_speaker_label": dict(labels), "sessions_skipped_non_json_reply": skipped,
              "unknown_share_pct": round(100 * labels.get("Unknown", 0) / total, 1) if total else None,
              "note": "counts only; no text, title or time was kept"}
    (HERE / "unknown_tally.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"{sessions} sessions ({skipped} skipped), {total} utterances: {dict(labels)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
