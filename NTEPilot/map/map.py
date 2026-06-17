import math
import time
from .map_data import map_data
from .map_locator import map_locator
from .navigation import MinimapNavigation
from .utils import MapMatchError, CROP

from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import MAIN_PAGE, MAP_PAGE
from template import Template
from template.map import *
from template.ui import CHAT
from template.control import JUMP

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

    def follow_navigation_from_teleport(self, number: int, target_template: Template | None = None) -> None:
        teleport = map_data.get_teleport(number)
        self.teleport_to(number)
        self.device.sleep((1.5, 1.8))
        self.follow_navigation(camera_angle=teleport.camera_yaw, target_template=target_template)

    def follow_navigation(self, camera_angle: float = 0.0, target_template: Template | None = None) -> None:
        logger.hr("FOLLOW NAVIGATION", level=2)
        self.ui_goto(MAIN_PAGE, skip_first_screenshot=False)

        navigator = MinimapNavigation(camera_angle=camera_angle)

        while True:
            self.device.screenshot()
            state = navigator.analyze(self.device.image)
            if navigator.arrived(state):
                if navigator.last_move_angle is not None:
                    logger.info(f"Navigation arrived. Moving at {navigator.last_move_angle:.1f}° for a constant 5.0s.")
                    start_move = time.time()
                    def move_and_jump():
                        while time.time() - start_move < 5.5:
                            self.device.click(JUMP)
                            time.sleep(0.1)
                    self.device.move(navigator.last_move_angle, move_and_jump)
                else:
                    logger.warning('Route not found, perhaps navigation point is not set')
                if target_template is not None:
                    self._fine_tune_navigation(navigator, target_template, camera_angle)
                return

            move_angle = navigator.move_angle(state)
            logger.info(
                f"Navigation route={self._format_angle(state.route_angle)}, "
                f"camera={self._format_angle(camera_angle)}, "
                f"move={self._format_angle(move_angle)}, "
                f"pixels={state.route_pixels}, nearest={state.nearest_distance:.1f}, "
                f"farthest={state.distance:.1f}"
            )

            if move_angle is None:
                continue

            self.device.move(move_angle, self._navigation_until(navigator, move_angle))

    def _fine_tune_navigation(
        self,
        navigator: MinimapNavigation,
        target_template: Template,
        camera_angle: float,
        max_attempts: int = 200,
    ) -> None:
        """使用终点小地图模板做像素级落点微调。
        Fine-tune the final position with a target minimap template at pixel precision.

        Args:
            navigator: 当前小地图导航器。
                       Current minimap navigator.
            target_template: 人物站在真实终点时截取的小地图模板。
                             Minimap template captured at the real endpoint.
            camera_angle: 当前相机朝向，用于把小地图方向换算为摇杆方向。
                          Current camera angle used to convert minimap direction to joystick direction.
            max_attempts: 最大微调次数，避免模板异常时无限循环。
                          Maximum fine-tuning attempts to avoid an infinite loop on bad templates.

        Raises:
            MapMatchError: 模板无法识别或多次微调后仍未逐像素对齐。
                           Raised when matching fails or pixel alignment is not reached.
        """
        logger.hr("FINE TUNE NAVIGATION", level=2)
        last_offset = None

        for attempt in range(1, max_attempts + 1):
            self.device.screenshot()
            offset = navigator.template_offset(self.device.image, target_template)
            if offset is None:
                raise MapMatchError(f"Unable to match target minimap template: {target_template}")

            last_offset = offset
            logger.info(
                f"Fine tune target={target_template}, dx={offset.dx}, dy={offset.dy}, "
                f"score={offset.score:.3f}, attempt={attempt}/{max_attempts}"
            )
            if offset.aligned:
                logger.info("Fine tune complete: minimap template aligned at pixel level")
                return

            screen_angle = MinimapNavigation._screen_vector_to_angle(offset.dx, offset.dy)
            move_angle = (screen_angle - camera_angle) % 360
            distance = math.hypot(offset.dx, offset.dy)
            self.device.move(move_angle, 0.1)
            self.device.sleep(0.12)

        raise MapMatchError(
            f"Unable to align minimap template after {max_attempts} attempts, last={last_offset}"
        )

    def _navigation_until(self, navigator: MinimapNavigation, move_angle: float):
        def wait_until_turn_or_arrive():
            while True:
                self.device.click(JUMP)
                self.device.screenshot()
                state = navigator.analyze(self.device.image)
                if navigator.arrived(state):
                    return
                next_angle = navigator.move_angle(state)
                if next_angle is None:
                    continue
                delta = abs(MinimapNavigation.angle_delta(next_angle, move_angle))
                if delta > 15:
                    return
                # if time.time() - segment_start > 4.0:
                #     return

        return wait_until_turn_or_arrive

    @staticmethod
    def _format_angle(angle: float | None) -> str:
        return "None" if angle is None else f"{angle:.1f}"

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
