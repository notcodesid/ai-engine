from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

from schemas.observation import JSONValue


class ToolResultStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True, frozen=True)
class ToolResult:
    tool_name: str
    status: ToolResultStatus
    output: dict[str, JSONValue] = field(default_factory=dict)
    error_message: str | None = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("Tool name cannot be empty.")

    @classmethod
    def success(cls, tool_name: str, output: dict[str, JSONValue]) -> "ToolResult":
        return cls(tool_name=tool_name, status=ToolResultStatus.SUCCESS, output=output)

    @classmethod
    def failed(cls, tool_name: str, error_message: str) -> "ToolResult":
        return cls(
            tool_name=tool_name,
            status=ToolResultStatus.FAILED,
            error_message=error_message,
        )

    @classmethod
    def skipped(cls, tool_name: str, reason: str) -> "ToolResult":
        return cls(
            tool_name=tool_name,
            status=ToolResultStatus.SKIPPED,
            error_message=reason,
        )
