from __future__ import annotations

from abc import ABC, abstractmethod

from agents.base_agent import BaseAgent
from schemas.decision import Decision, ToolCall
from schemas.observation import ObservationBatch
from schemas.run_log import RunLog


class BaseReasoner(ABC):
    """Produces a structured decision from observations and prior context."""

    @abstractmethod
    def decide(
        self,
        *,
        agent: BaseAgent,
        observations: ObservationBatch,
        recent_runs: tuple[RunLog, ...],
    ) -> Decision:
        """Return the next decision for the current run."""


class OpportunityReasoner(BaseReasoner):
    """Deterministic first-pass reasoner for the opportunity agent."""

    def decide(
        self,
        *,
        agent: BaseAgent,
        observations: ObservationBatch,
        recent_runs: tuple[RunLog, ...],
    ) -> Decision:
        for item in observations.items:
            watchlist = item.payload.get("watchlist")
            if item.source == "watchlist" and isinstance(watchlist, list) and watchlist:
                return Decision(
                    summary="Refresh the configured market snapshot before deeper analysis.",
                    confidence=0.85,
                    rationale=(
                        "The observation batch contains a non-empty watchlist.",
                        f"Recent run count available to the reasoner: {len(recent_runs)}.",
                    ),
                    tool_call=ToolCall(
                        tool_name="get_market_snapshot",
                        arguments={"watchlist": watchlist},
                    ),
                )

        return Decision(
            summary="No actionable observations were found.",
            confidence=0.6,
            rationale=("No watchlist observation was available for tool execution.",),
        )
