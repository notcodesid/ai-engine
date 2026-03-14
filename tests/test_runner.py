from __future__ import annotations

import unittest

from agents.base_agent import AgentConfig, BaseAgent
from engine.executor import Executor
from engine.memory import MemoryStore
from engine.planner import Planner
from engine.reasoner import BaseReasoner
from engine.runner import AgentRunner
from schemas.decision import Decision, ToolCall
from schemas.observation import Observation, ObservationBatch
from schemas.run_log import RunStatus
from schemas.tool_result import ToolResult, ToolResultStatus
from tools.registry import ToolRegistry


class DummyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            AgentConfig(
                name="runner-agent",
                goal="Exercise the full runner loop.",
                interval_seconds=60,
                allowed_tools=("get_market_snapshot",),
            )
        )

    def observe(self) -> ObservationBatch:
        return ObservationBatch(
            agent_name=self.name,
            items=(
                Observation(
                    source="market",
                    payload={"watchlist": ["BTC", "ETH"]},
                    summary="Initial watchlist snapshot.",
                ),
            ),
        )


class DummyReasoner(BaseReasoner):
    def __init__(self, decision: Decision) -> None:
        self._decision = decision

    def decide(
        self,
        *,
        agent: BaseAgent,
        observations: ObservationBatch,
        recent_runs: tuple,
    ) -> Decision:
        return self._decision


class CrashingReasoner(BaseReasoner):
    def decide(
        self,
        *,
        agent: BaseAgent,
        observations: ObservationBatch,
        recent_runs: tuple,
    ) -> Decision:
        raise RuntimeError("reasoner crashed")


def successful_tool(arguments: dict) -> ToolResult:
    return ToolResult.success(
        tool_name="get_market_snapshot",
        output={"received": arguments},
    )


class RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = DummyAgent()
        self.memory = MemoryStore()
        self.planner = Planner(available_tools={"get_market_snapshot"})
        registry = ToolRegistry()
        registry.register_handler(
            name="get_market_snapshot",
            handler=successful_tool,
            description="Return success for runner testing.",
        )
        self.executor = Executor(registry=registry)

    def test_successful_run_completes_and_is_stored(self) -> None:
        runner = AgentRunner(
            reasoner=DummyReasoner(
                Decision(
                    summary="Fetch market snapshot.",
                    confidence=0.8,
                    tool_call=ToolCall(
                        tool_name="get_market_snapshot",
                        arguments={"watchlist": ["BTC", "ETH"]},
                    ),
                )
            ),
            planner=self.planner,
            executor=self.executor,
            memory=self.memory,
        )

        run_log = runner.run_once(self.agent)

        self.assertEqual(run_log.status, RunStatus.COMPLETED)
        self.assertIsNotNone(run_log.tool_result)
        self.assertEqual(run_log.tool_result.status, ToolResultStatus.SUCCESS)
        self.assertEqual(len(self.memory.run_logs), 1)

    def test_blocked_run_is_marked_blocked(self) -> None:
        runner = AgentRunner(
            reasoner=DummyReasoner(
                Decision(
                    summary="Use a forbidden tool.",
                    confidence=0.9,
                    tool_call=ToolCall(tool_name="delete_everything"),
                )
            ),
            planner=self.planner,
            executor=self.executor,
            memory=self.memory,
        )

        run_log = runner.run_once(self.agent)

        self.assertEqual(run_log.status, RunStatus.BLOCKED)
        self.assertIsNotNone(run_log.tool_result)
        self.assertEqual(run_log.tool_result.status, ToolResultStatus.SKIPPED)
        self.assertIn("not allowed", run_log.error_message or "")

    def test_reasoner_exception_marks_run_failed(self) -> None:
        runner = AgentRunner(
            reasoner=CrashingReasoner(),
            planner=self.planner,
            executor=self.executor,
            memory=self.memory,
        )

        run_log = runner.run_once(self.agent)

        self.assertEqual(run_log.status, RunStatus.FAILED)
        self.assertIn("reasoner crashed", run_log.error_message or "")
        self.assertEqual(len(self.memory.run_logs), 1)


if __name__ == "__main__":
    unittest.main()
