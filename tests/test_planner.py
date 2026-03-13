from __future__ import annotations

import unittest

from agents.base_agent import AgentConfig, BaseAgent
from engine.planner import Planner, PlannerPolicy, PlanningStatus
from schemas.decision import Decision, ToolCall
from schemas.observation import ObservationBatch


class DummyAgent(BaseAgent):
    def observe(self) -> ObservationBatch:
        raise NotImplementedError


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = DummyAgent(
            AgentConfig(
                name="test-agent",
                goal="Test planning behavior.",
                interval_seconds=60,
                allowed_tools=("get_market_snapshot", "analyze_project"),
            )
        )

    def test_noop_decision_returns_noop_plan(self) -> None:
        planner = Planner(available_tools={"get_market_snapshot"})
        decision = Decision(summary="Nothing to do.", confidence=0.4)

        outcome = planner.plan(self.agent, decision)

        self.assertEqual(outcome.status, PlanningStatus.NOOP)
        self.assertIsNone(outcome.tool_call)
        self.assertIsNone(outcome.blocked_reason)

    def test_allowed_registered_tool_is_approved(self) -> None:
        planner = Planner(available_tools={"get_market_snapshot"})
        decision = Decision(
            summary="Refresh market data.",
            confidence=0.7,
            tool_call=ToolCall(tool_name="get_market_snapshot", arguments={"watchlist": []}),
        )

        outcome = planner.plan(self.agent, decision)

        self.assertEqual(outcome.status, PlanningStatus.APPROVED)
        self.assertEqual(outcome.tool_call, decision.tool_call)
        self.assertIsNone(outcome.blocked_reason)

    def test_tool_not_allowed_by_agent_is_blocked(self) -> None:
        planner = Planner(available_tools={"delete_everything"})
        decision = Decision(
            summary="Attempt a forbidden tool.",
            confidence=0.9,
            tool_call=ToolCall(tool_name="delete_everything"),
        )

        outcome = planner.plan(self.agent, decision)

        self.assertEqual(outcome.status, PlanningStatus.BLOCKED)
        self.assertIn("not allowed", outcome.blocked_reason or "")
        self.assertIsNone(outcome.tool_call)

    def test_unregistered_tool_is_blocked_when_registry_is_required(self) -> None:
        planner = Planner(available_tools={"get_market_snapshot"})
        decision = Decision(
            summary="Use a missing tool.",
            confidence=0.8,
            tool_call=ToolCall(tool_name="analyze_project"),
        )

        outcome = planner.plan(self.agent, decision)

        self.assertEqual(outcome.status, PlanningStatus.BLOCKED)
        self.assertIn("not registered", outcome.blocked_reason or "")

    def test_low_confidence_tool_call_is_blocked(self) -> None:
        planner = Planner(
            available_tools={"get_market_snapshot"},
            policy=PlannerPolicy(min_tool_confidence=0.6),
        )
        decision = Decision(
            summary="Low confidence action.",
            confidence=0.4,
            tool_call=ToolCall(tool_name="get_market_snapshot"),
        )

        outcome = planner.plan(self.agent, decision)

        self.assertEqual(outcome.status, PlanningStatus.BLOCKED)
        self.assertIn("below", outcome.blocked_reason or "")


if __name__ == "__main__":
    unittest.main()
