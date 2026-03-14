from tools.market_data import get_market_snapshot
from tools.registry import ToolDefinition, ToolRegistry


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_market_snapshot",
            handler=get_market_snapshot,
            description="Return a structured local market snapshot for a watchlist.",
        )
    )
    return registry


__all__ = [
    "ToolDefinition",
    "ToolRegistry",
    "build_default_tool_registry",
    "get_market_snapshot",
]
