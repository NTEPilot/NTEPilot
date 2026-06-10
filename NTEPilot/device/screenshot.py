import os
import time
from contextlib import contextmanager
from collections import deque
from datetime import datetime
from PIL import Image

import cv2
import numpy as np

from utils.timer import Timer
from utils.image import image_size, save_image, get_color
from .droidcast import DroidCast
from utils.exceptions import EmulatorNotRunningError, RequestHumanTakeover, ScriptError
from utils.logger import logger

class Screenshot(DroidCast):
    _screen_size_checked = False
    _screen_black_checked = False
    _minicap_uninstalled = False
    _screenshot_interval = Timer(0.1)
    _screenshot_save_timer = Timer(0.5)
    image: np.ndarray

    def screenshot(self):
        """截取屏幕截图。

        Returns:
            np.ndarray: 截取的屏幕图像。
        """
        self._screenshot_interval.wait()
        self._screenshot_interval.reset()

        for _ in range(2):
            self.image = self.screenshot_droidcast()

            width, height = image_size(self.image)

            self.image = self._handle_orientated_image(self.image)

            if self.check_screen_size() and self.check_screen_black():
                break
            else:
                continue

        return self.image

    @property
    def has_cached_image(self):
        return hasattr(self, 'image') and self.image is not None

    def _handle_orientated_image(self, image):
        """处理旋转的截图图像。

        Args:
            image: 待处理的图像。

        Returns:
            处理后的图像。
        """
        width, height = image_size(self.image)
        if width == 1280 and height == 720:
            return image

        # 仅在非 1280x720 时旋转截图
        if self.orientation == 0:
            pass
        elif self.orientation == 1:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif self.orientation == 2:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif self.orientation == 3:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        else:
            raise ScriptError(f'Invalid device orientation: {self.orientation}')

        return image

    def save_screenshot(self, interval=None):
        """保存截图。使用毫秒时间戳作为文件名。

        Args:
            interval: 两次保存之间的最小间隔（秒）。间隔内的保存将被跳过。

        Returns:
            保存成功返回 True。
        """
        if interval is not None:
            self._screenshot_save_timer.duration = interval

        if self._screenshot_save_timer.reached:
            now = time.time()
            fmt = 'png'
            file = '%s.%s' % (int(now * 1000), fmt)

            folder = './debug/screenshots'
            os.makedirs(folder, exist_ok=True)

            file = os.path.join(folder, file)
            self.image_save(file)
            self._screenshot_save_timer.reset()
            return True
        else:
            self._screenshot_save_timer.reset()
            return False

    def screenshot_last_save_time_reset(self):
        self._screenshot_save_timer.force_reached()

    def screenshot_interval_set(self, interval=None):
        """设置截图间隔。

        Args:
            interval: 两次截图之间的最小间隔（秒）。
                None 表示使用 0.1。
        """
        if interval is None:
            interval = 0.1
        elif isinstance(interval, (int, float)):
            # 代码中手动设置无限制
            pass
        else:
            logger.warning(f'Unknown screenshot interval: {interval}')
            raise ScriptError(f'Unknown screenshot interval: {interval}')

        if interval != self._screenshot_interval.duration:
            logger.info(f'Screenshot interval set to {interval}s')
            self._screenshot_interval.duration = interval

    @contextmanager
    def temporary_screenshot_interval(self, interval):
        old_interval = self._screenshot_interval.duration
        self.screenshot_interval_set(interval)
        try:
            yield
        finally:
            self.screenshot_interval_set(old_interval)

    def image_show(self, image=None):
        if image is None:
            image = self.image
        Image.fromarray(image).show()

    def image_save(self, file=None):
        if file is None:
            file = f'{int(time.time() * 1000)}.png'
        save_image(self.image, file)

    def check_screen_size(self):
        """检查屏幕分辨率是否为 1280x720。

        调用前需先截取截图。
        """
        if self._screen_size_checked:
            return True

        orientated = False
        for _ in range(2):
            # 检查屏幕分辨率
            width, height = image_size(self.image)
            logger.attr('Screen_size', f'{width}x{height}')
            if width == 1280 and height == 720:
                self._screen_size_checked = True
                return True
            elif not orientated and (width == 720 and height == 1280):
                logger.info('Received orientated screenshot, handling')
                self.get_orientation()
                self.image = self._handle_orientated_image(self.image)
                orientated = True
                width, height = image_size(self.image)
                if width == 720 and height == 1280:
                    logger.info('Unable to handle orientated screenshot, continue for now')
                    return True
                else:
                    continue
            elif hasattr(self, 'app_is_running') and not self.app_is_running():
                logger.warning('Received orientated screenshot, game not running')
                return True
            else:
                logger.critical(f"大叔，你看着分辨率对吗: {width}x{height}。真是个连分辨率都不会设的杂鱼呢❤")
                logger.critical("乖乖给我改成 1280x720 哦，不然我可不理你了❤")
                raise RequestHumanTakeover

    def check_screen_black(self):
        if self._screen_black_checked:
            return True
        # 检查屏幕颜色，某些模拟器可能会获取纯黑截图。
        color = get_color(self.image, area=(0, 0, 1280, 720))
        if sum(color) < 1:
            logger.warning(f'Received pure black screenshots from emulator, color: {color}')
            logger.warning(f'Screenshot method may not work on emulator `{self.serial}`, or the emulator is not fully started')
            self.droidcast_stop()
            self._screen_black_checked = False
            return False
        else:
            self._screen_black_checked = True
            return True
