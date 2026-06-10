import time

from NTEPilot.map.map import Map
from NTEPilot.team.team import Team
from template.ui import INTERACT, CHAT
from template.combat import *
from template.control import *
from utils.image import limit_in
from utils.logger import logger
from utils.exceptions import ScriptError

class Combat(Map, Team):
    SELECTIONS = {
        1: SELECTION_1,
        2: SELECTION_2,
        3: SELECTION_3,
        4: SELECTION_4,
        5: SELECTION_5
    }

    def combat(self, teleport_target, selection):
        self.teleport_to(teleport_target)
        self.device.sleep((1, 1.2))
        self.init_team()
        self.device.move_forward(lambda: self.wait_until_appear(INTERACT))
        self.device.click(INTERACT)
        self.device.sleep((1, 1.2))
        self.device.click(self.SELECTIONS[selection])
        self.device.sleep((0.3, 0.5))
        self.device.click(ENTER)
        self.wait_until_appear(CHAT)
        self.device.sleep((0.1, 0.2))
        self.start_combat()
        self.claim_reward()

    def start_combat(self):
        logger.hr('START COMBAT', level=2)
        def find_focus_point():
            with self.device.temporary_screenshot_interval(0.4):
                while True:
                    self.device.screenshot()
                    if self.appear(FOCUS_POINT, similarity=0.6):
                        break
                    self.device.click(LOCK)
        self.device.move_forward(find_focus_point)

        # 平A拉近距离
        for _ in range(3):
            self.current_chara.use_a()
        
        while True:
            self.device.screenshot()
            if self.appear(SUCCESS):
                break
            self.device.click(LOCK)
            self.combat_once()

    def claim_reward(self):
        logger.hr('CLAIM REWARD', level=2)

        target_x = 640
        tolerance_x = 45
        drag_start = (800, 360)
        drag_left, drag_top, drag_right, drag_bottom = 260, 130, 1120, 610

        for attempt in range(1, 101):
            self.device.screenshot()

            if self.appear(INTERACT):
                self.device.click(INTERACT)
                return

            if not self.appear(CHEST, similarity=0.65):
                logger.info(f'Chest marker not found, scanning, attempt {attempt}/100')
                self.device.move_forward(lambda: self.wait_until_appear(CHEST, similarity=0.65))
                continue

            chest_x, chest_y = CHEST.pos
            dx = chest_x - target_x

            logger.info(
                f'Chest marker ({chest_x}, {chest_y}), '
                f'offset ({dx}), attempt {attempt}/100'
            )

            if chest_y > 600:
                drag_x = 150
            elif abs(dx) <= tolerance_x:
                self.device.move_forward(0.5)
                time.sleep(0.8)
                continue
            elif dx < 0:
                drag_x = 150
            else:
                drag_x = limit_in(dx * 0.1, -180, 180)
            end_x = round(limit_in(drag_start[0] + drag_x, drag_left, drag_right))

            self.device.drag(drag_start, (end_x, drag_start[1]))

        raise ScriptError('Unable to center chest marker')