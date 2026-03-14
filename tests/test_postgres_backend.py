from __future__ import annotations

import unittest
from uuid import uuid4

import psycopg2

from engine.memory import MemoryStore
from schemas.decision import Decision, ToolCall
from schemas.observation import Observation, ObservationBatch
from schemas.run_log import RunLog, RunStatus
from schemas.tool_result import ToolResult
from storage.db import PostgresRunLogBackend


class PostgresBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.backend = PostgresRunLogBackend()
            cls.backend.initialize()
        except psycopg2.OperationalError as exc:
            raise unittest.SkipTest(f"postgres is not available: {exc}") from exc

    def test_memory_store_persists_and_reads_recent_runs(self) -> None:
        agent_name = f"postgres-agent-{uuid4()}"
        memory = MemoryStore(backend=self.backend)
        run_log = RunLog(
            agent_name=agent_name,
            status=RunStatus.COMPLETED,
            observations=ObservationBatch(
                agent_name=agent_name,
                items=(
                    Observation(
                        source="market",
                        payload={"watchlist": ["BTC"]},
                    ),
                ),
            ),
            decision=Decision(
                summary="Fetch BTC snapshot.",
                confidence=0.9,
                tool_call=ToolCall(
                    tool_name="get_market_snapshot",
                    arguments={"watchlist": ["BTC"]},
                ),
            ),
            tool_result=ToolResult.success(
                "get_market_snapshot",
                {"asset_count": 1},
            ),
        )

        memory.append_run(run_log)
        recent = memory.recent_runs(limit=10)

        matching = [stored for stored in recent if stored.run_id == run_log.run_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].agent_name, agent_name)
        self.assertEqual(matching[0].tool_result.output["asset_count"], 1)
