from __future__ import annotations

from dataclasses import dataclass, field

from schemas.run_log import RunLog


@dataclass(slots=True)
class MemoryStore:
    """Simple in-memory store for prior run logs."""

    run_logs: list[RunLog] = field(default_factory=list)

    def append_run(self, run_log: RunLog) -> None:
        self.run_logs.append(run_log)

    def recent_runs(self, limit: int = 10) -> tuple[RunLog, ...]:
        if limit <= 0:
            return ()
        return tuple(self.run_logs[-limit:])
