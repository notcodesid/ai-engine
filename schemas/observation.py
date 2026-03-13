from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]


def _ensure_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(slots=True, frozen=True)
class Observation:
    source: str
    payload: dict[str, JSONValue]
    summary: str | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("Observation source cannot be empty.")
        object.__setattr__(self, "collected_at", _ensure_utc(self.collected_at))


@dataclass(slots=True, frozen=True)
class ObservationBatch:
    agent_name: str
    items: tuple[Observation, ...]
    context: dict[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.agent_name.strip():
            raise ValueError("Agent name cannot be empty.")
