from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from agents.base_agent import BaseAgent
from schemas.decision import Decision, ToolCall


class PlanningStatus(StrEnum):
    NOOP = "noop"
    APPROVED = "approved"
    BLOCKED = "blocked"


@dataclass(slots=True, frozen=True)
class PlannerPolicy:
    min_tool_confidence: float = 0.0
    require_registered_tool: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_tool_confidence <= 1.0:
            raise ValueError("Planner min_tool_confidence must be between 0 and 1.")


@dataclass(slots=True, frozen=True)
class PlanOutcome:
    agent_name: str
    status: PlanningStatus
    decision: Decision
    tool_call: ToolCall | None = None
    blocked_reason: str | None = None

    @property
    def approved(self) -> bool:
        return self.status == PlanningStatus.APPROVED


class Planner:
    """Validates a reasoner decision before any tool execution happens."""

    def __init__(
        self,
        *,
        available_tools: set[str] | None = None,
        policy: PlannerPolicy | None = None,
    ) -> None:
        self.available_tools = available_tools or set()
        self.policy = policy or PlannerPolicy()

    def plan(self, agent: BaseAgent, decision: Decision) -> PlanOutcome:
        if decision.tool_call is None:
            return PlanOutcome(
                agent_name=agent.name,
                status=PlanningStatus.NOOP,
                decision=decision,
            )

        tool_call = decision.tool_call

        if decision.confidence < self.policy.min_tool_confidence:
            return self._blocked(
                agent=agent,
                decision=decision,
                reason=(
                    f"Decision confidence {decision.confidence:.2f} is below "
                    f"the planner threshold {self.policy.min_tool_confidence:.2f}."
                ),
            )

        if not agent.can_use_tool(tool_call.tool_name):
            return self._blocked(
                agent=agent,
                decision=decision,
                reason=f"Agent '{agent.name}' is not allowed to use '{tool_call.tool_name}'.",
            )

        if self.policy.require_registered_tool and tool_call.tool_name not in self.available_tools:
            return self._blocked(
                agent=agent,
                decision=decision,
                reason=f"Tool '{tool_call.tool_name}' is not registered in the planner.",
            )

        return PlanOutcome(
            agent_name=agent.name,
            status=PlanningStatus.APPROVED,
            decision=decision,
            tool_call=tool_call,
        )

    def _blocked(self, *, agent: BaseAgent, decision: Decision, reason: str) -> PlanOutcome:
        return PlanOutcome(
            agent_name=agent.name,
            status=PlanningStatus.BLOCKED,
            decision=decision,
            blocked_reason=reason,
        )
