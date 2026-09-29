"""What the service stores, and the shape that makes text impossible.

A household is a name somebody chose, an optional first name or
nickname for the child, and the hash of an API key. A day is the counts
the open-source package produced: integers and floats by the hour. A
note is the two sentences written from a day's counts, with the fact it
came from and which layer wrote it. There is no item type that carries
a transcript, and a test asserts that every stored string is one of the
few short fields named here.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone

SHORT_TEXT_FIELDS = ("name", "child_name")
MAX_SHORT_TEXT = 40


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_api_key() -> str:
    return "vk_" + secrets.token_urlsafe(24)


def key_hash(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf8")).hexdigest()


class Store:
    def create_household(self, household_id: str, name: str, child_name: str | None, key_hash_: str, simulated: bool = False) -> None:
        raise NotImplementedError

    def get_household(self, household_id: str) -> dict | None:
        raise NotImplementedError

    def household_id_for_key(self, key_hash_: str) -> str | None:
        raise NotImplementedError

    def put_day(self, household_id: str, day: dict) -> None:
        raise NotImplementedError

    def list_days(self, household_id: str) -> list[dict]:
        raise NotImplementedError

    def put_note(self, household_id: str, date: str, note: dict) -> None:
        raise NotImplementedError

    def get_note(self, household_id: str, date: str) -> dict | None:
        raise NotImplementedError

    def delete_household(self, household_id: str) -> None:
        raise NotImplementedError


class MemoryStore(Store):
    def __init__(self) -> None:
        self.households: dict[str, dict] = {}
        self.keys: dict[str, str] = {}
        self.days: dict[str, dict[str, dict]] = {}
        self.notes: dict[str, dict[str, dict]] = {}

    def create_household(self, household_id, name, child_name, key_hash_, simulated=False):
        self.households[household_id] = {
            "household_id": household_id,
            "name": name[:MAX_SHORT_TEXT],
            "child_name": (child_name or None) and child_name[:MAX_SHORT_TEXT],
            "simulated": simulated,
            "created": now_iso(),
        }
        self.keys[key_hash_] = household_id

    def get_household(self, household_id):
        return self.households.get(household_id)

    def household_id_for_key(self, key_hash_):
        return self.keys.get(key_hash_)

    def put_day(self, household_id, day):
        self.days.setdefault(household_id, {})[day["date"]] = day

    def list_days(self, household_id):
        return [self.days.get(household_id, {})[d] for d in sorted(self.days.get(household_id, {}))]

    def put_note(self, household_id, date, note):
        self.notes.setdefault(household_id, {})[date] = note

    def get_note(self, household_id, date):
        return self.notes.get(household_id, {}).get(date)

    def delete_household(self, household_id):
        self.households.pop(household_id, None)
        self.days.pop(household_id, None)
        self.notes.pop(household_id, None)
        for k, v in list(self.keys.items()):
            if v == household_id:
                del self.keys[k]


class DynamoStore(Store):
    """One on-demand table. Partition key ``HOUSEHOLD#{id}`` with sort keys
    ``META``, ``DAY#{date}``, ``NOTE#{date}``; and ``KEY#{hash}`` with sort
    key ``HOUSEHOLD`` for the key lookup. Days and notes are JSON strings,
    read back whole and never queried by field."""

    def __init__(self, table_name: str, client=None) -> None:
        import boto3  # lazy: tests never touch AWS

        self._table = (client or boto3.resource("dynamodb")).Table(table_name)

    @staticmethod
    def _pk(household_id: str) -> str:
        return f"HOUSEHOLD#{household_id}"

    def _query(self, household_id: str, prefix: str) -> list[dict]:
        from boto3.dynamodb.conditions import Key

        items: list[dict] = []
        kwargs = {"KeyConditionExpression": Key("pk").eq(self._pk(household_id)) & Key("sk").begins_with(prefix)}
        while True:
            res = self._table.query(**kwargs)
            items.extend(res.get("Items", []))
            if "LastEvaluatedKey" not in res:
                return items
            kwargs["ExclusiveStartKey"] = res["LastEvaluatedKey"]

    def create_household(self, household_id, name, child_name, key_hash_, simulated=False):
        meta = {
            "household_id": household_id,
            "name": name[:MAX_SHORT_TEXT],
            "child_name": (child_name or None) and child_name[:MAX_SHORT_TEXT],
            "simulated": simulated,
            "created": now_iso(),
        }
        self._table.put_item(Item={"pk": self._pk(household_id), "sk": "META", "body": json.dumps(meta)})
        self._table.put_item(Item={"pk": f"KEY#{key_hash_}", "sk": "HOUSEHOLD", "household_id": household_id})

    def get_household(self, household_id):
        res = self._table.get_item(Key={"pk": self._pk(household_id), "sk": "META"})
        item = res.get("Item")
        return json.loads(item["body"]) if item else None

    def household_id_for_key(self, key_hash_):
        res = self._table.get_item(Key={"pk": f"KEY#{key_hash_}", "sk": "HOUSEHOLD"})
        item = res.get("Item")
        return item["household_id"] if item else None

    def put_day(self, household_id, day):
        self._table.put_item(Item={"pk": self._pk(household_id), "sk": f"DAY#{day['date']}", "body": json.dumps(day)})

    def list_days(self, household_id):
        rows = self._query(household_id, "DAY#")
        return [json.loads(r["body"]) for r in sorted(rows, key=lambda r: r["sk"])]

    def put_note(self, household_id, date, note):
        self._table.put_item(Item={"pk": self._pk(household_id), "sk": f"NOTE#{date}", "body": json.dumps(note)})

    def get_note(self, household_id, date):
        res = self._table.get_item(Key={"pk": self._pk(household_id), "sk": f"NOTE#{date}"})
        item = res.get("Item")
        return json.loads(item["body"]) if item else None

    def delete_household(self, household_id):
        from boto3.dynamodb.conditions import Key

        rows = []
        kwargs = {"KeyConditionExpression": Key("pk").eq(self._pk(household_id))}
        while True:
            res = self._table.query(**kwargs)
            rows.extend(res.get("Items", []))
            if "LastEvaluatedKey" not in res:
                break
            kwargs["ExclusiveStartKey"] = res["LastEvaluatedKey"]
        with self._table.batch_writer() as batch:
            for r in rows:
                batch.delete_item(Key={"pk": r["pk"], "sk": r["sk"]})
