from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import CAFE_PAGE, MAIN_PAGE
from template.tycoon import CLAIM_CAFE, CONFIRM_CLAIM
from template.ui import GET_ITEM
from utils.logger import logger

class ClaimRewards(UI):
    def run(self):
        logger.hr('CLAIM CAFE REWARDS', level=1)
        self.ui_goto(CAFE_PAGE)

        while True:
            self.device.screenshot()
            if self.appear_then_click(CONFIRM_CLAIM):
                break
            if self.appear_then_click(CLAIM_CAFE):
                self.device.sleep((1, 1.2))

        self.wait_until_appear(GET_ITEM)
        self.device.click((640, 500))
        self.ui_goto(MAIN_PAGE)