from NTEPilot.map.map import Map
from .chinese_to_teleport import CHINESE_TO_TELEPORT
from template.house import *
from template.ui import CHAT, BUTTON_CROSS, GET_ITEM, SAFE_AREA
from utils.logger import logger

class ClaimHouse(Map):

    SELECTIONS = {
        1: CLAIM_1,
        2: CLAIM_2,
        3: CLAIM_3,
        4: CLAIM_4,
    }

    def run(self):
        logger.hr('CLAIM HOUSE', level=1)

        self.house = self.config['schedule.house.house']
        self.index = self.config['schedule.house.index']

        self.teleport_to(CHINESE_TO_TELEPORT[self.house])

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

        self.device.sleep((0.2, 0.3))
        self.device.swipe((1050, 220), (1050, 670))
        self.device.swipe((1050, 220), (1050, 670))
        self.device.swipe((1050, 220), (1050, 670))
        self.device.sleep((1, 1.2))
        self.device.screenshot()
        self.appear_then_click(self.SELECTIONS[self.index])

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