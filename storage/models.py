from __future__ import annotations

from datetime import datetime, timezone

from schemas.decision import Decision, ToolCall
from schemas.observation import Observation, ObservationBatch
from schemas.run_log import RunLog, RunStatus
from schemas.tool_result import ToolResult, ToolResultStatus


def _parse_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def serialize_observation(observation: Observation) -> dict:
    return {
        "source": observation.source,
        "payload": observation.payload,
        "summary": observation.summary,
        "collected_at": observation.collected_at.isoformat(),
    }


def deserialize_observation(data: dict) -> Observation:
    return Observation(
        source=data["source"],
        payload=data.get("payload", {}),
        summary=data.get("summary"),
        collected_at=_parse_datetime(data.get("collected_at")),
    )


def serialize_observation_batch(batch: ObservationBatch) -> dict:
    return {
        "agent_name": batch.agent_name,
        "items": [serialize_observation(item) for item in batch.items],
        "context": batch.context,
    }


def deserialize_observation_batch(data: dict) -> ObservationBatch:
    return ObservationBatch(
        agent_name=data["agent_name"],
        items=tuple(deserialize_observation(item) for item in data.get("items", [])),
        context=data.get("context", {}),
    )


def serialize_tool_call(tool_call: ToolCall) -> dict:
    return {
        "tool_name": tool_call.tool_name,
        "arguments": tool_call.arguments,
    }


def deserialize_tool_call(data: dict) -> ToolCall:
    return ToolCall(
        tool_name=data["tool_name"],
        arguments=data.get("arguments", {}),
    )


def serialize_decision(decision: Decision) -> dict:
    return {
        "summary": decision.summary,
        "confidence": decision.confidence,
        "rationale": list(decision.rationale),
        "tool_call": serialize_tool_call(decision.tool_call) if decision.tool_call else None,
    }


def deserialize_decision(data: dict) -> Decision:
    tool_call_data = data.get("tool_call")
    return Decision(
        summary=data["summary"],
        confidence=float(data["confidence"]),
        rationale=tuple(data.get("rationale", [])),
        tool_call=deserialize_tool_call(tool_call_data) if tool_call_data else None,
    )


def serialize_tool_result(tool_result: ToolResult) -> dict:
    return {
        "tool_name": tool_result.tool_name,
        "status": tool_result.status.value,
        "output": tool_result.output,
        "error_message": tool_result.error_message,
        "completed_at": tool_result.completed_at.isoformat(),
    }


def deserialize_tool_result(data: dict) -> ToolResult:
    return ToolResult(
        tool_name=data["tool_name"],
        status=ToolResultStatus(data["status"]),
        output=data.get("output", {}),
        error_message=data.get("error_message"),
        completed_at=_parse_datetime(data.get("completed_at")) or datetime.now(timezone.utc),
    )


def serialize_run_log(run_log: RunLog) -> dict:
    return {
        "run_id": run_log.run_id,
        "agent_name": run_log.agent_name,
        "status": run_log.status.value,
        "observations": serialize_observation_batch(run_log.observations)
        if run_log.observations
        else None,
        "decision": serialize_decision(run_log.decision) if run_log.decision else None,
        "tool_result": serialize_tool_result(run_log.tool_result) if run_log.tool_result else None,
        "error_message": run_log.error_message,
        "started_at": run_log.started_at.isoformat(),
        "finished_at": run_log.finished_at.isoformat() if run_log.finished_at else None,
    }


def deserialize_run_log(data: dict) -> RunLog:
    return RunLog(
        agent_name=data["agent_name"],
        status=RunStatus(data["status"]),
        observations=deserialize_observation_batch(data["observations"])
        if data.get("observations")
        else None,
        decision=deserialize_decision(data["decision"]) if data.get("decision") else None,
        tool_result=deserialize_tool_result(data["tool_result"])
        if data.get("tool_result")
        else None,
        error_message=data.get("error_message"),
        run_id=data["run_id"],
        started_at=_parse_datetime(data.get("started_at")) or datetime.now(timezone.utc),
        finished_at=_parse_datetime(data.get("finished_at")),
    )
