from app.store import ActionStore


def test_payload_hash_is_stable():
    a = ActionStore.hash_payload({"b": 2, "a": 1})
    b = ActionStore.hash_payload({"a": 1, "b": 2})
    assert a == b
