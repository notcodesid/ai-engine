from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from agents.base_agent import AgentConfig, BaseAgent
from engine.executor import Executor
from engine.memory import MemoryStore
from engine.planner import Planner
from engine.reasoner import BaseReasoner
from engine.runner import AgentRunner
from engine.scheduler import Scheduler
from schemas.decision import Decision, ToolCall
from schemas.observation import Observation, ObservationBatch
from schemas.run_log import RunStatus
from schemas.tool_result import ToolResult
from tools.registry import ToolRegistry


class DueAgent(BaseAgent):
    def __init__(self, *, enabled: bool = True, interval_seconds: int = 60) -> None:
        super().__init__(
            AgentConfig(
                name="scheduled-agent",
                goal="Exercise scheduler behavior.",
                interval_seconds=interval_seconds,
                allowed_tools=("get_market_snapshot",),
                enabled=enabled,
            )
        )

    def observe(self) -> ObservationBatch:
        return ObservationBatch(
            agent_name=self.name,
            items=(
                Observation(
                    source="watchlist",
                    payload={"watchlist": ["BTC"]},
                ),
            ),
        )


class StaticReasoner(BaseReasoner):
    def decide(
        self,
        *,
        agent: BaseAgent,
        observations: ObservationBatch,
        recent_runs: tuple,
    ) -> Decision:
        return Decision(
            summary="Fetch market snapshot.",
            confidence=0.9,
            tool_call=ToolCall(
                tool_name="get_market_snapshot",
                arguments={"watchlist": ["BTC"]},
            ),
        )


def successful_tool(arguments: dict) -> ToolResult:
    return ToolResult.success("get_market_snapshot", {"received": arguments})


class SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_time = datetime(2026, 3, 14, 10, 0, tzinfo=timezone.utc)
        self.agent = DueAgent()
        registry = ToolRegistry()
        registry.register_handler(
            name="get_market_snapshot",
            handler=successful_tool,
            description="Return scheduler test data.",
        )
        self.runner = AgentRunner(
            reasoner=StaticReasoner(),
            planner=Planner(available_tools={"get_market_snapshot"}),
            executor=Executor(registry=registry),
            memory=MemoryStore(),
        )

    def test_register_and_due_agents_returns_due_agent(self) -> None:
        scheduler = Scheduler()
        scheduler.register(self.agent, start_at=self.base_time)

        due = scheduler.due_agents(now=self.base_time)

        self.assertEqual(tuple(agent.name for agent in due), ("scheduled-agent",))

    def test_disabled_agent_is_not_due(self) -> None:
        scheduler = Scheduler()
        scheduler.register(DueAgent(enabled=False), start_at=self.base_time)

        due = scheduler.due_agents(now=self.base_time)

        self.assertEqual(due, ())

    def test_running_agent_is_not_due(self) -> None:
        scheduler = Scheduler()
        scheduler.register(self.agent, start_at=self.base_time)
        scheduler.entries[self.agent.name].is_running = True

        due = scheduler.due_agents(now=self.base_time)

        self.assertEqual(due, ())

    def test_run_due_executes_agent_and_schedules_next_run(self) -> None:
        scheduler = Scheduler()
        scheduler.register(self.agent, start_at=self.base_time)

        run_logs = scheduler.run_due(self.runner, now=self.base_time)

        self.assertEqual(len(run_logs), 1)
        self.assertEqual(run_logs[0].status, RunStatus.COMPLETED)
        entry = scheduler.entries[self.agent.name]
        self.assertFalse(entry.is_running)
        self.assertEqual(entry.last_status, RunStatus.COMPLETED)
        self.assertEqual(
            entry.next_run_at,
            self.base_time + timedelta(seconds=self.agent.config.interval_seconds),
        )

    def test_run_due_skips_agents_not_yet_due(self) -> None:
        scheduler = Scheduler()
        scheduler.register(self.agent, start_at=self.base_time + timedelta(minutes=5))

        run_logs = scheduler.run_due(self.runner, now=self.base_time)

        self.assertEqual(run_logs, ())
        self.assertIsNone(scheduler.entries[self.agent.name].last_status)


if __name__ == "__main__":
    unittest.main()
