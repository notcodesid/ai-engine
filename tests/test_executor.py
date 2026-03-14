from __future__ import annotations

import unittest

from agents.base_agent import AgentConfig, BaseAgent
from engine.executor import ExecutionStatus, Executor
from engine.planner import Planner, PlanningStatus
from schemas.decision import Decision, ToolCall
from schemas.observation import ObservationBatch
from schemas.tool_result import ToolResult, ToolResultStatus
from tools.registry import ToolRegistry
from tools.schema import ToolFieldSchema, ToolFieldType, ToolInputSchema


class DummyAgent(BaseAgent):
    def observe(self) -> ObservationBatch:
        raise NotImplementedError


def successful_tool(arguments: dict) -> ToolResult:
    return ToolResult.success(
        tool_name="get_market_snapshot",
        output={"received_arguments": arguments},
    )


def crashing_tool(arguments: dict) -> ToolResult:
    raise RuntimeError(f"tool crashed for {arguments!r}")


def validating_tool(arguments: dict) -> ToolResult:
    return ToolResult.success("get_market_snapshot", {"validated_arguments": arguments})


def require_watchlist(arguments: dict) -> dict:
    watchlist = arguments.get("watchlist")
    if not isinstance(watchlist, list) or not watchlist:
        raise ValueError("watchlist is required")
    return {"watchlist": watchlist}


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = DummyAgent(
            AgentConfig(
                name="test-agent",
                goal="Test execution behavior.",
                interval_seconds=60,
                allowed_tools=("get_market_snapshot",),
            )
        )
        self.planner = Planner(available_tools={"get_market_snapshot"})
        self.registry = ToolRegistry()

    def test_noop_plan_is_skipped(self) -> None:
        decision = Decision(summary="Nothing to do.", confidence=0.5)
        plan = self.planner.plan(self.agent, decision)

        outcome = Executor(registry=self.registry).execute(plan)

        self.assertEqual(plan.status, PlanningStatus.NOOP)
        self.assertEqual(outcome.status, ExecutionStatus.SKIPPED)
        self.assertIsNone(outcome.tool_result)

    def test_blocked_plan_is_skipped_with_tool_result(self) -> None:
        decision = Decision(
            summary="Use a forbidden tool.",
            confidence=0.9,
            tool_call=ToolCall(tool_name="delete_everything"),
        )
        plan = self.planner.plan(self.agent, decision)

        outcome = Executor(registry=self.registry).execute(plan)

        self.assertEqual(plan.status, PlanningStatus.BLOCKED)
        self.assertEqual(outcome.status, ExecutionStatus.SKIPPED)
        self.assertIsNotNone(outcome.tool_result)
        self.assertEqual(outcome.tool_result.status, ToolResultStatus.SKIPPED)

    def test_approved_plan_executes_registered_handler(self) -> None:
        decision = Decision(
            summary="Fetch market snapshot.",
            confidence=0.8,
            tool_call=ToolCall(
                tool_name="get_market_snapshot",
                arguments={"watchlist": ["BTC", "ETH"]},
            ),
        )
        plan = self.planner.plan(self.agent, decision)
        self.registry.register_handler(
            name="get_market_snapshot",
            handler=successful_tool,
            description="Return the received arguments.",
        )
        executor = Executor(registry=self.registry)

        outcome = executor.execute(plan)

        self.assertEqual(plan.status, PlanningStatus.APPROVED)
        self.assertEqual(outcome.status, ExecutionStatus.COMPLETED)
        self.assertIsNotNone(outcome.tool_result)
        self.assertEqual(outcome.tool_result.status, ToolResultStatus.SUCCESS)
        self.assertEqual(
            outcome.tool_result.output["received_arguments"],
            {"watchlist": ["BTC", "ETH"]},
        )

    def test_approved_plan_with_missing_handler_fails(self) -> None:
        decision = Decision(
            summary="Fetch market snapshot.",
            confidence=0.8,
            tool_call=ToolCall(tool_name="get_market_snapshot"),
        )
        plan = self.planner.plan(self.agent, decision)

        outcome = Executor(registry=self.registry).execute(plan)

        self.assertEqual(outcome.status, ExecutionStatus.FAILED)
        self.assertIsNotNone(outcome.tool_result)
        self.assertEqual(outcome.tool_result.status, ToolResultStatus.FAILED)
        self.assertIn("not registered", outcome.tool_result.error_message or "")

    def test_tool_exception_is_captured_as_failed_result(self) -> None:
        decision = Decision(
            summary="Fetch market snapshot.",
            confidence=0.8,
            tool_call=ToolCall(
                tool_name="get_market_snapshot",
                arguments={"watchlist": ["BTC"]},
            ),
        )
        plan = self.planner.plan(self.agent, decision)
        self.registry.register_handler(
            name="get_market_snapshot",
            handler=crashing_tool,
            description="Raise an exception for testing.",
        )
        executor = Executor(registry=self.registry)

        outcome = executor.execute(plan)

        self.assertEqual(outcome.status, ExecutionStatus.FAILED)
        self.assertIsNotNone(outcome.tool_result)
        self.assertEqual(outcome.tool_result.status, ToolResultStatus.FAILED)
        self.assertIn("tool crashed", outcome.tool_result.error_message or "")

    def test_invalid_tool_arguments_fail_before_handler_runs(self) -> None:
        decision = Decision(
            summary="Fetch market snapshot.",
            confidence=0.8,
            tool_call=ToolCall(tool_name="get_market_snapshot", arguments={}),
        )
        plan = self.planner.plan(self.agent, decision)
        self.registry.register_handler(
            name="get_market_snapshot",
            handler=validating_tool,
            validator=require_watchlist,
            description="Require watchlist input.",
        )
        executor = Executor(registry=self.registry)

        outcome = executor.execute(plan)

        self.assertEqual(outcome.status, ExecutionStatus.FAILED)
        self.assertIsNotNone(outcome.tool_result)
        self.assertEqual(outcome.tool_result.status, ToolResultStatus.FAILED)
        self.assertIn("Input validation failed", outcome.tool_result.error_message or "")

    def test_schema_validation_fails_before_handler_runs(self) -> None:
        decision = Decision(
            summary="Fetch market snapshot.",
            confidence=0.8,
            tool_call=ToolCall(
                tool_name="get_market_snapshot",
                arguments={"watchlist": "BTC"},
            ),
        )
        plan = self.planner.plan(self.agent, decision)
        self.registry.register_handler(
            name="get_market_snapshot",
            handler=validating_tool,
            input_schema=ToolInputSchema(
                fields=(
                    ToolFieldSchema(
                        name="watchlist",
                        field_type=ToolFieldType.ARRAY,
                        item_type=ToolFieldType.STRING,
                        min_items=1,
                    ),
                )
            ),
            description="Require a non-empty watchlist array.",
        )
        executor = Executor(registry=self.registry)

        outcome = executor.execute(plan)

        self.assertEqual(outcome.status, ExecutionStatus.FAILED)
        self.assertIsNotNone(outcome.tool_result)
        self.assertEqual(outcome.tool_result.status, ToolResultStatus.FAILED)
        self.assertIn("must be an array", outcome.tool_result.error_message or "")


if __name__ == "__main__":
    unittest.main()
