from template.map import BUTTON_TELEPORT_TOWER
from importlib.metadata import distribution
import math
from .map_data import map_data
from .map_locator import map_locator
from .utils import MapMatchError, CROP

from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import MAP_PAGE
from template.map import *
from template.ui import CHAT

from utils.logger import logger
from utils.image import limit_in

class Map(UI):
    def teleport_screen_position(self, number):
        teleport = map_data.get_teleport(number)
        self.device.screenshot()
        view = map_locator.locate(self.device.image)
        return view.map_to_screen(teleport.map_x, teleport.map_y), view

    def teleport_to(self, number, max_attempts=10):
        logger.hr(f'TELEPORT TO {number}', level=2)
        self.ui_goto(MAP_PAGE, skip_first_screenshot=False)

        while True:
            self.device.screenshot()
            if self.appear(MAP_BEEN_MINIMIZED):
                break
            self.device.click(MAP_MINIMIZE)

        teleport = map_data.get_teleport(number)
        last_position = None

        for attempt in range(1, max_attempts + 1):
            self.device.screenshot()
            view = map_locator.locate(self.device.image)
            sx, sy = view.map_to_screen(teleport.map_x, teleport.map_y)
            logger.info(
                f"Teleport #{number} screen position ({sx:.1f}, {sy:.1f}), "
                f"match score {view.score:.3f}, attempt {attempt}/{max_attempts}"
            )

            if self._inside_safe_rect(sx, sy):
                point = (round(sx), round(sy))
                self.device.click(point)
                while True:
                    self.device.screenshot()
                    if self.appear(BUTTON_TELEPORT):
                        self.device.click(BUTTON_TELEPORT)
                        break
                    if self.appear(BUTTON_TELEPORT_TOWER):
                        self.device.click(BUTTON_TELEPORT_TOWER)
                        break
                self.wait_until_appear(CHAT)
                return

            p1, p2 = self._drag_points(sx, sy)
            last_position = (round(sx), round(sy))
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            if dist > 200:
                steps = math.ceil(dist / 200)
                step_dx = dx / steps
                step_dy = dy / steps
                for i in range(steps):
                    sp2 = (round(p1[0] + step_dx), round(p1[1] + step_dy))
                    self.device.drag(p1, sp2, disturbance=True)
                    self.device.sleep(0.5)
            else:
                self.device.drag(p1, p2, disturbance=True)
                self.device.sleep(0.5)

        raise MapMatchError(f"Unable to bring teleport #{number} into view, last={last_position}")

    def _inside_safe_rect(self, x: float, y: float) -> bool:
        left, top, right, bottom = CROP
        return left <= x <= right and top <= y <= bottom

    def _drag_points(self, target_x: float, target_y: float) -> tuple[tuple[int, int], tuple[int, int]]:
        left, top, right, bottom = CROP
        center_x = (left + right) / 2
        center_y = (top + bottom) / 2

        drag_x = -limit_in(target_x - center_x, -420, 420)
        drag_y = -limit_in(target_y - center_y, -250, 250)
        if abs(drag_x) < 120 and not left <= target_x <= right:
            drag_x = 120 if target_x < left else -120
        if abs(drag_y) < 100 and not top <= target_y <= bottom:
            drag_y = 100 if target_y < top else -100

        p1 = (round(center_x), round(center_y))
        p2 = (
            round(limit_in(center_x + drag_x, left, right)),
            round(limit_in(center_y + drag_y, top, bottom)),
        )
        return p1, p2