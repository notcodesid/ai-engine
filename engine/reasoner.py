from __future__ import annotations

from abc import ABC, abstractmethod

from agents.base_agent import BaseAgent
from schemas.decision import Decision
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
