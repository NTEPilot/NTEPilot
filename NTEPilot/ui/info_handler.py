import time

from NTEPilot.instance import Instance
from template import Template
from template.ui import START_1, START_2, START_3, CHAT, MONTH_CARD, GET_ITEM, SAFE_AREA

from utils.logger import logger

class InfoHandler(Instance):
    def appear(self, template: Template, offset=10, similarity=0.85):
        """
        检测模板是否出现在当前截图上。

        Args:
            template: 待检测的 Template 或 xpath 字符串。
            similarity: 模板匹配相似度阈值，0~1。

        Returns:
            bool: 元素是否出现。
        """

        appear = template.match(self.device.image, offset=offset, similarity=similarity)
        return appear

    def appear_then_click(self, template: Template, offset=10, similarity=0.85):
        appear = self.appear(template, offset=offset, similarity=similarity)
        if appear:
            self.device.click(template)
        return appear

    def wait_until_appear(self, template: Template, offset=0, similarity=0.85, skip_first_screenshot=False):
        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(template, offset=offset, similarity=similarity):
                break

    def wait_until_appear_then_click(self, template: Template, offset=0, similarity=0.85):
        self.wait_until_appear(template, offset=offset, similarity=similarity)
        self.device.click(template)

    def wait_until_disappear(self, template: Template, offset=0, similarity=0.85):
        while True:
            self.device.screenshot()
            if not self.appear(template, offset=offset, similarity=similarity):
                break

    def handle_enter_game(self):
        if self.appear(MONTH_CARD):
            self.device.click(SAFE_AREA)
            return True
        if self.appear(GET_ITEM):
            self.device.click(SAFE_AREA)
            return True
        if self.appear(START_1):
            self.device.click(SAFE_AREA)
            return True
        if self.appear(START_2):
            self.device.click(START_2)
            return True
        if self.appear(START_3):
            self.device.click(SAFE_AREA)
            return True
        return False

    def restart_app(self):
        logger.hr('RESTART', level=1)
        self.device.app_stop_adb()
        time.sleep(3)
        self.device.app_start_adb()
        time.sleep(3)
        with self.device.temporary_screenshot_interval(3):
            while True:
                self.device.screenshot()
                if self.handle_enter_game():
                    continue
                if self.appear(CHAT):
                    logger.info('App restarted successfully')
                    break
                

    def ensure_in_game(self):
        if self.device.app_is_running():
            self.device.screenshot()
            if self.handle_enter_game():
                with self.device.temporary_screenshot_interval(3):
                    while True:
                        self.device.screenshot()
                        if self.handle_enter_game():
                            continue
                        if self.appear(CHAT):
                            logger.info('App restarted successfully')
                            break
        else:
            self.restart_app()
        