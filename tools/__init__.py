from tools.market_data import get_market_snapshot, validate_market_snapshot_arguments
from tools.registry import ToolDefinition, ToolRegistry
from tools.schema import ToolFieldSchema, ToolFieldType, ToolInputSchema, ToolInputValidationError


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_market_snapshot",
            handler=get_market_snapshot,
            description="Return a structured local market snapshot for a watchlist.",
            validator=validate_market_snapshot_arguments,
            input_schema=ToolInputSchema(
                description="Arguments for retrieving a market snapshot.",
                fields=(
                    ToolFieldSchema(
                        name="watchlist",
                        field_type=ToolFieldType.ARRAY,
                        item_type=ToolFieldType.STRING,
                        min_items=1,
                        description="A non-empty list of asset symbols to fetch.",
                        example=["BTC", "ETH", "SOL"],
                    ),
                ),
            ),
        )
    )
    return registry


__all__ = [
    "ToolDefinition",
    "ToolFieldSchema",
    "ToolFieldType",
    "ToolInputSchema",
    "ToolInputValidationError",
    "ToolRegistry",
    "build_default_tool_registry",
    "get_market_snapshot",
    "validate_market_snapshot_arguments",
]
