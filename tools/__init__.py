from tools.market_data import get_market_snapshot, validate_market_snapshot_arguments
from tools.registry import ToolDefinition, ToolInputValidationError, ToolRegistry


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_market_snapshot",
            handler=get_market_snapshot,
            description="Return a structured local market snapshot for a watchlist.",
            validator=validate_market_snapshot_arguments,
        )
    )
    return registry


__all__ = [
    "ToolDefinition",
    "ToolInputValidationError",
    "ToolRegistry",
    "build_default_tool_registry",
    "get_market_snapshot",
    "validate_market_snapshot_arguments",
]
