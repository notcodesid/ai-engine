from __future__ import annotations

from agents.base_agent import AgentConfig, BaseAgent
from schemas.observation import ObservationBatch


class OpportunityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            AgentConfig(
                name="opportunity-agent",
                goal="Monitor crypto signals and surface candidates for deeper analysis.",
                interval_seconds=300,
                allowed_tools=(
                    "get_market_snapshot",
                    "get_news_digest",
                    "analyze_project",
                ),
                description="First concrete agent built on the shared engine.",
            )
        )

    def observe(self) -> ObservationBatch:
        raise NotImplementedError("Observation collection will be implemented next.")
