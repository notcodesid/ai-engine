from __future__ import annotations

import os
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from schemas.run_log import RunLog
from storage.models import deserialize_run_log, serialize_run_log


CREATE_RUN_LOGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS run_logs (
    run_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    observations JSONB,
    decision JSONB,
    tool_result JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ
);
"""


@dataclass(slots=True, frozen=True)
class PostgresConfig:
    host: str = "127.0.0.1"
    port: int = 54329
    database: str = "agent_engine"
    user: str = "agent_engine"
    password: str = "agent_engine"

    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("AGENT_ENGINE_DB_HOST", "127.0.0.1"),
            port=int(os.getenv("AGENT_ENGINE_DB_PORT", "54329")),
            database=os.getenv("AGENT_ENGINE_DB_NAME", "agent_engine"),
            user=os.getenv("AGENT_ENGINE_DB_USER", "agent_engine"),
            password=os.getenv("AGENT_ENGINE_DB_PASSWORD", "agent_engine"),
        )


class PostgresRunLogBackend:
    def __init__(self, config: PostgresConfig | None = None) -> None:
        self.config = config or PostgresConfig.from_env()

    def initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_RUN_LOGS_TABLE_SQL)

    def write_run_log(self, run_log: RunLog) -> None:
        payload = serialize_run_log(run_log)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO run_logs (
                        run_id,
                        agent_name,
                        status,
                        observations,
                        decision,
                        tool_result,
                        error_message,
                        started_at,
                        finished_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        agent_name = EXCLUDED.agent_name,
                        status = EXCLUDED.status,
                        observations = EXCLUDED.observations,
                        decision = EXCLUDED.decision,
                        tool_result = EXCLUDED.tool_result,
                        error_message = EXCLUDED.error_message,
                        started_at = EXCLUDED.started_at,
                        finished_at = EXCLUDED.finished_at
                    """,
                    (
                        payload["run_id"],
                        payload["agent_name"],
                        payload["status"],
                        Json(payload["observations"]),
                        Json(payload["decision"]),
                        Json(payload["tool_result"]),
                        payload["error_message"],
                        payload["started_at"],
                        payload["finished_at"],
                    ),
                )

    def recent_runs(self, limit: int = 10) -> tuple[RunLog, ...]:
        query_limit = max(limit, 0)
        if query_limit == 0:
            return ()

        with self._connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        run_id,
                        agent_name,
                        status,
                        observations,
                        decision,
                        tool_result,
                        error_message,
                        started_at,
                        finished_at
                    FROM run_logs
                    ORDER BY started_at DESC
                    LIMIT %s
                    """,
                    (query_limit,),
                )
                rows = cursor.fetchall()

        return tuple(deserialize_run_log(dict(row)) for row in reversed(rows))

    def _connect(self):
        return psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.user,
            password=self.config.password,
            connect_timeout=5,
        )
