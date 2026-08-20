"""Versioned, resumable local cache for successful Phase 3 model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from institutional_investment_agents.phase3_schemas import Phase3CallSpec, RawCallRecord

CACHE_VERSION = "phase3-cache-v1"


def request_id(spec: Phase3CallSpec) -> str:
    payload = {"cache_version": CACHE_VERSION, **spec.model_dump(mode="json")}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class ResponseCache:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, identifier: str) -> Path:
        return self.root / CACHE_VERSION / f"{identifier}.json"

    def load(self, identifier: str) -> RawCallRecord | None:
        path = self.path_for(identifier)
        if not path.exists():
            return None
        return RawCallRecord.model_validate_json(path.read_text())

    def save(self, record: RawCallRecord) -> None:
        path = self.path_for(record.request_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(record.model_dump_json(indent=2) + "\n")


_SENSITIVE_KEYS = {"authorization", "api_key", "apikey", "access_token", "secret"}


def redact(value: Any) -> Any:
    """Recursively redact credentials without mutating the source object."""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        words = value.split()
        cleaned: list[str] = []
        skip_next = False
        for word in words:
            if skip_next:
                cleaned.append("[REDACTED]")
                skip_next = False
            elif word.lower() == "bearer":
                cleaned.append(word)
                skip_next = True
            elif word.startswith("sk-") and len(word) > 10:
                cleaned.append("[REDACTED]")
            else:
                cleaned.append(word)
        return " ".join(cleaned)
    return value
