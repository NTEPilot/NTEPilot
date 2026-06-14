from template.bond import PRESENT
from NTEPilot.device import screenshot
from rich import screen
from NTEPilot.ui.ui import UI
from NTEPilot.ocr import Ocr
from NTEPilot.ui.page import BOND_PAGE, MAIN_PAGE
from template.bond import *
from utils.logger import logger

class Gift(UI, Ocr):
    CHARAS = [CHARA_1, CHARA_2, CHARA_3, CHARA_4, CHARA_5]
    GIFTS = {
        1: GIFT_1,
        2: GIFT_2,
        3: GIFT_3,
        4: GIFT_4,
        5: GIFT_5,
        6: GIFT_6,
        7: GIFT_7,
        8: GIFT_8,
        9: GIFT_9,
        10: GIFT_10,
    }

    def ocr(self, *args, **kwargs):
        result = super().ocr(*args, **kwargs)

        # 狗狗人是驱（
        if result == '驱':
            logger.info('Detected 驱, correcting to 翳')
            result = '翳'
        elif result == '得':
            logger.info('Detected 得, correcting to 浔')
            result = '浔'

        return result

    def click(self, target):
        self.device.click(target)
        self.device.sleep((0.3, 0.5))

    def try_gift(self):
        self.device.screenshot()
        if self.appear(LOCKED):
            logger.warning(f'Failed to find {self.target_chara}')
            return True
        name = self.ocr(NAME, model='cn', letter_color=(180, 180, 180), screenshot=False)
        if name != self.target_chara:
            if name != self._last_chara:
                self._last_chara = name
                return False
            logger.warning(f'Failed to find {self.target_chara}')
            return True
        logger.info(f'Successfully find {self.target_chara}')

        self.device.click(GIFT)
        self.wait_until_appear(PRESENT)
        self.click(self.GIFTS[self.target_gift])
        for _ in range(self.target_number):
            self.device.click(PRESENT)
            self.device.sleep((2, 2.2))

        return True

    def gift(self):
        for chara in self.CHARAS:
            self.click(chara)
            if self.try_gift():
                return
        while True:
            self.device.drag((1200, 600), (1200, 490))
            self.click(CHARA_5)
            if self.try_gift():
                return
    
    def run(self):
        logger.hr('GIFT', level=1)

        self.target_chara = self.config['schedule.gift.character']
        self.target_gift = self.config['schedule.gift.gift']
        self.target_number = self.config['schedule.gift.number']
        self._last_chara = ''

        self.ui_goto(BOND_PAGE)
        self.gift()
        self.ui_goto(MAIN_PAGE)