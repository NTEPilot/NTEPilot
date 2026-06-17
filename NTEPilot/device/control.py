import time
import random
import math

from utils.exceptions import ScriptError
from .minitouch import Minitouch
from utils.logger import logger
from template import Template

JOYSTICK_CENTER = (198, 565)
JOYSTICK_OFFSET = 100

class Control(Minitouch):
    @staticmethod
    def random_time(second):
        """休眠指定时间。

        Args:
            second (tuple): 休眠时间（秒），可以是固定值或范围元组。
        """
        if isinstance(second, (int, float)):
            return float(second)
        a = float(second[0])
        b = float(second[1])
        total = 0
        for _ in range(3):
            total += random.uniform(a, b)
        return total / 3
    
    @classmethod
    def sleep(cls, duration):
        time.sleep(cls.random_time(duration))

    def click(self, target, control_check=True):
        """点击按钮。

        Args:
            target (button.Button): 碧蓝航线按钮实例。
            control_check (bool): 是否进行控制检查。
        """
        if isinstance(target, tuple):
            x, y = target[0], target[1]
            logger.info(f'Click ({x}, {y})')
        elif isinstance(target, Template):
            x, y = target.pos
            logger.info(f'Click ({x}, {y}) @ {target}')
        else:
            raise ScriptError(f'Unsupported target type: {type(target)}')

        self.click_minitouch(x, y)

    def multi_click(self, button, n, interval=(0.1, 0.2)):
        last_time = time.time()
        for _ in range(n):
            remain = self.random_time(interval) - (time.time() - last_time)
            if remain > 0:
                time.sleep(remain)
            last_time = time.time()
            self.click(button, control_check=False)

    def long_click(self, target, duration=(1, 1.2)):
        """长按按钮。

        Args:
            button (button.Button): 碧蓝航线按钮实例。
            duration (int, float, tuple): 长按持续时间。
        """
        duration = self.random_time(duration)
        if isinstance(target, tuple):
            x, y = target[0], target[1]
            logger.info(f'Long Click ({x}, {y}) for {duration:.3f}s')
        elif isinstance(target, Template):
            x, y = target.pos
            logger.info(f'Long Click ({x}, {y}) @ {target} for {duration:.3f}s')
        else:
            raise ScriptError(f'Unsupported target type: {type(target)}')

        self.long_click_minitouch(x, y, duration)

    def swipe(self, p1, p2):
        logger.info(f'Swipe {p1} -> {p2}')
        self.swipe_minitouch(p1, p2)

    def drag(self, p1, p2, disturbance=False):
        logger.info(f'Drag {p1} -> {p2}')
        self.drag_minitouch(p1, p2, disturbance=disturbance)

    def press(self, target):
        if isinstance(target, tuple):
            x, y = target[0], target[1]
            logger.info(f'Press ({x}, {y})')
        elif isinstance(target, Template):
            x, y = target.pos
            logger.info(f'Press ({x}, {y}) @ {target}')
        else:
            raise ScriptError(f'Unsupported target type: {type(target)}')
        self.press_minitouch(x, y)

    def release(self):
        logger.info('Release')
        self.release_minitouch()

    def move(self, angle, until):
        end_point = (JOYSTICK_CENTER[0] + math.sin(math.radians(angle)) * JOYSTICK_OFFSET, JOYSTICK_CENTER[1] - math.cos(math.radians(angle)) * JOYSTICK_OFFSET)
        self.keep_drag_minitouch(JOYSTICK_CENTER, end_point, contact=1)

        try:
            if isinstance(until, (int, float)):
                logger.info(f'Move at {angle} degrees for {until} seconds')
                time.sleep(until)
            elif callable(until):
                logger.info(f'Move at {angle} degrees until {until.__name__}')
                until()
                logger.info('Move stop')
            else:
                raise ScriptError(f'Unsupported until type: {type(until)}')
        finally:
            try:
                self.release_minitouch(contact=1)
            except Exception as exc:
                logger.warning('Failed to release move contact: %s', exc)
                logger.debug('Failed to release move contact', exc_info=True)

    def move_forward(self, until):
        self.move(0, until)

    def move_backward(self, until):
        self.move(180, until)

    def move_left(self, until):
        self.move(270, until)

    def move_right(self, until):
        self.move(90, until)

    def move_forward_right(self, until):
        self.move(45, until)
        
    def move_backward_right(self, until):
        self.move(135, until)
        
    def move_backward_left(self, until):
        self.move(225, until)
        
    def move_forward_left(self, until):
        self.move(315, until)
