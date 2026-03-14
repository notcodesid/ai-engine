from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from schemas.run_log import RunLog


class RunLogBackend(Protocol):
    def initialize(self) -> None: ...

    def write_run_log(self, run_log: RunLog) -> None: ...

    def recent_runs(self, limit: int = 10) -> tuple[RunLog, ...]: ...


@dataclass(slots=True)
class MemoryStore:
    """Simple in-memory store for prior run logs."""

    backend: RunLogBackend | None = None
    run_logs: list[RunLog] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.backend is not None:
            self.backend.initialize()

    def append_run(self, run_log: RunLog) -> None:
        self.run_logs.append(run_log)
        if self.backend is not None:
            self.backend.write_run_log(run_log)

    def recent_runs(self, limit: int = 10) -> tuple[RunLog, ...]:
        if limit <= 0:
            return ()
        if self.backend is not None:
            return self.backend.recent_runs(limit)
        return tuple(self.run_logs[-limit:])
