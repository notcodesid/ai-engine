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
from tools.market_data import get_market_snapshot


class OpportunityCycleTests(unittest.TestCase):
    def test_opportunity_agent_completes_a_real_local_cycle(self) -> None:
        agent = OpportunityAgent()
        runner = AgentRunner(
            reasoner=OpportunityReasoner(),
            planner=Planner(available_tools={"get_market_snapshot"}),
            executor=Executor({"get_market_snapshot": get_market_snapshot}),
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
