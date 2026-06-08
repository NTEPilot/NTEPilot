from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = Path(__file__).with_name("template.json")
INSTANCES_DIR = PROJECT_ROOT / "instances"
DEFAULT_INSTANCE_NAME = "NTE"
MISSING = object()


class Config:
    def __init__(self, name: str = DEFAULT_INSTANCE_NAME, data: dict[str, Any] | None = None):
        self.name = self.normalize_name(name)
        self.path = INSTANCES_DIR / f"{self.name}.json"
        self.data = self.normalize_keys(data or self.load_template_data())
        self.data.setdefault("general", {})
        self.data["general"]["name"] = self.name

    def __getitem__(self, key: str) -> Any:
        value = self.get_from_data(self.data, key)
        if value is MISSING:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self.set_path(self.data, key, value)

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self.data)

    def get_value(self, key: str, default: Any = None) -> Any:
        value = self.get_from_data(self.data, key)
        return default if value is MISSING else value

    def update(self, values: dict[str, Any], save: bool = True) -> "Config":
        values = self.normalize_keys(values)
        allowed = {key: value for key, value in self.template_paths().items() if key != "general.name"}
        unknown = sorted(key for key in values if key not in allowed)
        if unknown:
            raise ValueError(f"Unsupported config keys: {', '.join(unknown)}")

        for key, value in values.items():
            self[key] = self.normalize_value(key, value, allowed[key])

        if save:
            self.save()
        return self

    def save(self) -> None:
        INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, name: str = DEFAULT_INSTANCE_NAME) -> "Config":
        cls.ensure_default_instance()
        normalized = cls.normalize_name(name)
        path = INSTANCES_DIR / f"{normalized}.json"
        if not path.exists():
            raise FileNotFoundError(f"Instance config not found: {normalized}")

        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(normalized, cls.merge_with_template(data))

    @classmethod
    def create(cls, name: str = DEFAULT_INSTANCE_NAME, values: dict[str, Any] | None = None) -> "Config":
        config = cls(cls.normalize_name(name), cls.load_template_data())
        if values:
            config.update(values, save=False)
        config.save()
        return config

    @classmethod
    def list_instances(cls) -> list[dict[str, Any]]:
        cls.ensure_default_instance()
        instances = []
        for path in sorted(INSTANCES_DIR.glob("*.json")):
            instances.append({"name": cls.normalize_name(path.stem), "path": str(path)})
        return instances

    @classmethod
    def ensure_default_instance(cls) -> None:
        INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
        if not any(INSTANCES_DIR.glob("*.json")):
            shutil.copyfile(TEMPLATE_PATH, INSTANCES_DIR / f"{DEFAULT_INSTANCE_NAME}.json")

    @classmethod
    def load_template_data(cls) -> dict[str, Any]:
        data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        from NTEPilot.tools.registry import get_tool_default_data

        cls.deep_merge_defaults(data, get_tool_default_data())
        return data

    @classmethod
    def merge_with_template(cls, data: dict[str, Any]) -> dict[str, Any]:
        normalized = cls.normalize_keys(data)
        if "general" not in normalized and "tools" not in normalized:
            normalized = cls.migrate_flat_data(normalized)

        merged = cls.load_template_data()
        cls.deep_merge_known(merged, normalized)
        return merged

    @classmethod
    def template_paths(cls) -> dict[str, Any]:
        paths: dict[str, Any] = {}
        cls.walk_paths(cls.load_template_data(), "", paths)
        return paths

    @staticmethod
    def walk_paths(data: dict[str, Any], prefix: str, paths: dict[str, Any]) -> None:
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                Config.walk_paths(value, path, paths)
            else:
                paths[path] = value

    @staticmethod
    def get_from_data(data: dict[str, Any], path: str) -> Any:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return MISSING
            current = current[part]
        return current

    @staticmethod
    def set_path(data: dict[str, Any], path: str, value: Any) -> None:
        current = data
        parts = path.split(".")
        for part in parts[:-1]:
            child = current.setdefault(part, {})
            if not isinstance(child, dict):
                raise ValueError(f"Cannot set nested config path: {path}")
            current = child
        current[parts[-1]] = value

    @staticmethod
    def normalize_keys(data: dict[str, Any]) -> dict[str, Any]:
        normalized = {}
        for key, value in data.items():
            normalized_key = str(key).lower()
            normalized[normalized_key] = Config.normalize_keys(value) if isinstance(value, dict) else value
        return normalized

    @staticmethod
    def normalize_name(name: str) -> str:
        normalized = "".join(ch for ch in str(name).strip() if ch.isalnum() or ch in {"-", "_"})
        if not normalized:
            raise ValueError("Instance name cannot be empty")
        return normalized

    @staticmethod
    def normalize_value(key: str, value: Any, default: Any) -> Any:
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)
        if isinstance(default, int) and not isinstance(default, bool):
            return int(value)
        if isinstance(default, float):
            return float(value)
        return str(value)

    @classmethod
    def deep_merge_known(cls, target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, source_value in source.items():
            if key not in target:
                continue
            target_value = target[key]
            if isinstance(target_value, dict) and isinstance(source_value, dict):
                cls.deep_merge_known(target_value, source_value)
            elif not isinstance(target_value, dict):
                target[key] = source_value

    @classmethod
    def deep_merge_defaults(cls, target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, source_value in source.items():
            target_value = target.get(key)
            if isinstance(target_value, dict) and isinstance(source_value, dict):
                cls.deep_merge_defaults(target_value, source_value)
            elif key not in target:
                target[key] = source_value

    @staticmethod
    def migrate_flat_data(data: dict[str, Any]) -> dict[str, Any]:
        migrated: dict[str, Any] = {"general": {}, "tools": {"fish": {}}, "team": {}}
        general_keys = {"name", "serial", "package_name", "activity_name"}
        fish_keys = {"sell_fish", "buy_bait", "buy_bait_stack_count", "green_bar_safe_proportion"}
        team_keys = {"chara_1", "chara_2", "chara_3", "chara_4", "skill_order"}

        for key, value in data.items():
            if key in general_keys:
                migrated["general"][key] = value
            elif key in fish_keys:
                migrated["tools"]["fish"][key] = value
            elif key in team_keys:
                migrated["team"][key] = value
        return migrated
