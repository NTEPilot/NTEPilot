from __future__ import annotations

from NTEPilot.config import Config


class Instance:
    def __init__(self, device=None, config: Config | None = None, instance_name: str | None = None, create_device: bool = True):
        if device is not None:
            self.device = device
            self.config = device.config
            return

        self.config = config or Config.load(instance_name or "NTE")

        if create_device:
            from NTEPilot.device.device import Device

            self.device = Device(config=self.config)

    @classmethod
    def ensure_default_instance(cls) -> None:
        Config.ensure_default_instance()

    @classmethod
    def list_instances(cls) -> list[dict[str, str]]:
        return Config.list_instances()

    @classmethod
    def create(cls, name: str = "NTE", values: dict | None = None, create_device: bool = False) -> "Instance":
        return cls(config=Config.create(name, values), create_device=create_device)
