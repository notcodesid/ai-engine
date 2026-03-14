from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from schemas.observation import JSONValue


class ToolInputValidationError(ValueError):
    """Raised when tool arguments fail validation."""


class ToolFieldType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass(slots=True, frozen=True)
class ToolFieldSchema:
    name: str
    field_type: ToolFieldType
    description: str = ""
    required: bool = True
    example: JSONValue | None = None
    item_type: ToolFieldType | None = None
    min_items: int | None = None
    allow_empty_string: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Tool field name cannot be empty.")
        if self.field_type != ToolFieldType.ARRAY and self.item_type is not None:
            raise ValueError("item_type can only be set for array fields.")

    def validate(self, value: JSONValue) -> JSONValue:
        if self.field_type == ToolFieldType.STRING:
            if not isinstance(value, str):
                raise ToolInputValidationError(f"Field '{self.name}' must be a string.")
            if not self.allow_empty_string and not value.strip():
                raise ToolInputValidationError(f"Field '{self.name}' cannot be empty.")
            return value

        if self.field_type == ToolFieldType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ToolInputValidationError(f"Field '{self.name}' must be an integer.")
            return value

        if self.field_type == ToolFieldType.NUMBER:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ToolInputValidationError(f"Field '{self.name}' must be a number.")
            return value

        if self.field_type == ToolFieldType.BOOLEAN:
            if not isinstance(value, bool):
                raise ToolInputValidationError(f"Field '{self.name}' must be a boolean.")
            return value

        if self.field_type == ToolFieldType.OBJECT:
            if not isinstance(value, dict):
                raise ToolInputValidationError(f"Field '{self.name}' must be an object.")
            return value

        if self.field_type == ToolFieldType.ARRAY:
            if not isinstance(value, list):
                raise ToolInputValidationError(f"Field '{self.name}' must be an array.")
            if self.min_items is not None and len(value) < self.min_items:
                raise ToolInputValidationError(
                    f"Field '{self.name}' must contain at least {self.min_items} item(s)."
                )
            if self.item_type is not None:
                for index, item in enumerate(value):
                    self._validate_array_item(index, item)
            return value

        raise ToolInputValidationError(f"Unsupported field type '{self.field_type}'.")

    def _validate_array_item(self, index: int, item: JSONValue) -> None:
        if self.item_type == ToolFieldType.STRING:
            if not isinstance(item, str):
                raise ToolInputValidationError(
                    f"Field '{self.name}' item {index} must be a string."
                )
            return

        if self.item_type == ToolFieldType.INTEGER:
            if not isinstance(item, int) or isinstance(item, bool):
                raise ToolInputValidationError(
                    f"Field '{self.name}' item {index} must be an integer."
                )
            return

        if self.item_type == ToolFieldType.NUMBER:
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                raise ToolInputValidationError(
                    f"Field '{self.name}' item {index} must be a number."
                )
            return

        if self.item_type == ToolFieldType.BOOLEAN:
            if not isinstance(item, bool):
                raise ToolInputValidationError(
                    f"Field '{self.name}' item {index} must be a boolean."
                )
            return

        if self.item_type == ToolFieldType.OBJECT:
            if not isinstance(item, dict):
                raise ToolInputValidationError(
                    f"Field '{self.name}' item {index} must be an object."
                )
            return

        if self.item_type == ToolFieldType.ARRAY:
            if not isinstance(item, list):
                raise ToolInputValidationError(
                    f"Field '{self.name}' item {index} must be an array."
                )
            return


@dataclass(slots=True, frozen=True)
class ToolInputSchema:
    fields: tuple[ToolFieldSchema, ...]
    description: str = ""
    allow_extra_fields: bool = False

    def validate(self, arguments: dict[str, JSONValue]) -> dict[str, JSONValue]:
        validated: dict[str, JSONValue] = {}
        field_map = {field.name: field for field in self.fields}

        for field in self.fields:
            if field.name not in arguments:
                if field.required:
                    raise ToolInputValidationError(
                        f"Missing required field '{field.name}'."
                    )
                continue
            validated[field.name] = field.validate(arguments[field.name])

        if not self.allow_extra_fields:
            extra_fields = sorted(set(arguments) - set(field_map))
            if extra_fields:
                raise ToolInputValidationError(
                    f"Unexpected field(s): {', '.join(extra_fields)}."
                )
        else:
            for name, value in arguments.items():
                if name not in validated:
                    validated[name] = value

        return validated
