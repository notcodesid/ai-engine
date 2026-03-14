from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from agents.base_agent import BaseAgent
from engine.runner import AgentRunner
from schemas.run_log import RunLog, RunStatus


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(slots=True)
class SchedulerEntry:
    agent: BaseAgent
    next_run_at: datetime
    is_running: bool = False
    last_run_at: datetime | None = None
    last_status: RunStatus | None = None
    last_run_id: str | None = None


@dataclass(slots=True)
class Scheduler:
    entries: dict[str, SchedulerEntry] = field(default_factory=dict)

    def register(self, agent: BaseAgent, *, start_at: datetime | None = None) -> None:
        initial_run_at = _ensure_utc(start_at or datetime.now(timezone.utc))
        self.entries[agent.name] = SchedulerEntry(agent=agent, next_run_at=initial_run_at)

    def due_agents(self, *, now: datetime | None = None) -> tuple[BaseAgent, ...]:
        current_time = _ensure_utc(now or datetime.now(timezone.utc))
        due: list[BaseAgent] = []

        for entry in self.entries.values():
            if not entry.agent.config.enabled:
                continue
            if entry.is_running:
                continue
            if entry.next_run_at <= current_time:
                due.append(entry.agent)

        return tuple(due)

    def run_due(self, runner: AgentRunner, *, now: datetime | None = None) -> tuple[RunLog, ...]:
        current_time = _ensure_utc(now or datetime.now(timezone.utc))
        run_logs: list[RunLog] = []

        for agent in self.due_agents(now=current_time):
            entry = self.entries[agent.name]
            entry.is_running = True

            run_log = runner.run_once(agent)
            run_logs.append(run_log)

            entry.is_running = False
            entry.last_run_at = current_time
            entry.last_status = run_log.status
            entry.last_run_id = run_log.run_id
            entry.next_run_at = current_time + timedelta(seconds=agent.config.interval_seconds)

        return tuple(run_logs)
