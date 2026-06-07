from __future__ import annotations

import importlib
from functools import lru_cache
from pathlib import Path
from typing import Any

from NTEPilot.config.config_field import ConfigField
from NTEPilot.tools.base import ToolSpec


def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _discover_tool_specs() -> list[ToolSpec]:
    package_dir = Path(__file__).resolve().parent
    specs: list[ToolSpec] = []

    for path in package_dir.iterdir():
        if not path.is_dir():
            continue
        if path.name.startswith("_"):
            continue

        module_name = f"{__package__}.{path.name}.manifest"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue
            raise
        spec = getattr(module, "TOOL_SPEC", None)
        if not isinstance(spec, ToolSpec):
            raise TypeError(f"{module.__name__}.TOOL_SPEC must be a ToolSpec")
        specs.append(spec)

    return specs


@lru_cache(maxsize=1)
def get_tools() -> tuple[ToolSpec, ...]:
    return tuple(sorted(_discover_tool_specs(), key=lambda spec: spec.id))


def get_tool(task_id: str) -> ToolSpec:
    for tool in get_tools():
        if tool.id == task_id:
            return tool
    raise ValueError(f"Unknown task: {task_id}")


def get_task_catalog() -> list[dict[str, str]]:
    return [tool.to_task_json() for tool in get_tools()]


def get_tool_config_fields() -> list[ConfigField]:
    fields: list[ConfigField] = []
    for tool in get_tools():
        fields.extend(tool.config_fields)
    return fields


def get_tool_default_data() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for tool in get_tools():
        for field in tool.config_fields:
            if field.has_default:
                _set_path(data, field.key, field.default)
    return data
