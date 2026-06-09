from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any


NO_DEFAULT = object()


@dataclass(frozen=True)
class ConfigField:
    key: str
    label: str
    type: str
    group: str
    description: str = ""
    min: int | float | None = None
    max: int | float | None = None
    step: int | float | None = None
    options: tuple[str, ...] | None = None
    default: Any = dataclass_field(default=NO_DEFAULT, repr=False)

    @property
    def has_default(self) -> bool:
        return self.default is not NO_DEFAULT

    def to_json(self, config: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "type": self.type,
            "group": self.group,
            "description": self.description,
            "value": config.get_value(self.key, self.default if self.has_default else None),
        }
        if self.min is not None:
            data["min"] = self.min
        if self.max is not None:
            data["max"] = self.max
        if self.step is not None:
            data["step"] = self.step
        if self.options is not None:
            data["options"] = list(self.options)
        return data
