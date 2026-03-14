from __future__ import annotations

from schemas.observation import JSONValue
from schemas.tool_result import ToolResult
from tools.registry import ToolInputValidationError


DEFAULT_MARKET_DATA: dict[str, dict[str, JSONValue]] = {
    "BTC": {"price_usd": 82000.0, "change_24h_pct": 2.1, "volume_24h_usd": 34_000_000_000},
    "ETH": {"price_usd": 4300.0, "change_24h_pct": 1.4, "volume_24h_usd": 18_500_000_000},
    "SOL": {"price_usd": 195.0, "change_24h_pct": 4.8, "volume_24h_usd": 4_200_000_000},
}


def validate_market_snapshot_arguments(arguments: dict[str, JSONValue]) -> dict[str, JSONValue]:
    watchlist_raw = arguments.get("watchlist")
    if not isinstance(watchlist_raw, list):
        raise ToolInputValidationError("'watchlist' must be provided as a list of symbols.")

    watchlist: list[str] = []
    for symbol in watchlist_raw:
        if not isinstance(symbol, str):
            raise ToolInputValidationError("Each watchlist symbol must be a string.")

        normalized = symbol.strip().upper()
        if not normalized:
            raise ToolInputValidationError("Watchlist symbols cannot be empty.")
        watchlist.append(normalized)

    if not watchlist:
        raise ToolInputValidationError("'watchlist' must contain at least one symbol.")

    return {"watchlist": watchlist}


def get_market_snapshot(arguments: dict[str, JSONValue]) -> ToolResult:
    validated_arguments = validate_market_snapshot_arguments(arguments)
    watchlist = validated_arguments["watchlist"]

    snapshot: list[dict[str, JSONValue]] = []
    for symbol in watchlist:
        metrics = DEFAULT_MARKET_DATA.get(
            symbol,
            {"price_usd": None, "change_24h_pct": None, "volume_24h_usd": None},
        )
        snapshot.append({"symbol": symbol, **metrics})

    return ToolResult.success(
        tool_name="get_market_snapshot",
        output={
            "asset_count": len(snapshot),
            "assets": snapshot,
        },
    )
