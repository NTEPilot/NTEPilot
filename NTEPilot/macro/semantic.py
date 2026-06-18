"""语义动作到 NTEPilot 触控的适配层。
Adapter from semantic macro actions to NTEPilot touch controls.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Iterable
from typing import Any

from NTEPilot.device.control import JOYSTICK_CENTER, JOYSTICK_OFFSET
from template import Template
from template.control import BA, DODGE, JUMP, LOCK, SKILL_E, SKILL_G, SKILL_Q, SKILL_R, SWITCH_1, SWITCH_2, SWITCH_3
from template.ui import F5, INTERACT
from utils.exceptions import ScriptError
from utils.logger import logger


DIRECTION_KEYS = {"forward", "back", "left", "right"}
DIRECTION_VECTOR = {
    "forward": (0, -1),
    "back": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

SWITCH_4_FALLBACK_POS = (1190, 455)


class SemanticController:
    """维护语义按键状态并发送手机触控。
    Maintain semantic key state and send mobile touch controls.
    """

    def __init__(self, device: Any) -> None:
        """保存设备对象并初始化按键状态。
        Store the device object and initialize key state.

        Args:
            device: NTEPilot 设备对象。
                    NTEPilot device object.
        """
        self.device = device
        self.held_keys: set[str] = set()
        self._joystick_active = False
        self._held_contacts: dict[str, int] = {}
        self._next_contact = 0
        self._lock = threading.Lock()

    def key_down(self, key: str) -> bool:
        """按下一个语义键。
        Press one semantic key.

        Args:
            key: 语义键名。
                 Semantic key name.

        Returns:
            是否处理成功。
            Whether the key was handled.
        """
        key = self.normalize_key(key)
        if key in DIRECTION_KEYS:
            self.held_keys.add(key)
            self._sync_joystick()
            return True
        if key == "interact":
            self.held_keys.add(key)
            return True
        if key in {"attack", "lock", "jump", "dodge", "skill_e", "skill_q", "skill_g", "skill_r"}:
            self.held_keys.add(key)
            self._press_contact(key)
            return True
        self.held_keys.add(key)
        self.device.press(self._target_for_key(key))
        return True

    def key_up(self, key: str) -> bool:
        """松开一个语义键。
        Release one semantic key.

        Args:
            key: 语义键名。
                 Semantic key name.

        Returns:
            是否处理成功。
            Whether the key was handled.
        """
        key = self.normalize_key(key)
        self.held_keys.discard(key)
        if key in DIRECTION_KEYS:
            self._sync_joystick()
            return True
        if key == "interact":
            return True
        if key in {"attack", "lock", "jump", "dodge", "skill_e", "skill_q", "skill_g", "skill_r"}:
            self._release_contact(key)
            return True
        self.device.release()
        return True

    def tap(self, key: str, duration: float = 0.02) -> bool:
        """短按一个语义键。
        Tap one semantic key.

        Args:
            key: 语义键名。
                 Semantic key name.
            duration: 按住时长，单位秒。
                      Hold duration in seconds.

        Returns:
            是否处理成功。
            Whether the key was handled.
        """
        key = self.normalize_key(key)
        if key in DIRECTION_KEYS:
            self.key_down(key)
            time.sleep(max(duration, 0.0))
            self.key_up(key)
            return True
        if key == "camera_reset":
            self.camera_reset(duration=duration)
            return True
        if key == "escape":
            self.device.adb_shell(["input", "keyevent", "4"])
            return True
        target = self._target_for_key(key)
        if duration > 0.06:
            self.device.long_click(target, duration=max(duration, 0.0))
            return True
        self.device.click(target)
        return True

    def click(self, x: float = -1, y: float = -1, key: str = "attack", down_time: float = 0.01) -> bool:
        """执行鼠标点击语义动作。
        Execute a semantic mouse click.

        Args:
            x: 原桌面 X 坐标或比例；触控后端默认忽略并使用语义按钮。
               Original desktop x coordinate or ratio; touch backend uses semantic target by default.
            y: 原桌面 Y 坐标或比例；触控后端默认忽略并使用语义按钮。
               Original desktop y coordinate or ratio; touch backend uses semantic target by default.
            key: 鼠标语义键。
                 Semantic mouse key.
            down_time: 按住时长。
                       Hold duration.

        Returns:
            是否处理成功。
            Whether the click was handled.
        """
        key = self.normalize_key(key)
        if key == "camera_reset":
            self.camera_reset(duration=max(float(down_time), 0.01))
            return True
        if x >= 0 and y >= 0:
            target = self._normalize_position(x, y)
            if down_time > 0.05:
                self.device.long_click(target, duration=down_time)
                return True
            self.device.click(target)
            return True
        if down_time > 0.05:
            self.device.long_click(self._target_for_key(key), duration=down_time)
            return True
        return self.tap(key)

    def release_all(self) -> None:
        """释放所有触控状态。
        Release all touch state.
        """
        self.held_keys.clear()
        self._release_joystick()
        self._release_action_contacts()
        try:
            self.device.release_all_minitouch()
        except Exception as exc:
            logger.warning("Failed to release macro controls: %s", exc)
            logger.debug("Failed to release macro controls", exc_info=True)

    def camera_reset(self, duration: float = 0.15, start: tuple[int, int] | None = None) -> bool:
        """执行一次镜头校正拖拽。
        Perform one camera reset drag.
        """
        start_point = start or (640, 360)
        end_point = (min(1270, start_point[0] + 120), start_point[1])
        self.device.drag(start_point, end_point)
        if duration > 0.05:
            time.sleep(max(0.0, duration - 0.05))
        return True

    def _target_for_key(self, key: str) -> Template | tuple[int, int]:
        """返回语义键对应的点击目标。
        Return the click target for a semantic key.
        """
        targets: dict[str, Template | tuple[int, int]] = {
            "attack": BA,
            "interact": INTERACT,
            "jump": JUMP,
            "dodge": DODGE,
            "lock": LOCK,
            "skill_e": SKILL_E,
            "skill_q": SKILL_Q,
            "skill_g": SKILL_G,
            "skill_r": SKILL_R,
            "switch_1": SWITCH_1,
            "switch_2": SWITCH_2,
            "switch_3": SWITCH_3,
            "switch_4": SWITCH_4_FALLBACK_POS,
            "city_tycoon_menu": F5,
        }
        if key not in targets:
            raise ScriptError(f"Unsupported semantic key: {key}")
        return targets[key]

    def _sync_joystick(self) -> None:
        """根据当前方向键集合更新摇杆。
        Update joystick based on currently held direction keys.
        """
        vx = 0
        vy = 0
        for key in self.held_keys & DIRECTION_KEYS:
            dx, dy = DIRECTION_VECTOR[key]
            vx += dx
            vy += dy
        if vx == 0 and vy == 0:
            self._release_joystick()
            return
        angle = math.degrees(math.atan2(vx, -vy))
        if angle < 0:
            angle += 360
        end_point = (
            round(JOYSTICK_CENTER[0] + math.sin(math.radians(angle)) * JOYSTICK_OFFSET),
            round(JOYSTICK_CENTER[1] - math.cos(math.radians(angle)) * JOYSTICK_OFFSET),
        )
        if not self._joystick_active:
            self.device.keep_drag_minitouch(JOYSTICK_CENTER, end_point, contact=1)
            self._joystick_active = True
            return
        builder = self.device.minitouch_builder
        builder.move(*end_point, contact=1).commit()
        builder.send()

    def _release_joystick(self) -> None:
        """释放摇杆触点。
        Release joystick contact.
        """
        if not self._joystick_active:
            return
        try:
            self.device.release_minitouch(contact=1)
        finally:
            self._joystick_active = False

    def _release_action_contacts(self) -> None:
        """释放所有动作触点。
        Release all action contacts.
        """
        for key in list(self._held_contacts):
            self._release_contact(key)

    def _press_contact(self, key: str) -> None:
        """用独立触点按住动作键。
        Hold an action key with a dedicated contact.
        """
        with self._lock:
            if key in self._held_contacts:
                return
            contact = self._allocate_contact()
            self._held_contacts[key] = contact
        target = self._target_for_key(key)
        if isinstance(target, Template):
            x, y = target.pos
        else:
            x, y = target
        self.device.press_minitouch(x, y, contact=contact)

    def _release_contact(self, key: str) -> None:
        """释放独立动作触点。
        Release a dedicated action contact.
        """
        with self._lock:
            contact = self._held_contacts.pop(key, None)
        if contact is None:
            return
        self.device.release_minitouch(contact=contact)

    def _allocate_contact(self) -> int:
        """分配不与摇杆冲突的触点。
        Allocate a contact that does not conflict with the joystick.
        """
        used = set(self._held_contacts.values())
        used.add(1)
        for contact in range(2, 10):
            if contact not in used:
                return contact
        self._next_contact += 1
        return 10 + self._next_contact

    @staticmethod
    def _normalize_position(x: float, y: float) -> tuple[int, int]:
        """把比例或像素坐标统一成 1280x720 触控坐标。
        Normalize ratio or pixel coordinates into 1280x720 touch coordinates.
        """
        px = round(float(x) * 1280) if 0 <= x <= 1 else round(float(x))
        py = round(float(y) * 720) if 0 <= y <= 1 else round(float(y))
        return (max(0, min(1279, px)), max(0, min(719, py)))

    @staticmethod
    def normalize_key(key: str) -> str:
        """规范化语义键名。
        Normalize a semantic key name.
        """
        return str(key).strip().lower()

    @staticmethod
    def normalize_direction(value: str | Iterable[str] | None) -> list[str]:
        """规范化方向参数。
        Normalize a direction argument.
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [SemanticController.normalize_key(value)]
        return [SemanticController.normalize_key(item) for item in value]
