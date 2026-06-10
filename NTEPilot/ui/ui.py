from .info_handler import InfoHandler
from .page import Page

from utils.logger import logger

class UI(InfoHandler):
    def ui_page_appear(self, page, offset=10):
        return self.appear(page.check_template, offset=offset)

    def ui_goto(self, destination, offset=10, skip_first_screenshot=True):
        Page.init_connection(destination)

        logger.hr(f"UI goto {destination}")
        with self.device.temporary_screenshot_interval(1):
            while True:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                # 到达目标页面
                if self.ui_page_appear(page=destination, offset=offset):
                    logger.info(f'Page arrive: {destination}')
                    break

                # 其他页面：按 A* 路径点击导航
                for page in Page.iter_pages():
                    if page.parent is None or page.check_template is None:
                        continue
                    if self.appear(page.check_template, offset=offset):
                        logger.info(f'Page switch: {page} -> {page.parent}')
                        button = page.links[page.parent]
                        self.device.click(button)
                        break

        # 重置页面连接
        Page.clear_connection()