from __future__ import annotations

import unittest

from schemas.decision import Decision, ToolCall
from schemas.observation import Observation, ObservationBatch
from schemas.run_log import RunLog, RunStatus
from schemas.tool_result import ToolResult
from storage.models import deserialize_run_log, serialize_run_log


class StorageModelTests(unittest.TestCase):
    def test_run_log_round_trip_preserves_nested_contracts(self) -> None:
        run_log = RunLog(
            agent_name="storage-agent",
            status=RunStatus.COMPLETED,
            observations=ObservationBatch(
                agent_name="storage-agent",
                items=(
                    Observation(
                        source="market",
                        payload={"watchlist": ["BTC", "ETH"]},
                        summary="Observed watchlist.",
                    ),
                ),
                context={"source_count": 1},
            ),
            decision=Decision(
                summary="Fetch market snapshot.",
                confidence=0.8,
                rationale=("Watchlist is non-empty.",),
                tool_call=ToolCall(
                    tool_name="get_market_snapshot",
                    arguments={"watchlist": ["BTC", "ETH"]},
                ),
            ),
            tool_result=ToolResult.success(
                "get_market_snapshot",
                {"asset_count": 2},
            ),
        )

        payload = serialize_run_log(run_log)
        restored = deserialize_run_log(payload)

        self.assertEqual(restored.run_id, run_log.run_id)
        self.assertEqual(restored.status, RunStatus.COMPLETED)
        self.assertEqual(restored.observations.agent_name, "storage-agent")
        self.assertEqual(restored.decision.tool_call.tool_name, "get_market_snapshot")
        self.assertEqual(restored.tool_result.output["asset_count"], 2)
