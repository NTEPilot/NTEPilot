from NTEPilot.map.map import Map
from NTEPilot.team.team import Team
from template.combat import *
from template.control import *

class Combat(Map, Team):
    def start_combat(self):
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