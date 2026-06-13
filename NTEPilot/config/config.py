from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from NTEPilot.config import schema


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INSTANCES_DIR = PROJECT_ROOT / "instances"
DEFAULT_INSTANCE_NAME = "NTE"
MISSING = object()


class Config:
    def __init__(self, name: str = DEFAULT_INSTANCE_NAME, data: dict[str, Any] | None = None):
        self.name = self.normalize_name(name)
        self.path = INSTANCES_DIR / f"{self.name}.json"
        self.data = copy.deepcopy(data) if data is not None else schema.get_default_config()
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
        allowed = schema.get_user_config_fields()
        unknown = sorted(key for key in values if key not in allowed)
        if unknown:
            raise ValueError(f"Unsupported config keys: {', '.join(unknown)}")

        for key, value in values.items():
            self[key] = schema.normalize_config_value(key, value)

        if save:
            self.save()
        return self

    def save(self) -> None:
        INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, name: str = DEFAULT_INSTANCE_NAME) -> "Config":
        cls.ensure_default_instance()
        normalized_name = cls.normalize_name(name)
        path = INSTANCES_DIR / f"{normalized_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Instance config not found: {normalized_name}")

        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(normalized_name, schema.merge_defaults(data))

    @classmethod
    def create(cls, name: str = DEFAULT_INSTANCE_NAME, values: dict[str, Any] | None = None) -> "Config":
        config = cls(cls.normalize_name(name), schema.get_default_config())
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
            config = cls(DEFAULT_INSTANCE_NAME, schema.get_default_config())
            config.save()

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
    def normalize_name(name: str) -> str:
        normalized = "".join(ch for ch in str(name).strip() if ch.isalnum() or ch in {"-", "_"})
        if not normalized:
            raise ValueError("Instance name cannot be empty")
        return normalized
