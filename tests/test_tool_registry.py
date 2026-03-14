from __future__ import annotations

import unittest

from schemas.tool_result import ToolResult
from tools import build_default_tool_registry
from tools.registry import ToolDefinition, ToolRegistry


def sample_tool(arguments: dict) -> ToolResult:
    return ToolResult.success("sample_tool", {"arguments": arguments})


class ToolRegistryTests(unittest.TestCase):
    def test_register_and_lookup_tool_definition(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="sample_tool",
            handler=sample_tool,
            description="Return arguments for testing.",
        )

        registry.register(tool)

        stored = registry.get("sample_tool")
        self.assertIsNotNone(stored)
        self.assertEqual(stored.name, "sample_tool")
        self.assertEqual(stored.description, "Return arguments for testing.")

    def test_duplicate_registration_raises(self) -> None:
        registry = ToolRegistry()
        registry.register_handler(name="sample_tool", handler=sample_tool)

        with self.assertRaises(ValueError):
            registry.register_handler(name="sample_tool", handler=sample_tool)

    def test_default_registry_contains_market_snapshot_tool(self) -> None:
        registry = build_default_tool_registry()

        self.assertIn("get_market_snapshot", registry.names())
        definition = registry.get("get_market_snapshot")
        self.assertIsNotNone(definition)
        self.assertTrue(definition.description)


if __name__ == "__main__":
    unittest.main()
