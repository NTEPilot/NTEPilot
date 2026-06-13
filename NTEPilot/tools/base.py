from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from typing import Any

from NTEPilot.config.config_field import ConfigField
from utils.exceptions import GameStuckError
from utils.logger import logger


@dataclass(frozen=True)
class ToolSpec:
    id: str
    title: str
    description: str
    runner: str
    config_fields: tuple[ConfigField, ...] = ()
    config_group: str | None = None

    @property
    def group(self) -> str:
        return self.config_group or self.id

    def to_task_json(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "configGroup": self.group,
        }

    def run(self, config: Any) -> None:
        module_name, separator, class_name = self.runner.partition(":")
        if not separator or not module_name or not class_name:
            raise ValueError(f"Invalid tool runner path: {self.runner}")

        module = importlib.import_module(module_name)
        runner_class = getattr(module, class_name)
        runner = runner_class(config=config)

        while True:
            try:
                if not runner.device.app_is_running():
                    runner.restart_app()
                runner.run()
                break
            except GameStuckError:
                logger.warning("Game stuck error detected, restarting game")
                runner.device.app_stop_adb()
                time.sleep(3)