"""The opt-in child-present rule, on the Bee itself.

    python harness/beeloop/with_child.py

`volley setup --only-with-child yes` sets aside three-minute stretches
with no line that sounds like a child (apps/ingest/volley_ingest/presence.py).
On the corpus, held out by family, it refused 70.6 percent of adults-only
stretches and lost 15.7 percent of true turns (harness/blind/presence.py).
This runs the same rule, at the threshold the product ships, on the
sessions already recorded on the operator's Bee:

  the real parent-child conversation (session 11418600, 75 true turns),
  and the three negative controls (two adults, silence, one voice).

Each set is scored by a role model that never saw that family, as
score.py and controls.py do. Only counts are written (with_child.json).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "packages" / "serve-return"))
sys.path.insert(0, str(REPO / "apps" / "ingest"))

from serve_return import Roles, Utterance, count_turns  # noqa: E402
from serve_return.blind import RoleModel, relabel  # noqa: E402
from volley_ingest.bee import normalize_conversation  # noqa: E402
from volley_ingest.presence import THRESHOLD, with_child  # noqa: E402

ROLES = Roles.of(adult=["adult"], child=["child"])
CONVERSATION = 11418600


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bee(args: str) -> dict:
    return json.loads(subprocess.run("bee " + args, shell=True, capture_output=True).stdout.decode("utf-8", "replace"))


def _utterances(cid: int) -> list[Utterance]:
    out = []
    for u in normalize_conversation(_bee(f"conversations get {cid} --json")):
        if u.start_s is not None:
            out.append(Utterance(u.start_s, "Unknown", u.text, u.end_s))
    return sorted(out, key=lambda u: u.start)


def held_out(blind_run, corpus, leave: set[str]) -> RoleModel:
    others = [n for n in corpus if n.split("/")[-1] not in leave]
    m = RoleModel().fit([blind_run.labelled(corpus[n]) for n in others])
    m.turn_scale = blind_run.learn_scale(corpus, others)
    return m


def count(us: list[Utterance], model: RoleModel) -> dict:
    kept, dropped = with_child(us, model)
    every = round(count_turns(relabel(us, model), ROLES) * model.turn_scale) if us else 0
    only = round(count_turns(relabel(kept, model), ROLES) * model.turn_scale) if kept else 0
    return {"utterances_bee": len(us), "turns_every_stretch": every, "turns_only_with_child": only, "stretches_set_aside": dropped}


def main() -> int:
    blind_run = _load(REPO / "harness" / "blind" / "run.py", "blind_run")
    corpus, _m, _s = blind_run.childes().load(REPO / "harness" / "childes" / "data" / "Gleason.zip")
    loop = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    ctl = json.loads((HERE / "controls.json").read_text(encoding="utf-8"))
    manifest = json.loads((HERE / "out" / "controls.json").read_text(encoding="utf-8"))

    rows = {}
    # The real conversation, scored by a model that never saw its family.
    model = held_out(blind_run, corpus, {loop["session"].split("/")[-1]})
    convo = [u for u in _utterances(CONVERSATION)]
    rows["parent_and_child"] = {"turns_true": loop["turns_true"], **count(convo, model)}

    # The controls, by a model that never saw either control family.
    model = held_out(blind_run, corpus, {"charlie", "susan"})
    session = [u for b in ctl["bee_sessions"] for u in _utterances(b["id"])]
    for seg in manifest["segments"]:
        a, b = seg["played_at"] - 5, seg["played_at"] + seg["seconds"] + 5
        inside = [u for u in session if a <= u.start <= b]
        rows[seg["name"]] = {"turns_true": 0, **count(inside, model)}

    result = {"threshold": THRESHOLD, "rule": "apps/ingest/volley_ingest/presence.py", "rows": rows}
    (HERE / "with_child.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for name, r in rows.items():
        print(f"  {name:16} true {r['turns_true']:3}  every stretch {r['turns_every_stretch']:3}  only with child {r['turns_only_with_child']:3}  set aside {r['stretches_set_aside']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
