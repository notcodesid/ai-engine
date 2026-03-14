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
from tools.market_data import get_market_snapshot


def main() -> None:
    agent = OpportunityAgent()
    memory = MemoryStore()
    runner = AgentRunner(
        reasoner=OpportunityReasoner(),
        planner=Planner(available_tools={"get_market_snapshot"}),
        executor=Executor({"get_market_snapshot": get_market_snapshot}),
        memory=memory,
    )
    scheduler = Scheduler()

    now = datetime.now(timezone.utc)
    scheduler.register(agent, start_at=now)
    run_logs = scheduler.run_due(runner, now=now)

    print(f"registered agent: {agent.name}")
    print(f"scheduled at: {now.isoformat()}")
    print(f"runs executed: {len(run_logs)}")

    if not run_logs:
        print("no runs were due")
        return

    run_log = run_logs[0]
    print(f"run id: {run_log.run_id}")
    print(f"run status: {run_log.status}")

    if run_log.observations is not None:
        print(f"observation count: {len(run_log.observations.items)}")
        for observation in run_log.observations.items:
            print(
                "observation:"
                f" source={observation.source}"
                f" summary={observation.summary!r}"
                f" payload={observation.payload}"
            )

    if run_log.decision is not None:
        print(f"decision summary: {run_log.decision.summary}")
        print(f"decision confidence: {run_log.decision.confidence}")
        print(f"decision rationale: {list(run_log.decision.rationale)}")
        if run_log.decision.tool_call is not None:
            print(f"tool name: {run_log.decision.tool_call.tool_name}")
            print(f"tool arguments: {run_log.decision.tool_call.arguments}")

    if run_log.tool_result is not None:
        print(f"tool result status: {run_log.tool_result.status}")
        print(f"tool output: {run_log.tool_result.output}")
        if run_log.tool_result.error_message is not None:
            print(f"tool error: {run_log.tool_result.error_message}")

    next_run_at = scheduler.entries[agent.name].next_run_at
    print(f"next run at: {next_run_at.isoformat()}")
    print(f"memory run count: {len(memory.run_logs)}")


if __name__ == "__main__":
    main()
