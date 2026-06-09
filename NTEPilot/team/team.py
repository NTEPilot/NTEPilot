import time

from NTEPilot.instance import Instance
from .character import *

from template.control import *

SWITCH = {
    1: SWITCH_1,
    2: SWITCH_2,
    3: SWITCH_3
}

class Team(Instance):
    def __init__(self, config, device=None):
        super().__init__(config=config, device=device)
        self.team = {
            1: CHINESE_TO_CHARA[self.config["team.chara_1"]](1, self.device),
            2: CHINESE_TO_CHARA[self.config["team.chara_2"]](2, self.device),
            3: CHINESE_TO_CHARA[self.config["team.chara_3"]](3, self.device),
            4: CHINESE_TO_CHARA[self.config["team.chara_4"]](4, self.device)
        }
        self.switch_timer = {
            1: Timer(1),
            2: Timer(1),
            3: Timer(1),
            4: Timer(1)
        }
        self.skill_order = self.config["team.skill_order"].split(">")
    
    def switch_chara(self, target):
        if target == self.current_chara:
            return
        t = target if target < self.current_chara else target - 1
        self.switch_timer[t].wait()
        self.device.click(SWITCH[t])
        self.switch_timer[t].reset()
        self.device.sleep((0.2, 0.3))

    def init_team(self):
        self.device.click(SWITCH_2)
        time.sleep(1)
        self._current_chara = 2 # 临时设置成不为1的角色以便switch_chara切换
        self.switch_chara(1)

    @property
    def current_chara(self):
        if not hasattr(self, '_current_chara'):
            self.init_team()
        return self._current_chara

    def combat_once(self):
        for act in self.skill_order:
            chara = int(act[0])
            skill = act[1]
            if self.team[chara].is_ready(skill):
                self.switch_chara(chara)
                self.team[self.current_chara].use(skill)
                break
