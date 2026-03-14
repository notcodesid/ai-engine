from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.opportunity_agent import OpportunityAgent
from engine.executor import Executor
from engine.memory import MemoryStore
from engine.planner import Planner
from engine.reasoner import OpportunityReasoner
from engine.runner import AgentRunner
from engine.scheduler import Scheduler
from storage.db import PostgresRunLogBackend
from tools import build_default_tool_registry


def main() -> None:
    backend = PostgresRunLogBackend()
    memory = MemoryStore(backend=backend)
    agent = OpportunityAgent()
    registry = build_default_tool_registry()
    runner = AgentRunner(
        reasoner=OpportunityReasoner(),
        planner=Planner(available_tools=registry.names()),
        executor=Executor(registry=registry),
        memory=memory,
    )
    scheduler = Scheduler()

    now = datetime.now(timezone.utc)
    scheduler.register(agent, start_at=now)
    run_logs = scheduler.run_due(runner, now=now)
    persisted_runs = memory.recent_runs(limit=5)

    print(f"runs executed: {len(run_logs)}")
    if run_logs:
        print(f"latest run id: {run_logs[0].run_id}")
        print(f"latest run status: {run_logs[0].status}")
    print(f"persisted run count fetched: {len(persisted_runs)}")
    for run in persisted_runs:
        print(
            f"persisted run: id={run.run_id} agent={run.agent_name} "
            f"status={run.status} started_at={run.started_at.isoformat()}"
        )


if __name__ == "__main__":
    main()
