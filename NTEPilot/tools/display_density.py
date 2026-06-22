"""设备 DPI 校准工具。
Device DPI calibration tool.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-22
Date: 2026-06-22
"""

from __future__ import annotations

import time

from NTEPilot.device.connection import DisplayDensityState
from NTEPilot.ui.ui import UI
from template import Template
from template.ui import F1, F2, F3
from utils.exceptions import RequestHumanTakeover
from utils.logger import logger


class DisplayDensityCalibrator(UI):
    """通过 ADB 逐个尝试 DPI，直到 F1/F2/F3 UI 可匹配。
    Try DPI values one by one via ADB until F1/F2/F3 UI templates match.
    """

    DEFAULT_MIN_DPI = 10
    DEFAULT_MAX_DPI = 999
    DEFAULT_STARTUP_TIMEOUT = 90.0
    DEFAULT_RESTART_SETTLE_SECONDS = 3.0
    TARGET_TEMPLATES: tuple[Template, ...] = (F1, F2, F3)

    def ensure_in_game(self) -> None:
        """跳过任务通用进游戏前置流程。
        Skip the generic task preflight game check.

        这个工具本身会反复改 DPI 并重启游戏，不能让通用前置流程先卡在旧 DPI。
        This tool repeatedly changes DPI and restarts the game itself, so generic preflight must not run first.
        """
        logger.info('Skip generic ensure_in_game for display density calibration')

    def run(self) -> None:
        """运行 DPI 校准。
        Run DPI calibration.

        Raises:
            RequestHumanTakeover: 从 10 到 999 都无法匹配 F1/F2/F3 时抛出。
                                  Raised when no DPI from 10 to 999 matches F1/F2/F3.
        """
        logger.hr('DISPLAY DENSITY CALIBRATION', level=1)
        original_state = self.device.get_display_density_state()
        matched_density: int | None = None
        should_restore = True

        try:
            for density in self._density_candidates():
                logger.hr(f'TRY DPI {density}', level=2)
                if self._try_density(density):
                    matched_density = density
                    should_restore = False
                    logger.info(f'DPI calibration succeeded: {density}')
                    break

            if matched_density is None:
                raise RequestHumanTakeover('DPI 10-999 都无法匹配 F1/F2/F3')
        finally:
            if should_restore:
                logger.warning('DPI calibration failed or stopped, restoring original density')
                self.device.restore_display_density(original_state)
                self._restart_app_for_density()

    def _density_candidates(self) -> range:
        """生成 DPI 尝试顺序。
        Build the DPI trial order.

        Returns:
            从 10 到 999 的连续 DPI 序列。
            Continuous DPI sequence from 10 to 999.
        """
        return range(self.DEFAULT_MIN_DPI, self.DEFAULT_MAX_DPI + 1)

    def _try_density(self, density: int) -> bool:
        """尝试单个 DPI 并检测目标 UI。
        Try one DPI and detect target UI.

        Args:
            density: 当前尝试的 DPI。
                     Current DPI to try.

        Returns:
            F1/F2/F3 任意一个模板命中时返回 True。
            True when any of F1/F2/F3 templates matches.
        """
        self.device.set_display_density(density)
        self._restart_app_for_density()
        return self._wait_until_target_ui()

    def _restart_app_for_density(self) -> None:
        """重启游戏让 DPI 设置生效。
        Restart the game to apply the DPI setting.
        """
        self.device.release_all_minitouch()
        self.device.app_stop_adb()
        time.sleep(self.DEFAULT_RESTART_SETTLE_SECONDS)
        self.device.app_start_adb()
        time.sleep(self.DEFAULT_RESTART_SETTLE_SECONDS)

    def _wait_until_target_ui(self) -> bool:
        """等待进入主界面并检测 F1/F2/F3。
        Wait for the main UI and detect F1/F2/F3.

        Returns:
            超时时间内匹配到目标 UI 时返回 True，否则返回 False。
            True when target UI matches before timeout, otherwise False.
        """
        deadline = time.monotonic() + self.DEFAULT_STARTUP_TIMEOUT
        with self.device.temporary_screenshot_interval(1):
            while time.monotonic() < deadline:
                self.device.screenshot()
                if self.handle_enter_game():
                    continue
                if self._target_ui_appears():
                    return True
        return False

    def _target_ui_appears(self) -> bool:
        """检测 F1/F2/F3 是否出现。
        Detect whether F1/F2/F3 appears.

        Returns:
            任意目标模板匹配成功时返回 True。
            True when any target template matches.
        """
        for template in self.TARGET_TEMPLATES:
            if self.appear(template, offset=30, similarity=0.85):
                logger.info(f'Target UI matched: {template}')
                return True
        return False
