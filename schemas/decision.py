from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from schemas.observation import JSONValue


class DecisionKind(StrEnum):
    NOOP = "noop"
    TOOL_CALL = "tool_call"


@dataclass(slots=True, frozen=True)
class ToolCall:
    tool_name: str
    arguments: dict[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("Tool name cannot be empty.")


@dataclass(slots=True, frozen=True)
class Decision:
    summary: str
    confidence: float
    rationale: tuple[str, ...] = ()
    tool_call: ToolCall | None = None

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("Decision summary cannot be empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Decision confidence must be between 0 and 1.")

    @property
    def kind(self) -> DecisionKind:
        if self.tool_call is None:
            return DecisionKind.NOOP
        return DecisionKind.TOOL_CALL
