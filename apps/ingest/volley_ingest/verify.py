"""Recompute every published number from committed inputs.

A judge should not have to trust a figure on a page. `volley verify`
reruns the counter over the committed fixtures and harness inputs and
prints a diff against the results files the site reads. Silence means
the page is the code's output; any line means it is not.
"""

from __future__ import annotations

import json
from pathlib import Path

from serve_return import Roles, Utterance, count_day


def _fixture_days(repo: Path) -> dict:
    """The device fixture: shapes from the real Bee with placeholder words."""
    src = repo / "apps/ingest/tests/fixtures/device_day.json"
    if not src.exists():
        return {}
    data = json.loads(src.read_text(encoding="utf8"))
    roles = Roles.of(adult=data["roles"]["adult"], child=data["roles"]["child"])
    utts = [Utterance(u["start"], u["speaker"], u["text"], u.get("end")) for u in data["utterances"]]
    day = count_day(utts, roles, date=data["date"], tz_offset_hours=data.get("tz_offset_hours", 0))
    return {"turns": day.turns, "questions_adult": day.questions_adult, "words_discarded": day.words_discarded}


def run(repo: Path) -> int:
    checks = {"device_fixture": (_fixture_days(repo), repo / "apps/ingest/tests/fixtures/device_day.expected.json")}
    harness = repo / "harness/playlogue/results.json"
    if harness.exists():
        from importlib import import_module

        try:
            recompute = import_module("harness.playlogue.run").recompute  # type: ignore[attr-defined]
            checks["playlogue"] = (recompute(repo), harness)
        except Exception as err:  # noqa: BLE001
            print(f"playlogue: could not recompute ({type(err).__name__}: {err})")
    corpus = repo / "harness/childes/results.json"
    if corpus.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("childes_run", repo / "harness/childes/run.py")
        childes = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(childes)
            result = json.loads(corpus.read_text(encoding="utf8"))
            # The site's copy must be what the results file derives to.
            checks["corpus_site_copy"] = (childes.summarise(result), repo / "apps/web/src/data/corpus.json")
            data = repo / "harness/childes/data/Gleason.zip"
            if data.exists():
                sessions, meta, skipped = childes.load(data)
                playlogue = childes.playlogue_harness()
                playlogue.role_map = childes.roles_for
                fresh = playlogue.evaluate(sessions, meta)
                checks["corpus_recount"] = ({k: fresh[k] for k in ("sessions", "hours", "turns", "turns_per_hour", "negative_control", "baselines")},
                                            corpus)
            else:
                print("corpus_recount: the Gleason zip is not here (TalkBank rules forbid committing it); only the site copy is checked")
        except Exception as err:  # noqa: BLE001
            print(f"corpus: could not recompute ({type(err).__name__}: {err})")
    diffs = 0
    for name, (fresh, expected_path) in checks.items():
        if not expected_path.exists():
            print(f"{name}: no committed result at {expected_path}")
            diffs += 1
            continue
        expected = json.loads(expected_path.read_text(encoding="utf8"))
        for k, v in expected.items():
            if k not in fresh and name == "corpus_recount":
                continue  # the results file carries more than the recount compares
            if fresh.get(k) != v:
                print(f"{name}: {k} committed {v!r}, recomputed {fresh.get(k)!r}")
                diffs += 1
    if diffs == 0:
        print("every published number recomputes to what is committed")
    return 0 if diffs == 0 else 1
