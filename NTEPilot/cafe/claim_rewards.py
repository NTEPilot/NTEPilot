from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import CAFE_PAGE, MAIN_PAGE
from template.tycoon import CLAIM_CAFE, CONFIRM_CLAIM
from template.ui import GET_ITEM
from utils.logger import logger

class ClaimRewards(UI):
    def run(self):
        logger.hr('CLAIM CAFE REWARDS', level=1)
        self.ui_goto(CAFE_PAGE)
        self.device.click(CLAIM_CAFE)
        self.wait_until_appear_then_click(CONFIRM_CLAIM)
        self.wait_until_appear(GET_ITEM)
        self.device.click((640, 500))
        self.ui_goto(MAIN_PAGE)