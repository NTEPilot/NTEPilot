from NTEPilot.map.map import Map
from .chinese_to_teleport import CHINESE_TO_TELEPORT
from template.house import *
from template.ui import CHAT, BUTTON_CROSS, GET_ITEM, SAFE_AREA
from utils.logger import logger

class ClaimHouse(Map):
    def run(self):
        logger.hr('CLAIM HOUSE', level=1)

        self.teleport_to(32)

        with self.device.temporary_screenshot_interval(0.5):
            while True:
                self.device.screenshot()
                if self.appear(FURNITURE):
                    self.device.click(FURNITURE)
                    continue
                if self.appear(FURNITURE_OVERVIEW):
                    self.device.sleep((0.2, 0.3))
                    self.device.click(FURNITURE_OVERVIEW)
                    break

        self.wait_until_appear_then_click(FURNITURE_CLAIM_ALL)

        with self.device.temporary_screenshot_interval(0.5):
            while True:
                self.device.screenshot()
                if self.appear(GET_ITEM):
                    self.device.click(SAFE_AREA)
                    continue
                if self.appear(BUTTON_CROSS):
                    self.device.click(BUTTON_CROSS)
                    continue
                if self.appear(CHAT):
                    break