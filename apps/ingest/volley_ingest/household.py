"""The household: which label is the parent, which is the child, and
where the counts go. Local, small, and the only thing `volley setup`
writes.

Nothing here is a transcript. The file holds two speaker labels, an
optional first name or nickname for the note, the timezone offset for
the day view, an optional API endpoint and key, and whether the parent
agreed to have tomorrow's one thing written into their Bee as a
reminder. Consent for that is asked once and stored as a boolean; it is
never assumed.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def home() -> Path:
    override = os.environ.get("VOLLEY_HOME")
    return Path(override) if override else Path.home() / ".volley"


@dataclass
class Household:
    parent_labels: list[str] = field(default_factory=list)
    child_labels: list[str] = field(default_factory=list)
    child_name: str | None = None
    tz_offset_hours: float = 0.0
    api_url: str | None = None
    api_key: str | None = None
    household_id: str | None = None
    mine_url: str | None = None
    write_reminders_to_bee: bool = False
    # The Bee labels every speaker "Unknown" today. Blind households have
    # their roles read from the transcript by serve_return.blind instead.
    blind: bool = False
    # Opt-in, blind only: set aside three-minute stretches with no line that
    # sounds like a child (presence.py), so adults talking do not count.
    only_with_child: bool = False
    # "childes": the bundled role model (CC BY-NC-SA 3.0, non-commercial).
    # "alternation": no trained model at all, every line a new speaker, scaled;
    # free of the corpus licence, measured worse per session (harness/blind).
    role_model: str = "childes"
    # The local time `volley setup --daily` scheduled, if any; informational.
    daily_at: str | None = None

    @property
    def ready(self) -> bool:
        return self.blind or bool(self.parent_labels and self.child_labels)

    @property
    def connected(self) -> bool:
        return bool(self.api_url and self.api_key and self.household_id)

    @staticmethod
    def path() -> Path:
        return home() / "household.json"

    @staticmethod
    def load() -> "Household | None":
        p = Household.path()
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf8"))
        return Household(**{k: v for k, v in data.items() if k in Household.__dataclass_fields__})

    def save(self) -> Path:
        p = Household.path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=1), encoding="utf8")
        return p
