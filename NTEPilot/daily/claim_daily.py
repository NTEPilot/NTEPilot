from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import MAIN_PAGE, DAILY_TASK_PAGE
from template.daily import *
from template.ui import GET_ITEM
from utils.logger import logger

class ClaimDaily(UI):
    def run(self):
        logger.hr('CLAIM DAILY', level=1)
        self.ui_goto(DAILY_TASK_PAGE)
        if self.appear(CLAIM_DAILY_POINT):
            self.device.click(CLAIM_DAILY_POINT)
            self.device.sleep((2, 2.2))
        
        # 避免动画影响
        for _ in range(20):
            self.device.screenshot()
            if  self.appear_then_click(DAILY_REWARDS_1) or \
                self.appear_then_click(DAILY_REWARDS_2) or \
                self.appear_then_click(DAILY_REWARDS_3) or \
                self.appear_then_click(DAILY_REWARDS_4) or \
                self.appear_then_click(DAILY_REWARDS_5):
                self.wait_until_appear(GET_ITEM)
                self.device.click((640, 500))
                break
        
        self.ui_goto(MAIN_PAGE)