"""The DynamoDB store against an in-memory table with the same calls.

The deployed service runs on DynamoStore and every other test runs on
MemoryStore, so a mistake in the item layout would pass the suite and
fail in production. This drives DynamoStore through the operations that
carry a key or a share, which is where a wrong pk or a dangling item
would let somebody read what they should not.
"""

from __future__ import annotations

from volley_server.store import DynamoStore


class FakeTable:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}

    def put_item(self, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)

    def get_item(self, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {"Item": dict(item)} if item else {}

    def delete_item(self, Key):
        self.items.pop((Key["pk"], Key["sk"]), None)

    def query(self, KeyConditionExpression, **_):
        # Evaluate the boto3 condition by walking its two halves:
        # pk equals, and optionally sk begins_with.
        expr = KeyConditionExpression
        parts = expr._values if expr.expression_operator == "AND" else (expr,)
        pk = next(p._values[1] for p in parts if p._values[0].name == "pk")
        prefix = next((p._values[1] for p in parts if p._values[0].name == "sk"), "")
        return {"Items": [dict(v) for (p, s), v in sorted(self.items.items()) if p == pk and s.startswith(prefix)]}

    def batch_writer(self):
        table = self

        class Batch:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def delete_item(self, Key):
                table.delete_item(Key)

        return Batch()


class FakeResource:
    def __init__(self) -> None:
        self.table = FakeTable()

    def Table(self, _name):
        return self.table


def store() -> tuple[DynamoStore, FakeTable]:
    res = FakeResource()
    return DynamoStore("t", client=res), res.table


def test_a_share_replaces_the_last_and_revoking_leaves_no_lookup():
    s, table = store()
    s.create_household("h_1", "ours", None, "keyhash")
    s.set_share("h_1", "a" * 64)
    assert s.household_id_for_share("a" * 64) == "h_1"
    s.set_share("h_1", "b" * 64)
    assert s.household_id_for_share("a" * 64) is None
    assert s.household_id_for_share("b" * 64) == "h_1"
    s.set_share("h_1", None)
    assert s.household_id_for_share("b" * 64) is None
    assert not [k for k in table.items if k[0].startswith("SHARE#")]


def test_deleting_a_household_removes_its_share_lookup():
    s, table = store()
    s.create_household("h_1", "ours", None, "keyhash")
    s.put_day("h_1", {"date": "2026-10-19", "turns": 66})
    s.set_share("h_1", "c" * 64)
    s.delete_household("h_1")
    assert s.get_household("h_1") is None and s.list_days("h_1") == []
    assert s.household_id_for_share("c" * 64) is None
