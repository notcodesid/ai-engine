from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from engine.planner import PlanOutcome, PlanningStatus
from schemas.observation import JSONValue
from schemas.tool_result import ToolResult


ToolHandler = Callable[[dict[str, JSONValue]], ToolResult]


class ExecutionStatus(StrEnum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(slots=True, frozen=True)
class ExecutionOutcome:
    status: ExecutionStatus
    plan: PlanOutcome
    tool_result: ToolResult | None = None
    message: str | None = None

    @property
    def completed(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED


@dataclass(slots=True)
class Executor:
    tools: dict[str, ToolHandler] = field(default_factory=dict)

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        self.tools[name] = handler

    def execute(self, plan: PlanOutcome) -> ExecutionOutcome:
        if plan.status == PlanningStatus.NOOP:
            return ExecutionOutcome(
                status=ExecutionStatus.SKIPPED,
                plan=plan,
                message="Planner returned noop; nothing to execute.",
            )

        if plan.status == PlanningStatus.BLOCKED:
            tool_name = plan.decision.tool_call.tool_name if plan.decision.tool_call else "blocked"
            return ExecutionOutcome(
                status=ExecutionStatus.SKIPPED,
                plan=plan,
                tool_result=ToolResult.skipped(
                    tool_name=tool_name,
                    reason=plan.blocked_reason or "Planner blocked execution.",
                ),
                message="Planner blocked execution.",
            )

        if plan.tool_call is None:
            return ExecutionOutcome(
                status=ExecutionStatus.FAILED,
                plan=plan,
                message="Approved plan is missing a tool call.",
            )

        handler = self.tools.get(plan.tool_call.tool_name)
        if handler is None:
            return ExecutionOutcome(
                status=ExecutionStatus.FAILED,
                plan=plan,
                tool_result=ToolResult.failed(
                    tool_name=plan.tool_call.tool_name,
                    error_message=f"Tool '{plan.tool_call.tool_name}' is not registered in executor.",
                ),
                message="Executor could not find a registered handler for the approved tool.",
            )

        try:
            tool_result = handler(plan.tool_call.arguments)
        except Exception as exc:
            return ExecutionOutcome(
                status=ExecutionStatus.FAILED,
                plan=plan,
                tool_result=ToolResult.failed(
                    tool_name=plan.tool_call.tool_name,
                    error_message=str(exc),
                ),
                message="Tool handler raised an exception.",
            )

        return ExecutionOutcome(
            status=ExecutionStatus.COMPLETED,
            plan=plan,
            tool_result=tool_result,
            message="Tool executed successfully.",
        )
