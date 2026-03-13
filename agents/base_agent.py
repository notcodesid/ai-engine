from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from schemas.observation import ObservationBatch


@dataclass(slots=True, frozen=True)
class AgentConfig:
    name: str
    goal: str
    interval_seconds: int
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Agent name cannot be empty.")
        if not self.goal.strip():
            raise ValueError("Agent goal cannot be empty.")
        if self.interval_seconds <= 0:
            raise ValueError("Agent interval_seconds must be positive.")


class BaseAgent(ABC):
    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    def can_use_tool(self, tool_name: str) -> bool:
        return tool_name in self.config.allowed_tools

    @abstractmethod
    def observe(self) -> ObservationBatch:
        """Collect structured observations for a single run."""
