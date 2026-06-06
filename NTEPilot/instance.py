from NTEPilot.device.device import Device

class Instance:
    def __init__(self, device=None):
        if isinstance(device, Device):
            self.device = device
        else:
            self.device = Device()