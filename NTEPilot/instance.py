from __future__ import annotations

from typing import Any

from NTEPilot.config.config import Config


class Instance:
    def __init__(self, config: Config, device: Any | None = None):
        self.config = config
        if device is None:
            from NTEPilot.device.device import Device

            device = Device(self.config)
        self.device = device
