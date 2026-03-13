# Architecture

Agent Engine

observe → reason → act → store → repeat

## Core Runtime

The engine is organized into the following layers:

1. Scheduler
2. Observation
3. Reasoner
4. Planner
5. Executor
6. Memory
7. Logging and storage

## Agent Loop

Each agent run follows the same bounded loop:

1. Scheduler triggers the run.
2. Agent collects observations.
3. Memory provides relevant prior context.
4. Reasoner returns a structured decision.
5. Planner validates the decision.
6. Executor runs the approved tool.
7. Memory and storage persist the outcome.

## Control Boundaries

- The engine owns orchestration.
- The reasoner interprets context and proposes actions.
- The planner enforces tool and parameter constraints.
- The executor only runs approved tools.
- Downstream systems retain policy, signing, and capital authority.
