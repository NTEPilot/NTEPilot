"""粉爪大劫案 JSON 路线运行时。
Runtime for PinkPaw Heist JSON routes.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from NTEPilot.macro.route import RouteResult, is_hit
from NTEPilot.macro.semantic import SemanticController
from NTEPilot.ocr import Ocr
from NTEPilot.team.team import Team
from NTEPilot.ui.ui import UI
from template import Template
from template.pinkpaw import HEIST_INTERAC_LOCK_PICK, HEIST_LOCK_PICK, INTERACTABLE
from template.ui import INTERACT
from utils.exceptions import ScriptError
from utils.logger import logger


DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
REWARD_OCR_DELAY_MS = 3000
POST_REWARD_DELAY_MS = 7000
ROUTE_SLEEP_POLL_INTERVAL = 0.02
ROUTE_REWARD_CHECK_MIN_SLEEP = 0.5
REWARD_CHECK_INTERVAL = 1.0
WAIT_UNTIL_POLL_INTERVAL = 0.05
TEAM_HEALTH_SLASH_ROI = (620, 654, 95, 42)
CURRENT_CHAR_MARKER_ROI = (1168, 164, 68, 36)
CURRENT_CHAR_MARKER_CORE_ROI = (1176, 172, 38, 16)
CURRENT_CHAR_SLOT_SPACING = 88
CURRENT_CHAR_SLOT_WHITE_THRESHOLDS = (205, 188, 205, 205)
CURRENT_CHAR_SLOT_COLORED_THRESHOLDS = (170, 145, 170, 170)
CURRENT_CHAR_SLOT_SCORE_BONUS = (0, 4, 0, 0)
CURRENT_CHAR_SLOT_MIN_SCORE = (16, 12, 16, 16)
CURRENT_CHAR_SLOT_MIN_MARGIN = (5, 2, 5, 5)
CURRENT_CHAR_CORE_SCORE_WEIGHT = 3
CURRENT_CHAR_SLOT2_CORE_MIN_SCORE = 6
CURRENT_CHAR_SLOT2_CORE_MIN_MARGIN = 2
SWITCH_CHECK_DURATION = 1.0
SWITCH_CONFIRM_RETRY_COUNT = 1
SWITCH_CONFIRM_RETRY_WINDOW = 0.7
SWITCH_BLACK_SCREEN_EXTENSION = 0.5
SWITCH_DEAD_SETTLE = 0.2
BLACK_SCREEN_MEAN_THRESHOLD = 18
BLACK_SCREEN_BRIGHT_PIXEL_THRESHOLD = 80
BLACK_SCREEN_BRIGHT_PIXEL_COUNT = 300
INTERACT_HOLD_INTERVAL = 0.25


@dataclass
class CharacterSwitchState:
    """角色切换候选状态。
    Character switch candidate state.
    """

    role: str
    keys: list[str]
    index: int = 0
    deadline: float = 0.0

    @property
    def current_key(self) -> str:
        """返回当前候选按键。
        Return the current candidate key.
        """
        return self.keys[self.index]

    def advance(self) -> bool:
        """推进到下一个候选。
        Advance to the next candidate.
        """
        self.index += 1
        return self.index < len(self.keys)


class AbortException(Exception):
    """粉爪路线主动中止。
    PinkPaw route aborted intentionally.
    """


class EarlyExtractException(Exception):
    """粉爪路线提前撤离。
    PinkPaw route extracted early.
    """


class RouteStopException(Exception):
    """粉爪路线内部停止异常。
    Internal stop exception for PinkPaw routes.
    """


class PinkPawRouteRuntime(Team, Ocr, UI):
    """把转换后的粉爪源码路线映射到 NTEPilot 手机触控。
    Map converted PinkPaw source routes to NTEPilot mobile touch controls.
    """

    ROLE_RUNNER = "runner"
    ROLE_AVOIDER = "avoider"
    ROLE_FIGHTER = "fighter"
    AVOID_METHOD_DASH = "dash"
    AVOID_METHOD_ATTACK = "attack"

    def __init__(self, config: Any, device: Any | None = None, params: dict[str, Any] | None = None) -> None:
        """初始化粉爪运行时。
        Initialize PinkPaw runtime.

        Args:
            config: 配置对象。
                    Config object.
            device: 可复用设备对象。
                    Reusable device object.
            params: 路线参数。
                    Route parameters.
        """
        super().__init__(config=config, device=device)
        params = params or {}
        self.semantic = SemanticController(self.device)
        self.ah = self
        self.stopping = False
        self._held_keys: set[str] = set()
        self._quick_pick_active = False
        self._quick_pick_ready_at = 0.0
        self._next_quick_pick_at = 0.0
        self._last_action_at: dict[str, float] = {}
        self._interaction_watch_active = False
        self._interaction_watch_found = False
        self._checking_interaction = False
        self._switch_state: CharacterSwitchState | None = None
        self._handling_switch_state = False
        self._next_switch_poll_at = 0.0
        self._dead_fighter_keys: list[str] = []
        self._current_fighter_key: str | None = None
        self._pointer_pos: tuple[int, int] = (640, 360)
        self._adaptive_timeout_ms = 120000.0
        self._calibrated = False
        self.check_reward_fail_count = 0
        self.last_check_reward_time = 0.0
        self.exit_state = {1: False, 2: False, 3: False}
        self.early_extract_exit = {
            1: bool(params.get("early_extract_exit1", False)),
            2: bool(params.get("early_extract_exit2", False)),
        }
        avoid_method = str(params.get("avoid_method", self.AVOID_METHOD_DASH))
        self.avoid_methods = [self.AVOID_METHOD_DASH, self.AVOID_METHOD_ATTACK]
        self.config_values = {
            "fighter": [str(v) for v in params.get("fighter", ["4", "1"])],
            "runner": [str(v) for v in params.get("runner", ["3"])],
            "avoider": [str(v) for v in params.get("avoider", ["2"])],
            "avoid_method": avoid_method,
        }
        self.route_timing_scale = float(params.get("timing_scale", 1.0))
        self.interaction_pause = float(params.get("interaction_pause", 0.2))

    def route_exec_namespace(self) -> dict[str, Any]:
        """返回路线源码执行命名空间。
        Return namespace for route source execution.
        """
        return {
            "time": time,
            "range": range,
            "len": len,
            "list": list,
            "set": set,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "max": max,
            "min": min,
            "print": print,
            "AbortException": AbortException,
            "EarlyExtractException": EarlyExtractException,
            "RouteStopException": RouteStopException,
            "REWARD_OCR_DELAY_MS": REWARD_OCR_DELAY_MS,
            "POST_REWARD_DELAY_MS": POST_REWARD_DELAY_MS,
            "_is_hit": is_hit,
            "DEFAULT_WIDTH": DEFAULT_WIDTH,
            "DEFAULT_HEIGHT": DEFAULT_HEIGHT,
        }

    @staticmethod
    def route_result(success: bool = True) -> RouteResult:
        """创建路线返回结果。
        Create a route result.
        """
        return RouteResult(success)

    def raise_if_stopped(self) -> None:
        """任务停止时抛出异常。
        Raise when the route is stopping.
        """
        if self.stopping:
            raise AbortException("PinkPaw route stopped")

    def is_stopping(self) -> bool:
        """返回停止状态。
        Return stopping state.
        """
        return bool(self.stopping)

    def key_down(self, key: str) -> bool:
        """按下语义键。
        Press a semantic key.
        """
        return self.send_key_down(key)

    def key_up(self, key: str) -> bool:
        """松开语义键。
        Release a semantic key.
        """
        return self.send_key_up(key)

    def click_key(self, key: str, duration: float | None = None) -> bool:
        """短按语义键。
        Tap a semantic key.
        """
        return self.send_key(key, down_time=duration or 0.02)

    def send_key(self, key: str, down_time: float = 0.02, interval: float = -1, after_sleep: float = 0, action_name: str | None = None) -> bool:
        """短按或长按语义键。
        Tap or hold a semantic key.
        """
        key = self._norm_key(key)
        name = action_name or f"key:{key}"
        if not self._check_interval(name, interval):
            return False
        self.semantic.tap(key, duration=max(float(down_time or 0.0), 0.0))
        if after_sleep:
            self.sleep(after_sleep)
        return True

    def send_key_down(self, key: str, after_sleep: float = 0) -> bool:
        """按下语义键。
        Press a semantic key.
        """
        key = self._norm_key(key)
        if key == "interact":
            if not self._quick_pick_active:
                self._quick_pick_ready_at = time.monotonic()
                self._next_quick_pick_at = self._quick_pick_ready_at
            self._quick_pick_active = True
            self._held_keys.add(key)
            return True
        self._held_keys.add(key)
        ret = self.semantic.key_down(key)
        if after_sleep:
            self.sleep(after_sleep)
        return ret

    def send_key_up(self, key: str, after_sleep: float = 0) -> bool:
        """松开语义键。
        Release a semantic key.
        """
        key = self._norm_key(key)
        if key == "interact":
            self._quick_pick_active = False
            self._held_keys.discard(key)
            return True
        self._held_keys.discard(key)
        ret = self.semantic.key_up(key)
        if after_sleep:
            self.sleep(after_sleep)
        return ret

    def sleep_send_key(self, time_out: float, key: str, interval: float = 0.2) -> None:
        """在指定时间内重复短按语义键。
        Repeatedly tap a semantic key during a duration.
        """
        deadline = time.monotonic() + float(time_out)
        while time.monotonic() < deadline:
            self.send_key(key, interval=interval)
            self.sleep(0.01)

    def sleep(self, timeout: float, check_reward: bool = True, scaled: bool = True) -> bool:
        """等待并轮询停止状态。
        Sleep while polling stop state.
        """
        duration = max(float(timeout), 0.0)
        if scaled:
            duration = self._scale_route_duration(duration)
        deadline = time.perf_counter() + duration
        allow_reward_check = check_reward and duration >= ROUTE_REWARD_CHECK_MIN_SLEEP
        while time.perf_counter() < deadline:
            self.raise_if_stopped()
            self._poll_quick_pick()
            self._poll_character_switch()
            if allow_reward_check and not self._has_timing_sensitive_key_held():
                self._check_still_in_heist()
            if self._interaction_watch_active and not self._interaction_watch_found and not self._checking_interaction:
                self._interaction_watch_found = self.find_interac()
            remaining = deadline - time.perf_counter()
            time.sleep(max(0.0, min(ROUTE_SLEEP_POLL_INTERVAL, remaining)))
        self._poll_quick_pick()
        self._poll_character_switch()
        return True

    def delay(self, ms: int | float, check_reward: bool = True) -> bool:
        """按毫秒等待。
        Sleep for milliseconds.
        """
        return self.sleep(float(ms) / 1000.0, check_reward=check_reward, scaled=False)

    def click(self, x: float = -1, y: float = -1, move_back: bool = False, name: str | None = None, interval: float = -1, move: bool = True, key: str = "attack", down_time: float = 0.01, after_sleep: float = 0) -> bool:
        """点击语义鼠标键。
        Click a semantic mouse key.
        """
        name = name or f"click:{key}"
        if not self._check_interval(name, interval):
            return False
        ret = self.semantic.click(x=x, y=y, key=key, down_time=down_time)
        if after_sleep:
            self.sleep(after_sleep)
        return ret

    def mouse_down(self, x: float = -1, y: float = -1, name: str | None = None, key: str = "attack") -> bool:
        """按下鼠标语义键。
        Press a semantic mouse key.
        """
        if self._norm_key(key) == "camera_reset":
            return self.semantic.camera_reset(start=self._pointer_pos)
        return self.send_key_down(key)

    def mouse_up(self, name: str | None = None, key: str = "attack") -> bool:
        """松开鼠标语义键。
        Release a semantic mouse key.
        """
        if self._norm_key(key) == "camera_reset":
            return True
        return self.send_key_up(key)

    def move_to(self, x: int, y: int, duration_ms: int | None = None) -> bool:
        """记录路线指针位置供后续触控动作使用。
        Record route pointer position for later touch actions.
        """
        self._pointer_pos = (max(0, min(DEFAULT_WIDTH - 1, int(x))), max(0, min(DEFAULT_HEIGHT - 1, int(y))))
        if duration_ms:
            self.sleep(float(duration_ms) / 1000.0, check_reward=False, scaled=False)
        return True

    def focus_window(self) -> bool:
        """通过中心点击让游戏接收后续触控。
        Focus the game by tapping the center area before later touches.
        """
        self.device.click((640, 360))
        return True

    def run_task(self, task_name: str, pipeline_override: dict[str, Any] | None = None) -> RouteResult:
        """执行路线节点名对应的 NTEPilot 行为。
        Execute NTEPilot behavior mapped from a route node name.
        """
        handlers = {
            "PinkPawHeist_CheckReward": self._task_check_reward,
            "PinkPawHeist_EvacuateOnce": self._task_evacuate_once,
            "PinkPawHeist_Once": self._task_confirm_once,
            "PinkPawHeist_CheckDoorOnce": self._task_check_door,
            "PinkPawHeist_CheckGateOnce": self._task_check_gate,
            "PinkPawHeist_CheckGate2Once": self._task_check_gate,
            "PinkPawHeist_CheckEvacuateOnce": self._task_check_evacuate,
            "PinkPawHeist_Core1_Attack_Space": self._task_attack_space,
            "PinkPawHeist_Core1_Log_FightG1": lambda: self._task_log("等待G层战斗1"),
            "PinkPawHeist_Core1_Log_FightG2": lambda: self._task_log("等待G层战斗2"),
            "PinkPawHeist_LogMessage": lambda: self._task_log("粉爪日志"),
            "SceneClickCloseButton": self._task_click_safe_area,
            "SceneClickBlankToExit": self._task_click_safe_area,
            "SceneAnyEnterWorld": self._task_click_safe_area,
            "SceneAnyEnterCityTycoonsMenu": self._task_enter_city_tycoon,
            "RealTimeConfirmTeleportPhone": self._task_click_interact,
            "PinkPawHeist_CityTycoonToHethereauHobbies": lambda: RouteResult(self._recognize_once("PinkPawHeist_CityTycoonToHethereauHobbies")),
            "PinkPawHeist_HethereauHobbiesToHeistMap": lambda: RouteResult(self._recognize_once("PinkPawHeist_HethereauHobbiesToHeistMap")),
        }
        handler = handlers.get(task_name)
        if handler is None:
            raise ScriptError(f"Unsupported PinkPaw node: {task_name}")
        return handler()

    def run_recognition(self, node_name: str, image: Any = None) -> RouteResult:
        """执行一次识别节点。
        Run one recognition node.
        """
        return RouteResult(self._recognize_once(node_name, image=image))

    def screenshot_image(self) -> Any:
        """截取并返回当前画面。
        Capture and return the current screen image.
        """
        self.device.screenshot()
        return self.device.image

    def _recognize_once(self, node_name: str, image: Any = None) -> bool:
        """识别粉爪节点。
        Recognize a PinkPaw node.
        """
        if image is None:
            self.device.screenshot()
            image = self.device.image
        if node_name == "PinkPawHeist_CheckReward":
            return self._ocr_contains((23, 239, 264, 302), ["本局收益", "Round", "Profit"])
        if node_name in {"PinkPawHeist_CheckDoorOnce", "PinkPawHeist_CheckGateOnce", "PinkPawHeist_CheckGate2Once"}:
            return self._ocr_contains((700, 300, 1060, 520), ["开门", "强制", "Open", "Force"])
        if node_name == "PinkPawHeist_CheckEvacuateOnce":
            return self._ocr_contains((650, 450, 900, 550), ["确认撤离", "撤离", "Confirm", "Retreat"])
        if node_name == "PinkPawHeist_CheckMonsterOnce":
            return self._check_monster_color(image)
        if node_name in {"PinkPawHeist_Core3_CheckInteractPinkOnce", "PinkPawHeist_Core3_CheckInteractTemplateOnce"}:
            return self.find_interac()
        if node_name == "PinkPawHeist_Core3_CheckSafeLockPromptOnce":
            return self._appear_optional(HEIST_INTERAC_LOCK_PICK)
        if node_name in {"PinkPawHeist_Core3_CheckLockPickActiveOnce", "PinkPawHeist_Core3_CheckLockPickTextOnce"}:
            return self._ocr_contains((700, 390, 860, 470), ["撬锁", "锁中"])
        if node_name == "PinkPawHeist_Core3_CheckLockPickActiveTemplateOnce":
            return self._appear_optional(HEIST_LOCK_PICK)
        if node_name == "PinkPawHeist_DetectXiaoZhi":
            return self._ocr_contains((765, 374, 974, 411), ["小吱", "Chiz"])
        if node_name == "PinkPawHeist_CityTycoonToHethereauHobbies":
            return self._ocr_contains((520, 260, 810, 365), ["都市闲趣", "Hethereau", "Hobbies"])
        if node_name == "PinkPawHeist_HethereauHobbiesToHeistMap":
            return self._ocr_contains((470, 430, 820, 535), ["粉爪", "大劫案", "Heist"])
        if node_name == "InWorld":
            return self._is_in_team_in_image(image) or self._ocr_contains((1120, 0, 1275, 90), ["F5"])
        if node_name == "InCityTycoonMenu":
            return self._ocr_contains((500, 80, 850, 160), ["都市", "大亨", "City"])
        if node_name == "InHethereauHobbiesMenu":
            return self._ocr_contains((430, 80, 860, 170), ["都市闲趣", "Hethereau", "Hobbies"])
        raise ScriptError(f"Unsupported PinkPaw recognition node: {node_name}")

    def find_interac(self, include_text: bool = False) -> bool:
        """查找普通交互提示。
        Find a normal interaction prompt.
        """
        self.device.screenshot()
        if self.appear(INTERACT, offset=50, similarity=0.65):
            return True
        if self._appear_optional(INTERACTABLE):
            return True
        if self._appear_optional(HEIST_INTERAC_LOCK_PICK):
            return True
        if include_text:
            return self._ocr_contains((700, 300, 1080, 560), ["F", "开门", "强制", "撤离", "撬锁", "Open", "Retreat"])
        return False

    def _screencap(self) -> Any:
        """截图并返回图像。
        Capture and return the current image.
        """
        self.device.screenshot()
        return self.device.image

    def next_frame(self) -> bool:
        """等待一个轮询帧。
        Wait one polling frame.
        """
        self.sleep(WAIT_UNTIL_POLL_INTERVAL, check_reward=False, scaled=False)
        return True

    def wait_team_ui_settle(self) -> bool:
        """等待队伍 UI 稳定。
        Wait until the team UI settles.
        """
        self.wait_until(lambda: not self.is_in_team(), time_out=1, raise_if_not_found=False)
        self.wait_until(self.is_in_team, time_out=30, settle_time=0.25, raise_if_not_found=False)
        self.sleep(0.1, check_reward=False, scaled=False)
        return True

    def is_in_team(self) -> bool:
        """判断当前是否在可操作队伍界面。
        Determine whether the current screen is the playable team UI.
        """
        return self._is_in_team_in_image(self._screencap())

    def _is_black_screen_in_image(self, image: Any) -> bool:
        """用亮度判断黑屏加载。
        Detect black loading screens by brightness.
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return False
        sample = image[::8, ::8, :3]
        if sample.size == 0:
            return False
        max_ch = sample.max(axis=2)
        return float(max_ch.mean()) <= BLACK_SCREEN_MEAN_THRESHOLD and int((max_ch >= BLACK_SCREEN_BRIGHT_PIXEL_THRESHOLD).sum()) <= BLACK_SCREEN_BRIGHT_PIXEL_COUNT

    def _is_in_team_in_image(self, image: Any) -> bool:
        """检测队伍 UI 的亮色特征。
        Detect bright features of the team UI.
        """
        crop = self._crop_wh(image, TEAM_HEALTH_SLASH_ROI)
        if crop is None:
            return False
        max_ch = crop.max(axis=2)
        min_ch = crop.min(axis=2)
        bright = (max_ch >= 175) & ((max_ch - min_ch) <= 95)
        return int(bright.sum()) >= 10

    def _current_char_roi_score(self, image: Any, roi: tuple[int, int, int, int], index: int) -> int:
        """计算角色槽位高亮分数。
        Calculate highlight score for a character slot.
        """
        crop = self._crop_wh(image, roi)
        if crop is None:
            return 0
        max_ch = crop.max(axis=2)
        min_ch = crop.min(axis=2)
        sat = max_ch - min_ch
        white = (max_ch >= CURRENT_CHAR_SLOT_WHITE_THRESHOLDS[index]) & (sat <= 65)
        colored = (max_ch >= CURRENT_CHAR_SLOT_COLORED_THRESHOLDS[index]) & (sat >= 55)
        return int((white | colored).sum())

    def _current_char_scores(self, image: Any) -> list[int]:
        """计算四个角色槽位分数。
        Calculate scores for four character slots.
        """
        scores: list[int] = []
        for index in range(4):
            x, y, w, h = CURRENT_CHAR_MARKER_ROI
            roi = (x, y + CURRENT_CHAR_SLOT_SPACING * index, w, h)
            score = self._current_char_roi_score(image, roi, index)
            scores.append(score + CURRENT_CHAR_SLOT_SCORE_BONUS[index])
        return scores

    def _current_char_core_scores(self, image: Any) -> list[int]:
        """计算角色槽位核心分数。
        Calculate core scores for character slots.
        """
        scores: list[int] = []
        for index in range(4):
            x, y, w, h = CURRENT_CHAR_MARKER_CORE_ROI
            roi = (x, y + CURRENT_CHAR_SLOT_SPACING * index, w, h)
            scores.append(self._current_char_roi_score(image, roi, index) * CURRENT_CHAR_CORE_SCORE_WEIGHT)
        return scores

    def _is_current_char_score_accepted(self, scores: list[int], index: int) -> bool:
        """判断目标角色分数是否可信。
        Determine whether the target character score is reliable.
        """
        if not 0 <= index < len(scores):
            return False
        target_score = scores[index]
        best_other = max((score for idx, score in enumerate(scores) if idx != index), default=0)
        return target_score >= CURRENT_CHAR_SLOT_MIN_SCORE[index] and target_score - best_other >= CURRENT_CHAR_SLOT_MIN_MARGIN[index]

    def _is_slot2_core_score_accepted(self, image: Any) -> bool:
        """二号位头像偏暗时使用核心区域确认。
        Confirm slot 2 via core area when the portrait is dim.
        """
        scores = self._current_char_core_scores(image)
        target_score = scores[1]
        best_other = max(score for idx, score in enumerate(scores) if idx != 1)
        return target_score >= CURRENT_CHAR_SLOT2_CORE_MIN_SCORE and target_score - best_other >= CURRENT_CHAR_SLOT2_CORE_MIN_MARGIN

    def get_current_char_index(self, image: Any = None) -> int:
        """返回当前角色槽位索引。
        Return the current character slot index.
        """
        image = self._screencap() if image is None else image
        scores = self._current_char_scores(image)
        if not scores:
            return -1
        best_idx = max(range(len(scores)), key=lambda idx: scores[idx])
        if self._is_current_char_score_accepted(scores, best_idx):
            return best_idx
        return -1

    def is_char_at_index(self, index: int, image: Any = None) -> bool:
        """判断当前角色是否是指定槽位。
        Determine whether current character is at the given slot.
        """
        image = self._screencap() if image is None else image
        index = int(index)
        if self._is_current_char_score_accepted(self._current_char_scores(image), index):
            return True
        if index == 1:
            return self._is_slot2_core_score_accepted(image)
        return False

    def ensure_in_team(self, time_out: float = 2.0) -> bool:
        """尝试关闭弹窗直到回到队伍 UI。
        Try closing blockers until the team UI is visible.
        """
        deadline = time.monotonic() + float(time_out)
        while time.monotonic() < deadline:
            if self.is_in_team():
                return True
            self.send_key("escape", action_name="ensure_in_team", interval=0.3)
            self.sleep(0.05, check_reward=False, scaled=False)
        return self.is_in_team()

    def start_interaction_watch(self) -> bool:
        """开启移动交互监听。
        Start interaction watch while moving.
        """
        self._interaction_watch_active = True
        self._interaction_watch_found = False
        return True

    def stop_interaction_watch(self) -> bool:
        """关闭移动交互监听。
        Stop interaction watch while moving.
        """
        self._interaction_watch_active = False
        self._interaction_watch_found = False
        return True

    def is_lock_pick_active_fast(self) -> bool:
        """快速检测是否正在撬锁。
        Quickly detect whether lock-picking is active.
        """
        return self._recognize_once("PinkPawHeist_Core3_CheckLockPickActiveOnce")

    def wait_lock_pick_active(self, time_out: float = 2, settle_time: float = -1) -> bool:
        """等待撬锁状态出现。
        Wait for lock-picking to become active.
        """
        if self.wait_until(self.is_lock_pick_active_fast, time_out=time_out, settle_time=settle_time):
            return True
        return self.is_lock_pick_active_fast()

    def is_safe_lock_pick_active(self) -> bool:
        """检测保险柜撬锁状态。
        Detect safe lock-picking state.
        """
        return self.is_lock_pick_active_fast() or self._recognize_once("PinkPawHeist_Core3_CheckLockPickActiveTemplateOnce")

    def wait_safe_lock_pick_active(self, time_out: float = 2, settle_time: float = -1) -> bool:
        """等待保险柜撬锁状态。
        Wait for safe lock-picking state.
        """
        return self.wait_until(self.is_safe_lock_pick_active, time_out=time_out, settle_time=settle_time)

    def wait_door_open(self, time_out: float = 1.5) -> bool:
        """等待开门提示。
        Wait for a door-open prompt.
        """
        return self._run_check_node("PinkPawHeist_CheckDoorOnce", timeout=time_out)

    def wait_door(self, timeout: int = 10000) -> bool:
        """等待 Core2 路线开门提示。
        Wait for the Core2 door prompt.
        """
        return self.wait_door_open(time_out=float(timeout) / 1000.0)

    def wait_gate2(self, timeout: int = 10000) -> bool:
        """等待 Core2 路线二号铁门提示。
        Wait for the Core2 gate 2 prompt.
        """
        return self._run_check_node("PinkPawHeist_CheckGate2Once", timeout=float(timeout) / 1000.0)

    def wait_gate(self, timeout: int = 10000) -> bool:
        """等待 Core1 路线铁门提示。
        Wait for the Core1 gate prompt.
        """
        return self._run_check_node("PinkPawHeist_CheckGateOnce", timeout=float(timeout) / 1000.0)

    def _run_check_node(self, node_name: str, timeout: float = 1.5) -> bool:
        """在超时内重复检测一个节点。
        Repeatedly check one node within timeout.
        """
        deadline = time.monotonic() + float(timeout)
        while time.monotonic() < deadline:
            self.raise_if_stopped()
            if self._recognize_once(node_name):
                return True
            time.sleep(0.05)
        return False

    def has_safe_lock_prompt(self) -> bool:
        """检测保险柜交互提示。
        Detect the safe lock-pick prompt.
        """
        return self._recognize_once("PinkPawHeist_Core3_CheckSafeLockPromptOnce")

    def wait_for_interac(self, time_out: float = 10, include_text_fallback: bool = True) -> bool:
        """等待交互点出现。
        Wait for an interaction prompt.
        """
        if self.wait_until(self.find_interac, time_out=time_out):
            return True
        if include_text_fallback:
            return self.find_interac(include_text=True)
        return False

    def loot_safes_while_walking(self, direction: str | list[str] | None = None, min_walk_time: float = 0, time_out: float = 10, hold: bool = False, send_pick: bool = False) -> None:
        """边走边处理保险柜撬锁。
        Loot safes while walking.
        """
        start_time = time.monotonic()
        deadline = start_time + float(time_out)
        earliest_lock_pick_time = start_time + float(min_walk_time)
        direction_keys = self.semantic.normalize_direction(direction)
        for key in direction_keys:
            self.send_key_down(key)
        pick_started = False
        try:
            while time.monotonic() < deadline:
                now = time.monotonic()
                if send_pick and not pick_started and now >= earliest_lock_pick_time:
                    self.send_key_down("interact")
                    pick_started = True
                if self.has_safe_lock_prompt():
                    if now < earliest_lock_pick_time:
                        self.sleep(earliest_lock_pick_time - now)
                    lock_pick_start = time.monotonic()
                    for key in direction_keys:
                        self.send_key_up(key)
                    if self.wait_safe_lock_pick_active(time_out=2, settle_time=0.25):
                        self.wait_until(lambda: not self.is_safe_lock_pick_active(), time_out=10, settle_time=0.5)
                        self.sleep(0.5, check_reward=False, scaled=False)
                    deadline += time.monotonic() - lock_pick_start
                    for key in direction_keys:
                        self.send_key_down(key)
                self.next_frame()
        finally:
            if not hold:
                for key in direction_keys:
                    self.send_key_up(key)
            if send_pick and pick_started:
                self.send_key_up("interact")

    def wait_for_safe_loot(self, time_out: float = 10, raise_timeout: bool = False) -> bool:
        """等待保险柜撬锁开始并结束。
        Wait for safe lock-picking to start and finish.
        """
        deadline = time.monotonic() + float(time_out)
        while time.monotonic() < deadline:
            if self.has_safe_lock_prompt():
                self.wait_safe_lock_pick_active(time_out=2)
            if self.is_safe_lock_pick_active():
                self.wait_until(lambda: not self.is_safe_lock_pick_active(), time_out=10, settle_time=0.5)
                self.sleep(0.5, check_reward=False, scaled=False)
                return True
            self.next_frame()
        if raise_timeout:
            raise AbortException("timeout for wait_for_safe_loot")
        return False

    def has_extract_panel(self) -> bool:
        """检测撤离确认面板。
        Detect extract confirmation panel.
        """
        return self._recognize_once("PinkPawHeist_CheckEvacuateOnce")

    def should_early_extract(self, exit_index: int | None) -> bool:
        """判断是否启用提前撤离。
        Determine whether early extraction is enabled.
        """
        if exit_index is None:
            return False
        return bool(self.early_extract_exit.get(int(exit_index), False))

    def try_open_exit(self, direction: str | list[str] | None = None, exit_index: int | None = None) -> bool:
        """尝试打开撤离点。
        Try to open an exit.
        """
        if not self.wait_for_interac(time_out=4):
            raise AbortException("not found exit interaction")
        for key in self.semantic.normalize_direction(direction):
            self.send_key_up(key)
        if direction is not None:
            self.sleep(0.3, check_reward=False, scaled=False)
        ret = self.wait_until(self.has_extract_panel, pre_action=lambda: self.send_key("interact", interval=0.7), time_out=2.5)
        if ret:
            if self.should_early_extract(exit_index):
                self.log_round_info(f"Exit {exit_index} available, early extract")
                self._release_held_keys()
                if not self.exit_heist():
                    raise AbortException(f"early extract at exit {exit_index} failed")
                raise EarlyExtractException(f"early extracted at exit {exit_index}")
            self.sleep(0.3, check_reward=False, scaled=False)
            self.send_key("escape", interval=0.5)
            self.sleep(0.5, check_reward=False, scaled=False)
        return ret

    def walk_until_extract_panel(self, direction: str | list[str] | None = None, time_out: float = 10) -> bool:
        """边走边按交互直到撤离面板出现。
        Walk and tap interact until the extract panel appears.
        """
        direction_keys = self.semantic.normalize_direction(direction)
        for key in direction_keys:
            self.send_key_down(key)
        try:
            return self.wait_until(self.has_extract_panel, pre_action=lambda: self.send_key("interact", interval=0.25), time_out=time_out, raise_if_not_found=True)
        finally:
            for key in direction_keys:
                self.send_key_up(key)

    def clear_current_combat(self, fighter_mode: str | int = "all_desc") -> None:
        """切战斗角色清怪后切回跑图角色。
        Switch to a fighter, clear combat, then switch back to runner.
        """
        self.switch_to_fighter(check_switched=True, mode=fighter_mode)
        self.fight_until_no_monster(timeout_no_monster=10000, wait_for_monster=True)
        self.switch_to_runner(check_switched=True)

    def check_monster(self) -> bool:
        """检测怪物血条。
        Detect monster HP bars.
        """
        self.device.screenshot()
        return self._check_monster_color(self.device.image)

    def wait_monster(self, timeout: int = 6000) -> bool:
        """等待怪物出现。
        Wait for monsters to appear.
        """
        deadline = time.monotonic() + float(timeout) / 1000.0
        while time.monotonic() < deadline:
            if self.check_monster():
                return True
            self.sleep(0.2)
        return False

    def attack_cycle(self, times: int = 3, loot: bool = False) -> None:
        """执行基础攻击循环。
        Execute basic attack cycles.
        """
        for _ in range(times):
            self._task_attack_space()
        if loot:
            self.send_key("interact")

    def fight_until_no_monster(self, timeout_no_monster: int = 10000, wait_for_monster: bool = True, role_to_switch_back: str | None = None, loot: bool = False, attack_cycles: int = 3) -> bool:
        """攻击直到一段时间内检测不到怪物。
        Attack until no monster is detected for a duration.
        """
        if wait_for_monster and not self.wait_monster(timeout=timeout_no_monster):
            return False
        no_monster_start: float | None = None
        while True:
            if self.check_monster():
                no_monster_start = None
                self.attack_cycle(times=attack_cycles, loot=loot)
            else:
                now = time.monotonic()
                if no_monster_start is None:
                    no_monster_start = now
                elif now - no_monster_start >= float(timeout_no_monster) / 1000.0:
                    break
                self.sleep(0.05)
        if role_to_switch_back:
            self.switch_to_key(role_to_switch_back)
        return True

    def switch_to_key(self, key: str) -> str:
        """直接多次短按角色键。
        Tap a character key several times directly.
        """
        key = self._norm_key(key)
        for _ in range(4):
            self.send_key(key)
            self.sleep(0.2)
        return key

    def _send_current_switch_key(self) -> str | None:
        """发送当前切换候选键。
        Send the current switch candidate key.
        """
        state = self._switch_state
        if state is None:
            return None
        key = state.current_key
        if state.role == self.ROLE_FIGHTER:
            self._current_fighter_key = key
        state.deadline = time.monotonic() + SWITCH_CHECK_DURATION
        self._next_switch_poll_at = time.monotonic() + 0.05
        self.send_key(key)
        return key

    def _clear_switch_state(self) -> None:
        """清空切人状态。
        Clear switch state.
        """
        self._switch_state = None
        self._next_switch_poll_at = 0.0

    def _handle_dead_switch_candidate(self, state: CharacterSwitchState) -> None:
        """切人失败时尝试下一个候选。
        Try the next candidate when switching fails.
        """
        key = state.current_key
        self.log_warning(f"{state.role} char {key} may be dead, try next")
        if state.role == self.ROLE_FIGHTER and key not in self._dead_fighter_keys:
            self._dead_fighter_keys.append(key)
        self.ensure_in_team()
        if not state.advance():
            self._clear_switch_state()
            raise AbortException(f"{state.role} {state.keys} dead or empty")
        self._send_current_switch_key()

    def _poll_character_switch(self) -> None:
        """后台确认切人状态。
        Poll character switch state in the background.
        """
        if self._switch_state is None or self._handling_switch_state:
            return
        now = time.monotonic()
        if now < self._next_switch_poll_at:
            return
        self._next_switch_poll_at = now + 0.1
        state = self._switch_state
        if now > state.deadline:
            self._clear_switch_state()
            return
        image = self._screencap()
        if self._is_black_screen_in_image(image):
            state.deadline = max(state.deadline, time.monotonic() + SWITCH_BLACK_SCREEN_EXTENSION)
            return
        if self._is_in_team_in_image(image):
            return
        self._handling_switch_state = True
        try:
            self._handle_dead_switch_candidate(state)
        finally:
            self._handling_switch_state = False

    def _wait_character_switch_success(self, role: str, key: str | None) -> str | None:
        """等待角色槽位高亮确认。
        Wait for character slot highlight confirmation.
        """
        if key is None:
            return None
        retry_count = 0
        retry_key = str(key)
        not_team_since: float | None = None
        old_handling = self._handling_switch_state
        self._handling_switch_state = True
        try:
            while self._switch_state is not None:
                state = self._switch_state
                last_key = state.current_key
                if retry_key != last_key:
                    retry_key = last_key
                    retry_count = 0
                now = time.monotonic()
                if now > state.deadline:
                    if retry_count < SWITCH_CONFIRM_RETRY_COUNT:
                        retry_count += 1
                        self.send_key(last_key, action_name=f"switch_char_retry:{last_key}", interval=-1)
                        state.deadline = time.monotonic() + SWITCH_CONFIRM_RETRY_WINDOW
                        not_team_since = None
                        continue
                    self._clear_switch_state()
                    return last_key
                self.send_key(last_key, action_name="switch_char", interval=0.5)
                image = self._screencap()
                if self.is_char_at_index(int(self._slot_from_switch_key(last_key)) - 1, image=image):
                    self._clear_switch_state()
                    return last_key
                if self._is_black_screen_in_image(image):
                    state.deadline = max(state.deadline, time.monotonic() + SWITCH_BLACK_SCREEN_EXTENSION)
                    not_team_since = None
                    self.sleep(WAIT_UNTIL_POLL_INTERVAL, check_reward=False, scaled=False)
                    continue
                if self._is_in_team_in_image(image):
                    not_team_since = None
                else:
                    not_team_since = now if not_team_since is None else not_team_since
                    if now - not_team_since >= SWITCH_DEAD_SETTLE:
                        self._handle_dead_switch_candidate(state)
                        not_team_since = None
                self.sleep(WAIT_UNTIL_POLL_INTERVAL, check_reward=False, scaled=False)
        finally:
            self._handling_switch_state = old_handling
        return key

    def _begin_character_switch(self, role: str, keys: list[str], check_switched: bool = False) -> str | None:
        """开始切换角色。
        Begin character switching.
        """
        normalized = [self._semantic_switch_key(key) for key in keys]
        if not normalized:
            raise AbortException(f"{role} {normalized} dead or empty")
        self._switch_state = CharacterSwitchState(role=role, keys=normalized)
        key = self._send_current_switch_key()
        if check_switched:
            return self._wait_character_switch_success(role, key)
        return key

    def switch_to_runner(self, check_switched: bool = False) -> str | None:
        """切到跑图角色。
        Switch to runner.
        """
        return self._begin_character_switch(self.ROLE_RUNNER, self.config_values.get("runner", []), check_switched)

    def switch_to_avoider(self, check_switched: bool = False) -> str | None:
        """切到避战角色。
        Switch to avoider.
        """
        keys = self.config_values.get("avoider", [])
        if not keys:
            self.log_info("no avoider")
            return None
        return self._begin_character_switch(self.ROLE_AVOIDER, keys, check_switched)

    def switch_to_fighter(self, check_switched: bool = False, mode: str | int = "all_desc") -> str | None:
        """切到战斗角色。
        Switch to fighter.
        """
        config_keys = [self._slot_from_switch_key(key) for key in self.config_values.get("fighter", [])]
        config_keys = [key for key in config_keys if key not in self._dead_fighter_keys]
        if not config_keys:
            raise AbortException("fighter list empty")
        sorted_keys = sorted(config_keys, key=int)
        if mode == "all_asc":
            keys = sorted_keys
        elif mode == "all_desc":
            keys = sorted_keys[::-1]
        elif isinstance(mode, int):
            index = len(sorted_keys) - 1 if mode == -1 else mode - 1
            if 0 <= index < len(sorted_keys):
                keys = [sorted_keys[index]]
            else:
                keys = [sorted_keys[-1]]
        else:
            keys = sorted_keys[::-1]
        return self._begin_character_switch(self.ROLE_FIGHTER, [f"switch_{key}" for key in keys], check_switched)

    def avoider_strategy_index(self) -> int:
        """返回避战路线索引。
        Return avoidance strategy index.
        """
        if not self.config_values.get("avoider", []):
            return -1
        method_name = self.config_values.get("avoid_method")
        if method_name not in self.avoid_methods:
            return 0
        return self.avoid_methods.index(str(method_name))

    def perform_avoidance_action(self) -> None:
        """执行避战动作。
        Perform avoidance action.
        """
        if self.config_values.get("avoid_method") == self.AVOID_METHOD_ATTACK:
            self.click(down_time=0.6)
            return
        self.send_key_down("forward")
        self.sleep(0.1)
        self.send_key_down("dodge")
        self.sleep(1.0)
        self.send_key_up("dodge")
        self.sleep(0.1)
        self.send_key_up("forward")

    def exit_heist(self) -> bool:
        """确认撤离并记录结果。
        Confirm extraction and log the result.
        """
        self.log_round_info("Confirm extract")
        self.sleep(1.0, check_reward=False, scaled=False)
        result = self.run_task("PinkPawHeist_EvacuateOnce")
        if is_hit(result):
            self.sleep(REWARD_OCR_DELAY_MS / 1000.0, check_reward=False, scaled=False)
            self.notify_pinkpaw_reward(success=True)
            self.sleep(POST_REWARD_DELAY_MS / 1000.0, check_reward=False, scaled=False)
            return True
        self.notify_pinkpaw_reward(success=False)
        return False

    def abort_heist(self) -> None:
        """异常时释放按键并尝试退出。
        Release controls and try to exit on route failure.
        """
        self.log_round_info("Abort and return to main")
        self.release_controls()
        for _ in range(4):
            self.send_key("escape")
            self.sleep(1.0, check_reward=False, scaled=False)
        self.run_task("PinkPawHeist_Once")
        self.sleep(5.0, check_reward=False, scaled=False)
        self.notify_pinkpaw_reward(success=False)

    def _poll_quick_pick(self) -> None:
        """交互按住状态下定频点击交互。
        Tap interact at intervals while interact is held.
        """
        if not self._quick_pick_active:
            return
        now = time.monotonic()
        if now < self._quick_pick_ready_at or now < self._next_quick_pick_at:
            return
        self.semantic.tap("interact")
        self._next_quick_pick_at = now + INTERACT_HOLD_INTERVAL

    def _has_timing_sensitive_key_held(self) -> bool:
        """判断是否按住影响走位时间的键。
        Determine whether timing-sensitive keys are held.
        """
        return bool(self._held_keys & {"forward", "back", "left", "right", "dodge", "jump", "skill_e"})

    def _check_still_in_heist(self) -> None:
        """低频检测是否仍在粉爪局内。
        Check at low frequency whether still inside the heist round.
        """
        now = time.monotonic()
        if now - self.last_check_reward_time <= REWARD_CHECK_INTERVAL:
            return
        self.last_check_reward_time = now
        if not self._recognize_once("PinkPawHeist_CheckReward"):
            self.check_reward_fail_count += 1
            if self.check_reward_fail_count >= 2:
                raise AbortException("PinkPawHeist_CheckReward 连续 2 次检测失败")
        else:
            self.check_reward_fail_count = 0

    @staticmethod
    def _slot_from_switch_key(key: str) -> str:
        """把 switch_3 还原成角色槽位 3。
        Convert switch_3 back to slot 3.
        """
        text = str(key).strip().lower()
        return text.split("_", 1)[1] if text.startswith("switch_") else text

    @staticmethod
    def _semantic_switch_key(key: str) -> str:
        """把角色槽位转换为语义切人键。
        Convert a character slot into a semantic switch key.
        """
        text = str(key).strip().lower()
        return text if text.startswith("switch_") else f"switch_{text}"

    @staticmethod
    def _crop_wh(image: Any, roi: tuple[int, int, int, int]) -> np.ndarray | None:
        """按 x/y/w/h 裁剪图像。
        Crop image by x/y/w/h.
        """
        if image is None or not isinstance(image, np.ndarray):
            return None
        x, y, w, h = roi
        height, width = image.shape[:2]
        x1 = max(0, min(width, int(x)))
        y1 = max(0, min(height, int(y)))
        x2 = max(x1, min(width, int(x + w)))
        y2 = max(y1, min(height, int(y + h)))
        if x2 <= x1 or y2 <= y1:
            return None
        return image[y1:y2, x1:x2, :3]

    def wait_and_interact(self, direction: str | list[str] | None = None, interact: bool = True, key_up_sleep: float | None = None, is_lock: bool = False, time_out: float = 10) -> bool:
        """等待交互提示并点击交互。
        Wait for an interaction prompt and tap interact.
        """
        direction_keys = self.semantic.normalize_direction(direction)
        if not self.wait_until(lambda: self.find_interac(include_text=True), time_out=time_out):
            raise AbortException("timeout for wait_and_interact")
        if interact:
            for key in direction_keys:
                self.send_key_up(key)
            self.sleep(self.interaction_pause if key_up_sleep is None else key_up_sleep, check_reward=False, scaled=False)
            self.send_key("interact")
            if is_lock:
                self.sleep(float(time_out), check_reward=False, scaled=False)
        return True

    def wait_until(self, condition: Any, time_out: float = 0, pre_action: Any = None, post_action: Any = None, settle_time: float = -1, raise_if_not_found: bool = False, **kwargs: Any) -> bool:
        """轮询等待条件成立。
        Poll until a condition is true.
        """
        timeout = 10.0 if not time_out or time_out <= 0 else float(time_out)
        deadline = time.monotonic() + timeout
        settled_at: float | None = None
        while time.monotonic() < deadline:
            if pre_action is not None:
                pre_action()
            if bool(condition()):
                if post_action is not None:
                    post_action()
                if settle_time is not None and settle_time >= 0:
                    settled_at = settled_at or time.monotonic()
                    if time.monotonic() - settled_at >= settle_time:
                        return True
                else:
                    return True
            else:
                settled_at = None
            self.sleep(0.05, check_reward=False, scaled=False)
        if raise_if_not_found:
            raise AbortException("timeout for wait_until")
        return False

    def _task_check_reward(self) -> RouteResult:
        """检测是否仍在粉爪局内。
        Check whether the route is still inside a PinkPaw round.
        """
        return RouteResult(self._recognize_once("PinkPawHeist_CheckReward"))

    def _task_evacuate_once(self) -> RouteResult:
        """点击撤离确认。
        Tap retreat confirmation.
        """
        if not self._recognize_once("PinkPawHeist_CheckEvacuateOnce"):
            return RouteResult(False)
        self.device.click((770, 504))
        return RouteResult(True)

    def _task_confirm_once(self) -> RouteResult:
        """点击确认按钮。
        Tap a confirmation button.
        """
        self.device.click((770, 473))
        return RouteResult(True)

    def _task_check_door(self) -> RouteResult:
        """检测开门。
        Check door prompt.
        """
        return RouteResult(self._recognize_once("PinkPawHeist_CheckDoorOnce"))

    def _task_check_gate(self) -> RouteResult:
        """检测铁门。
        Check gate prompt.
        """
        return RouteResult(self._recognize_once("PinkPawHeist_CheckGateOnce"))

    def _task_check_evacuate(self) -> RouteResult:
        """检测撤离确认。
        Check retreat prompt.
        """
        return RouteResult(self._recognize_once("PinkPawHeist_CheckEvacuateOnce"))

    def _task_attack_space(self) -> RouteResult:
        """执行一轮跳跃加攻击。
        Execute one jump plus attack cycle.
        """
        self.send_key("jump")
        self.send_key("attack")
        return RouteResult(True)

    def _task_log(self, message: str) -> RouteResult:
        """记录粉爪日志。
        Log a PinkPaw message.
        """
        logger.info(message)
        return RouteResult(True)

    def _task_click_safe_area(self) -> RouteResult:
        """点击安全区域。
        Click the safe area.
        """
        self.device.click((640, 360))
        return RouteResult(True)

    def _task_enter_city_tycoon(self) -> RouteResult:
        """尝试打开都市大亨入口。
        Try to open city tycoon entry.
        """
        self.send_key("escape")
        self.send_key("skill_g")
        return RouteResult(True)

    def _task_click_interact(self) -> RouteResult:
        """点击交互。
        Tap interact.
        """
        self.send_key("interact")
        return RouteResult(True)

    def _ocr_contains(self, rect: tuple[int, int, int, int], expected: list[str]) -> bool:
        """OCR 判断区域文字是否包含任一目标。
        Check whether OCR text contains any expected string.
        """
        try:
            text = self.ocr(rect, model="cn", screenshot=False)
        except Exception as exc:
            logger.debug("PinkPaw OCR failed for %s: %s", rect, exc)
            return False
        lowered = text.lower()
        return any(item.lower() in lowered for item in expected)

    def _appear_optional(self, template: Template | None, similarity: float = 0.65) -> bool:
        """匹配可选模板，模板不存在时明确返回 False。
        Match an optional template and explicitly return False when missing.
        """
        if template is None:
            return False
        return self.appear(template, offset=20, similarity=similarity)

    @staticmethod
    def _check_monster_color(image: Any) -> bool:
        """用源路线的血条颜色范围检测怪物。
        Detect monsters using the source route HP-bar color range.
        """
        if image is None or not isinstance(image, np.ndarray):
            return False
        roi = image[27:666, 33:1255]
        if roi.size == 0:
            return False
        lower = np.array([242, 31, 32], dtype=np.uint8)
        upper = np.array([244, 33, 34], dtype=np.uint8)
        mask = cv2.inRange(roi, lower, upper)
        return int(mask.sum() // 255) >= 3

    def _scale_route_duration(self, duration: float) -> float:
        """按路线倍率缩放时间。
        Scale route duration by route timing scale.
        """
        return max(0.0, duration * self.route_timing_scale)

    def _check_interval(self, name: str, interval: float | None) -> bool:
        """按动作名限流。
        Rate-limit by action name.
        """
        if interval is None or interval < 0:
            return True
        now = time.monotonic()
        last = self._last_action_at.get(name, 0.0)
        if now - last < interval:
            return False
        self._last_action_at[name] = now
        return True

    def _release_held_keys(self) -> None:
        """释放路线记录的所有按键。
        Release all keys tracked by the route.
        """
        for key in list(self._held_keys):
            try:
                self.send_key_up(key)
            except Exception:
                logger.debug("Failed to release key %s", key, exc_info=True)
        self._held_keys.clear()
        self.semantic.release_all()

    def release_controls(self) -> None:
        """释放所有触控。
        Release all controls.
        """
        self._release_held_keys()

    def notify_pinkpaw_reward(self, context: Any = None, success: bool = False, fansi: int = 0, pinkcoins: int = 0) -> None:
        """记录粉爪收益结果，不伪造 OCR 金额。
        Log PinkPaw reward result without faking OCR amounts.
        """
        if success:
            logger.info("粉爪大劫案撤离成功")
        else:
            logger.warning("粉爪大劫案撤离失败")

    def log_round_info(self, message: str) -> None:
        """记录路线信息。
        Log route information.
        """
        logger.info("[PinkPaw] %s", message)

    def log_warning(self, message: str) -> None:
        """记录路线警告。
        Log route warning.
        """
        logger.warning("[PinkPaw] %s", message)

    def log_info(self, message: str) -> None:
        """记录普通信息。
        Log normal information.
        """
        logger.info("[PinkPaw] %s", message)

    def log_error(self, message: str, exc: Exception | None = None) -> None:
        """记录错误。
        Log an error.
        """
        if exc is None:
            logger.error("[PinkPaw] %s", message)
        else:
            logger.error("[PinkPaw] %s: %s", message, exc)

    def __getattr__(self, name: str) -> Any:
        """禁止未知调用静默成功。
        Forbid unknown calls from silently succeeding.
        """
        raise ScriptError(f"Unsupported PinkPaw runtime call: {name}")

    @staticmethod
    def _norm_key(key: str) -> str:
        """规范化语义键。
        Normalize semantic key.
        """
        return str(key).strip().lower()
