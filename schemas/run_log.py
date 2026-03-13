from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from schemas.decision import Decision
from schemas.observation import ObservationBatch
from schemas.tool_result import ToolResult


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(slots=True)
class RunLog:
    agent_name: str
    status: RunStatus = RunStatus.PENDING
    observations: ObservationBatch | None = None
    decision: Decision | None = None
    tool_result: ToolResult | None = None
    error_message: str | None = None
    run_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None

    def mark_finished(self, status: RunStatus) -> None:
        self.status = status
        self.finished_at = datetime.now(timezone.utc)
