from __future__ import annotations

import unittest

from agents.opportunity_agent import OpportunityAgent
from engine.executor import Executor
from engine.memory import MemoryStore
from engine.planner import Planner
from engine.reasoner import OpportunityReasoner
from engine.runner import AgentRunner
from schemas.run_log import RunStatus
from schemas.tool_result import ToolResultStatus
from tools import build_default_tool_registry


class OpportunityCycleTests(unittest.TestCase):
    def test_opportunity_agent_completes_a_real_local_cycle(self) -> None:
        agent = OpportunityAgent()
        registry = build_default_tool_registry()
        runner = AgentRunner(
            reasoner=OpportunityReasoner(),
            planner=Planner(available_tools=registry.names()),
            executor=Executor(registry=registry),
            memory=MemoryStore(),
        )

        run_log = runner.run_once(agent)

        self.assertEqual(run_log.status, RunStatus.COMPLETED)
        self.assertIsNotNone(run_log.observations)
        self.assertIsNotNone(run_log.decision)
        self.assertEqual(run_log.decision.tool_call.tool_name, "get_market_snapshot")
        self.assertIsNotNone(run_log.tool_result)
        self.assertEqual(run_log.tool_result.status, ToolResultStatus.SUCCESS)
        self.assertEqual(run_log.tool_result.output["asset_count"], 3)


if __name__ == "__main__":
    unittest.main()
