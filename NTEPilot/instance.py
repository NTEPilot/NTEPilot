from __future__ import annotations

from NTEPilot.config.config import Config
from NTEPilot.device.device import Device

class Instance:
    def __init__(self, config: Config | None = None, device: Device | None = None):
        if config is None:
            config = Config.load()
        self.config = config

        if device is None:
            device = Device(self.config)
        self.device = device