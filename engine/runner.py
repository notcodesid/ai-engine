from __future__ import annotations

from dataclasses import dataclass

from agents.base_agent import BaseAgent
from engine.executor import ExecutionStatus, Executor
from engine.memory import MemoryStore
from engine.planner import Planner, PlanningStatus
from engine.reasoner import BaseReasoner
from schemas.run_log import RunLog, RunStatus


@dataclass(slots=True)
class AgentRunner:
    reasoner: BaseReasoner
    planner: Planner
    executor: Executor
    memory: MemoryStore

    def run_once(self, agent: BaseAgent) -> RunLog:
        run_log = RunLog(agent_name=agent.name, status=RunStatus.RUNNING)

        try:
            observations = agent.observe()
            run_log.observations = observations

            decision = self.reasoner.decide(
                agent=agent,
                observations=observations,
                recent_runs=self.memory.recent_runs(),
            )
            run_log.decision = decision

            plan = self.planner.plan(agent, decision)
            execution = self.executor.execute(plan)
            run_log.tool_result = execution.tool_result

            if plan.status == PlanningStatus.BLOCKED:
                run_log.error_message = plan.blocked_reason
                run_log.mark_finished(RunStatus.BLOCKED)
            elif execution.status == ExecutionStatus.FAILED:
                run_log.error_message = execution.message
                run_log.mark_finished(RunStatus.FAILED)
            else:
                run_log.mark_finished(RunStatus.COMPLETED)
        except Exception as exc:
            run_log.error_message = str(exc)
            run_log.mark_finished(RunStatus.FAILED)

        self.memory.append_run(run_log)
        return run_log
