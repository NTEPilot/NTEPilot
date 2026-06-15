from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import MAIN_PAGE, BIG_MONTHCARD_PAGE, BIG_MONTHCARD_TASK_PAGE
from template.daily import *
from template.ui import GET_ITEM
from utils.logger import logger

class ClaimBigMonthcard(UI):
    def run(self):
        logger.hr('CLAIM BIG MONTHCARD', level=1)
        self.ui_goto(BIG_MONTHCARD_TASK_PAGE)
        if self.appear(BIG_MONTHCARD_TASK_CLAIM_ALL):
            self.device.click(BIG_MONTHCARD_TASK_CLAIM_ALL)
            self.device.sleep((2, 2.2))
        self.ui_goto(BIG_MONTHCARD_PAGE)
        if self.appear(BIG_MONTHCARD_CLAIM_ALL):
            self.device.click(BIG_MONTHCARD_CLAIM_ALL)
            self.device.sleep((2, 2.2))
            self.device.click((640, 500))
        self.ui_goto(MAIN_PAGE)