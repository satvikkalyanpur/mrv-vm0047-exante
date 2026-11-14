"""Tamper-evident log: a SHA-256 hash chain over inputs and results."""
from __future__ import annotations

import hashlib
import json
from typing import Any

GENESIS = "0" * 64


def _digest(record: dict[str, Any], previous: str) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")) + previous
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build_chain(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each entry stores its own hash, which covers the entry and the hash
    before it. Changing any earlier entry breaks every later hash."""
    chain, previous = [], GENESIS
    for record in records:
        h = _digest(record, previous)
        chain.append({**record, "previous_hash": previous, "hash": h})
        previous = h
    return chain


def verify_chain(chain: list[dict[str, Any]]) -> bool:
    previous = GENESIS
    for entry in chain:
        record = {k: v for k, v in entry.items() if k not in ("hash", "previous_hash")}
        if entry.get("previous_hash") != previous or entry.get("hash") != _digest(record, previous):
            return False
        previous = entry["hash"]
    return True
