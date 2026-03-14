from __future__ import annotations

import unittest

from schemas.tool_result import ToolResult
from tools import build_default_tool_registry
from tools.registry import ToolDefinition, ToolRegistry
from tools.schema import ToolFieldSchema, ToolFieldType, ToolInputSchema


def sample_tool(arguments: dict) -> ToolResult:
    return ToolResult.success("sample_tool", {"arguments": arguments})


def sample_validator(arguments: dict) -> dict:
    name = arguments.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name is required")
    return {"name": name.strip()}


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
        self.assertIsNotNone(definition.validator)
        self.assertIsNotNone(definition.input_schema)
        self.assertEqual(definition.input_schema.fields[0].name, "watchlist")
        self.assertEqual(definition.input_schema.fields[0].field_type, ToolFieldType.ARRAY)

    def test_tool_definition_validator_can_normalize_input(self) -> None:
        tool = ToolDefinition(
            name="sample_tool",
            handler=sample_tool,
            input_schema=ToolInputSchema(
                fields=(
                    ToolFieldSchema(
                        name="name",
                        field_type=ToolFieldType.STRING,
                    ),
                )
            ),
            validator=sample_validator,
        )

        validated = tool.validate_arguments({"name": "  alpha  "})

        self.assertEqual(validated, {"name": "alpha"})

    def test_default_market_snapshot_validator_rejects_empty_watchlist(self) -> None:
        registry = build_default_tool_registry()
        definition = registry.get("get_market_snapshot")

        with self.assertRaises(ValueError):
            definition.validate_arguments({"watchlist": []})

    def test_schema_rejects_unexpected_fields(self) -> None:
        tool = ToolDefinition(
            name="sample_tool",
            handler=sample_tool,
            input_schema=ToolInputSchema(
                fields=(
                    ToolFieldSchema(name="name", field_type=ToolFieldType.STRING),
                ),
            ),
        )

        with self.assertRaises(ValueError):
            tool.validate_arguments({"name": "alpha", "extra": True})


if __name__ == "__main__":
    unittest.main()
