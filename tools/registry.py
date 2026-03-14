from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from schemas.observation import JSONValue
from schemas.tool_result import ToolResult
from tools.schema import ToolInputSchema


ToolHandler = Callable[[dict[str, JSONValue]], ToolResult]
ToolValidator = Callable[[dict[str, JSONValue]], dict[str, JSONValue]]


@dataclass(slots=True, frozen=True)
class ToolDefinition:
    name: str
    handler: ToolHandler
    description: str = ""
    validator: ToolValidator | None = None
    input_schema: ToolInputSchema | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Tool name cannot be empty.")

    def validate_arguments(self, arguments: dict[str, JSONValue]) -> dict[str, JSONValue]:
        validated_arguments = arguments
        if self.input_schema is not None:
            validated_arguments = self.input_schema.validate(validated_arguments)
        if self.validator is None:
            return validated_arguments
        return self.validator(validated_arguments)


@dataclass(slots=True)
class ToolRegistry:
    _tools: dict[str, ToolDefinition] = field(default_factory=dict)

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def register_handler(
        self,
        *,
        name: str,
        handler: ToolHandler,
        description: str = "",
        validator: ToolValidator | None = None,
        input_schema: ToolInputSchema | None = None,
    ) -> None:
        self.register(
            ToolDefinition(
                name=name,
                handler=handler,
                description=description,
                validator=validator,
                input_schema=input_schema,
            )
        )

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def names(self) -> set[str]:
        return set(self._tools)

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._tools.values())
