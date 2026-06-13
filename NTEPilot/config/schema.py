from __future__ import annotations

import copy
import importlib
from collections.abc import Iterator
from typing import Any, Literal

from NTEPilot.config.framework import CONFIG

TaskSection = Literal["tools", "schedule"]
SCHEDULER_DEFAULTS = {
    "enabled": False,
    "plans": [],
}

def iter_config_fields() -> Iterator[tuple[str, str, dict[str, Any]]]:
    for section in ("general", "team"):
        for key, field in CONFIG[section].items():
            yield f"{section}.{key}", section, field

    for section in ("tools", "schedule"):
        for task_id, task in CONFIG[section].items():
            group = task_id if section == "tools" else f"schedule.{task_id}"
            for key, field in task.get("config", {}).items():
                yield f"{section}.{task_id}.{key}", group, field


def get_default_config() -> dict[str, Any]:
    data: dict[str, Any] = {"scheduler": copy.deepcopy(SCHEDULER_DEFAULTS)}
    for path, _, field in iter_config_fields():
        set_path(data, path, copy.deepcopy(field.get("default")))
    return data


def merge_defaults(data: dict[str, Any]) -> dict[str, Any]:
    merged = get_default_config()
    merge(merged, data)
    return merged


def get_user_config_fields() -> dict[str, dict[str, Any]]:
    return {path: field for path, _, field in iter_config_fields()}


def get_config_schema(config: Any) -> list[dict[str, Any]]:
    return [field_to_json(path, group, field, config) for path, group, field in iter_config_fields()]


def get_task_catalog(section: TaskSection = "tools") -> list[dict[str, str]]:
    return [task_to_json(section, task_id, task) for task_id, task in CONFIG[section].items()]


def get_task(section: TaskSection, task_id: str) -> dict[str, Any]:
    task = CONFIG.get(section, {}).get(task_id)
    if not isinstance(task, dict):
        raise ValueError(f"Unknown {section} task: {task_id}")
    return task


def get_task_title(section: TaskSection, task_id: str) -> str:
    return str(get_task(section, task_id)["label"])


def create_runner(section: TaskSection, task_id: str, config: Any, device: Any | None = None) -> Any:
    runner_path = str(get_task(section, task_id).get("runner") or "")
    module_name, separator, class_name = runner_path.partition(":")
    if not separator or not module_name or not class_name:
        raise ValueError(f"Task has no runner: {section}.{task_id}")
    module = importlib.import_module(module_name)
    runner_class = getattr(module, class_name)
    return runner_class(config=config, device=device)


def normalize_config_value(path: str, value: Any) -> Any:
    field = get_user_config_fields()[path]
    field_type = str(field.get("type", "text"))

    if field_type == "boolean":
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    if field_type == "integer":
        normalized: Any = int(value)
    elif field_type == "float":
        normalized = float(value)
    elif field_type == "select":
        normalized = str(value)
        options = tuple(field.get("options") or ())
        if options and normalized not in options:
            raise ValueError(f"Unsupported value for {path}: {normalized}")
    else:
        normalized = str(value)

    if field_type in {"integer", "float"} and "range" in field:
        minimum, maximum, _ = field["range"]
        if normalized < minimum or normalized > maximum:
            raise ValueError(f"Value out of range for {path}: {normalized}")
    return normalized


def field_to_json(path: str, group: str, field: dict[str, Any], config: Any) -> dict[str, Any]:
    field_type = str(field.get("type", "text"))
    payload: dict[str, Any] = {
        "key": path,
        "label": str(field.get("label", path)),
        "type": "number" if field_type in {"integer", "float"} else field_type,
        "group": group,
        "value": config.get_value(path, copy.deepcopy(field.get("default"))),
    }
    if field.get("description") is not None:
        payload["description"] = str(field["description"])
    if "range" in field:
        minimum, maximum, step = field["range"]
        payload.update({"min": minimum, "max": maximum, "step": step})
    if "options" in field:
        payload["options"] = list(field["options"])
    return payload


def task_to_json(section: TaskSection, task_id: str, task: dict[str, Any]) -> dict[str, str]:
    config_group = task_id if section == "tools" else f"schedule.{task_id}"
    payload = {
        "id": task_id,
        "title": str(task.get("label", task_id)),
        "configGroup": config_group,
    }
    if task.get("description") is not None:
        payload["description"] = str(task["description"])
    return payload


def set_path(data: dict[str, Any], path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"Cannot set nested config path: {path}")
        current = child
    current[parts[-1]] = value


def merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(target.get(key), dict) and isinstance(value, dict):
            merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)
