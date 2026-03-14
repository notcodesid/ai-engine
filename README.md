# Autonomous Agent Engine

Initial scaffold for a Web4-inspired autonomous agent runtime.

## Repository Layout

- `docs/`: vision, architecture, and Web4-inspired design notes
- `engine/`: runtime loop, scheduling, reasoning, planning, execution, memory
- `agents/`: reusable agent base classes and concrete agents
- `tools/`: bounded tools agents can invoke
- `schemas/`: structured inputs and outputs for decisions and tool results
- `storage/`: persistence contracts and storage models

## Initial Goal

The first implementation target is an opportunity-scanning agent that runs on a reusable engine:

1. observe signals
2. reason over them
3. validate an action
4. execute a bounded tool
5. store the result
6. repeat

## Notes

- The engine owns control flow and safety boundaries.
- The reasoning layer only returns structured decisions.
- Trading or capital movement remains behind downstream policy and execution gates.

## Local Demo

You can run the current local prototype end-to-end without any API keys:

```bash
python3 examples/run_local_demo.py
```

What it does:

1. registers the `OpportunityAgent`
2. schedules one run immediately
3. observes a local watchlist
4. reasons over it deterministically
5. plans and executes `get_market_snapshot`
6. prints the run log and next scheduled run time

## Postgres Storage

You can run Postgres locally with Docker Compose:

```bash
docker-compose up -d postgres
```

Default database settings:

- host: `127.0.0.1`
- port: `54329`
- database: `agent_engine`
- user: `agent_engine`
- password: `agent_engine`

The engine reads these optional environment variables if you want to override them:

- `AGENT_ENGINE_DB_HOST`
- `AGENT_ENGINE_DB_PORT`
- `AGENT_ENGINE_DB_NAME`
- `AGENT_ENGINE_DB_USER`
- `AGENT_ENGINE_DB_PASSWORD`

After Postgres is up, run the persistence-backed demo:

```bash
python3 examples/run_postgres_demo.py
```

This uses the same opportunity-agent loop, but stores and reloads run logs from Postgres instead of only keeping them in memory.
