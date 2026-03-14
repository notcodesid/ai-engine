from __future__ import annotations

from schemas.observation import JSONValue
from schemas.tool_result import ToolResult
from tools.schema import ToolInputValidationError


DEFAULT_MARKET_DATA: dict[str, dict[str, JSONValue]] = {
    "BTC": {"price_usd": 82000.0, "change_24h_pct": 2.1, "volume_24h_usd": 34_000_000_000},
    "ETH": {"price_usd": 4300.0, "change_24h_pct": 1.4, "volume_24h_usd": 18_500_000_000},
    "SOL": {"price_usd": 195.0, "change_24h_pct": 4.8, "volume_24h_usd": 4_200_000_000},
}


def validate_market_snapshot_arguments(arguments: dict[str, JSONValue]) -> dict[str, JSONValue]:
    watchlist_raw = arguments["watchlist"]
    watchlist: list[str] = []
    for symbol in watchlist_raw:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ToolInputValidationError("Watchlist symbols cannot be empty.")
        watchlist.append(normalized)

    return {"watchlist": watchlist}


def get_market_snapshot(arguments: dict[str, JSONValue]) -> ToolResult:
    watchlist = arguments["watchlist"]

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
