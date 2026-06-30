import time
import threading
from dataclasses import dataclass

import numpy as np

from NTEPilot.ui.ui import UI
from NTEPilot.ui.page import FISH_MAIN_PAGE, FISH_SHOP, FISH_STORAGE_PAGE
from template.fish import *
from template.ui import GET_ITEM, INTERACT, SAFE_AREA

from utils.logger import logger

@dataclass(frozen=True)
class FishControlSignal:
    """钓鱼按键控制信号。
    Fishing key control signal.

    Args:
        direction: 控制方向，-1 表示左，0 表示释放，1 表示右。
                   Control direction: -1 for left, 0 for release, 1 for right.
        duration: 从 created_at 开始保持该方向的秒数。
                  Seconds to keep the direction from created_at.
        created_at: 主线程生成指令时的时间戳。
                    Timestamp when the main thread created the signal.
    """

    direction: int
    duration: float
    created_at: float

    @property
    def expires_at(self) -> float:
        """返回指令过期时间。
        Return the expiration timestamp of the signal.
        """
        return self.created_at + self.duration


class Fish(UI):
    FISH_BAR_RECT = (404, 44, 880, 55)

    GREEN_BAR_RGB = (58, 240, 177)
    YELLOW_CURSOR_RGB = (255, 253, 160)
    _pending_control_signal: FishControlSignal | None

    @property
    def green_bar_left(self):
        return 0.5 - self.green_bar_safe_proportion / 2

    @property
    def green_bar_right(self):
        return 0.5 + self.green_bar_safe_proportion / 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.green_bar_safe_proportion = self.config["tools.fish.green_bar_safe_proportion"]
        self.green_bar_length_tolerance = self.config["tools.fish.green_bar_length_tolerance"]
        self.green_bar_velocity_abrupt_threshold = self.config["tools.fish.green_bar_velocity_abrupt_threshold"]
        self.input_delay = float(self.config["tools.fish.input_delay"])
        self.yellow_cursor_speed = self.config["tools.fish.yellow_cursor_speed"]

    def run(self):
        logger.hr('FISH', level=1)
        
        with self.device.temporary_screenshot_interval(0.5):
            while True:
                self.device.screenshot()
                if self.appear(HOOK):
                    break
                if self.appear(INTERACT):
                    self.device.click(INTERACT)
                    continue
                if self.appear(FISH_READY):
                    self.device.click(START_TO_FISH)
                    continue

        while True:
            self.device.click(HOOK)
            self.device.sleep((0.1, 0.2))
            self.device.screenshot()
            
            if self.appear(FISH_BAR_ICON):
                self.fish()

            if self.appear(NEED_BAIT):
                if not self.config["tools.fish.buy_bait"]:
                    logger.info('Need bait, stopping because BUY_BAIT is disabled')
                    break
                self.buy_bait()

            if self.appear(FULL_STORAGE):
                if not self.config["tools.fish.sell_fish"]:
                    logger.info('Fish storage full, stopping because SELL_FISH is disabled')
                    break
                self.sell_fish()

    def buy_bait(self):
        logger.hr('BUY BAIT')
        self.device.screenshot()
        self.ui_goto(FISH_SHOP)
        for _ in range(self.config["tools.fish.buy_bait_stack_count"]):
            self.device.click(BAIT)
            self.device.click(SHOP_MAX_BUTTON)
            self.device.click(BUY)
            while True:
                self.device.screenshot()
                self.appear_then_click(BUY_CONFIRM)
                if self.appear(GET_ITEM):
                    self.device.click(SAFE_AREA)
                    break
            time.sleep(1)
            self.wait_until_appear(BAIT)
        self.ui_goto(FISH_MAIN_PAGE)
        self.device.click(BUTTON_CHANGE_BAIT)
        self.wait_until_appear_then_click(CHANGE_BAIT_CONFIRM)

    def sell_fish(self):
        logger.hr('SELL FISH')
        self.device.screenshot()
        self.ui_goto(FISH_STORAGE_PAGE)
        self.device.click(SELL_ALL)
        self.wait_until_appear_then_click(SELL_CONFIRM)
        self.device.screenshot()
        self.wait_until_appear(SELL_SUCCESS, offset=50)
        count = 0
        while True:
            self.device.click(SAFE_AREA)
            self.device.screenshot()
            if self.appear(SELL_SUCCESS, offset=50):
                self.device.sleep((0.1, 0.2))
                count = 0
                continue
            count += 1
            if count >= 3:
                break
        self.ui_goto(FISH_MAIN_PAGE)

    def _find_matching_cols(
            self,
            roi: np.ndarray,
            target_rgb: tuple[int, int, int],
            threshold: int = 60,
    ) -> np.ndarray | None:
        """查找颜色匹配的列坐标。
        Find column indexes matching the target color.
        """
        diff = roi.astype(np.int16) - target_rgb
        color_diff = np.maximum(diff, 0).max(axis=-1) - np.minimum(diff, 0).min(axis=-1)
        mask = color_diff <= threshold
        col_counts = np.sum(mask, axis=0)
        cols = np.where(col_counts > 0)[0]
        if len(cols) > 0:
            return cols
        return None

    def _get_green_bar(self, roi: np.ndarray) -> tuple[int, int] | None:
        """获取绿条安全区间。
        Get the safe interval of the green bar.
        """
        cols = self._find_matching_cols(roi, self.GREEN_BAR_RGB)
        if cols is None:
            return None
        left, right = cols[0], cols[-1]
        width = right - left
        return (int(left + width * self.green_bar_left), int(left + width * self.green_bar_right))
    
    def _get_yellow_cursor(self, roi: np.ndarray) -> int | None:
        """获取黄色光标中心位置。
        Get the center position of the yellow cursor.
        """
        cols = self._find_matching_cols(roi, self.YELLOW_CURSOR_RGB)
        if cols is None:
            return None
        return int((cols[0] + cols[-1]) // 2)

    _right_pushed = False
    _left_pushed = False

    def _release(self) -> None:
        """释放当前钓鱼方向键。
        Release the current fishing direction key.
        """
        need_release = False
        with self._fish_lock:
            if self._right_pushed or self._left_pushed:
                self._right_pushed = False
                self._left_pushed = False
                need_release = True
        if need_release:
            self.device.release()
    
    def _record_input_velocity(self, timestamp: float, velocity: float) -> None:
        """记录输入速度变化，用于延迟和位置预测。
        Record input velocity changes for delay and position prediction.
        """
        with self._fish_lock:
            self._input_history.append((timestamp, velocity))
            while len(self._input_history) > 1 and self._input_history[1][0] < timestamp - 2.0:
                self._input_history.pop(0)

    def _integrate_input_velocity(self, t_start: float, t_end: float) -> float:
        """积分输入速度，估算时间窗内光标位移。
        Integrate input velocity to estimate cursor displacement in a time window.
        """
        with self._fish_lock:
            history = list(self._input_history)
        
        if not history:
            return 0.0
        
        total = 0.0
        for i in range(len(history)):
            t_curr, v_curr = history[i]
            t_next = history[i+1][0] if i + 1 < len(history) else t_end
            
            # 裁剪到目标积分区间，避免历史指令污染当前估算。
            # Clip to the target integration window to avoid stale command pollution.
            start = max(t_curr, t_start)
            end = min(t_next, t_end)
            
            if start < end:
                total += v_curr * (end - start)
                
        return total

    def _apply_control_direction(self, direction: int) -> None:
        """应用控制方向并记录实际发送时刻。
        Apply the control direction and record the actual send timestamp.
        """
        need_release = False
        need_press_right = False
        need_press_left = False
        
        with self._fish_lock:
            if direction == 1:
                if self._left_pushed:
                    self._left_pushed = False
                    need_release = True
                if not self._right_pushed:
                    self._right_pushed = True
                    need_press_right = True
            elif direction == -1:
                if self._right_pushed:
                    self._right_pushed = False
                    need_release = True
                if not self._left_pushed:
                    self._left_pushed = True
                    need_press_left = True
            else:
                if self._right_pushed or self._left_pushed:
                    self._right_pushed = False
                    self._left_pushed = False
                    need_release = True

        if need_release:
            self.device.release()
            t_release = time.time()
            self._record_input_velocity(t_release, 0.0)
            
        if need_press_right:
            self.device.press(BUTTON_RIGHT)
            t_press = time.time()
            self._record_input_velocity(t_press, float(self.yellow_cursor_speed))
            
        if need_press_left:
            self.device.press(BUTTON_LEFT)
            t_press = time.time()
            self._record_input_velocity(t_press, -float(self.yellow_cursor_speed))

    def _send_control_signal(self, signal: FishControlSignal) -> None:
        """发送最新控制信号给异步控制线程。
        Send the latest control signal to the asynchronous control thread.
        """
        with self._control_condition:
            self._pending_control_signal = signal
            self._control_condition.notify()

    def _calculate_control_signal(
            self,
            cursor: int,
            green_bar: tuple[int, int],
            green_vel: float,
            t_shot: float,
            t_now: float,
    ) -> FishControlSignal:
        """根据当前帧计算唯一的按键方向和持续时间。
        Calculate the deterministic key direction and duration from the current frame.
        """
        roi_width = self.FISH_BAR_RECT[2] - self.FISH_BAR_RECT[0]
        dt_shot = max(0.0, t_now - t_shot)
        left, right = green_bar
        width = max(1.0, float(right - left))
        green_center = (left + right) / 2.0

        # 预测输入实际生效时的绿条中心，并限制到钓鱼条边界。
        # Predict the green center when input takes effect and clamp it to the fishing bar.
        pred_green_center = green_center + green_vel * (dt_shot + self.input_delay)
        pred_green_center = max(width / 2.0, min(float(roi_width) - width / 2.0, pred_green_center))
        pred_left = pred_green_center - width / 2.0
        pred_right = pred_green_center + width / 2.0

        # 预测输入生效时的黄标位置：截图时刻到生效时刻的运动来自延迟前已经发出的指令。
        # Predict cursor at input-effect time from commands already sent before the delay boundary.
        displacement = self._integrate_input_velocity(t_shot - self.input_delay, t_now)
        pred_cursor = max(0.0, min(float(roi_width), float(cursor) + displacement))

        # 获取当前实际的按键方向，用于迟滞控制。
        # Get the current active key direction for hysteresis control.
        current_dir = 0
        with self._fish_lock:
            if self._right_pushed:
                current_dir = 1
            elif self._left_pushed:
                current_dir = -1

        if pred_cursor < pred_left:
            direction = 1
        elif pred_cursor > pred_right:
            direction = -1
        # 迟滞控制：若光标已进入安全区，但仍在向中心靠拢，则继续保持当前方向的运动。
        # Hysteresis: if the cursor is within the safe zone, but still moving towards the center, keep the current direction.
        elif current_dir == 1 and pred_cursor < pred_green_center:
            direction = 1
        elif current_dir == -1 and pred_cursor > pred_green_center:
            direction = -1
        else:
            return FishControlSignal(direction=0, duration=0.0, created_at=t_now)

        target = pred_green_center
        if direction == 1:
            closing_speed = float(self.yellow_cursor_speed) - green_vel
            raw_duration = (target - pred_cursor) / closing_speed if closing_speed > 1.0 else 0.2
        else:
            closing_speed = float(self.yellow_cursor_speed) + green_vel
            raw_duration = (pred_cursor - target) / closing_speed if closing_speed > 1.0 else 0.2

        duration = max(0.0, raw_duration)
        return FishControlSignal(direction=direction, duration=duration, created_at=t_now)

    def _control_loop(self) -> None:
        """事件驱动的异步控制线程，只执行主线程计算好的指令。
        Event-driven asynchronous control thread that only executes main-thread signals.
        """
        logger.info("Fish control thread started")
        # 当前异步线程已经按下的方向，0 为释放，1 为右，-1 为左。
        # Current direction held by the async thread: 0 release, 1 right, -1 left.
        current_dir = 0
        deadline: float | None = None
        
        try:
            while True:
                action_dir: int | None = None
                with self._control_condition:
                    while self._fishing_active and self._pending_control_signal is None:
                        if current_dir == 0 or deadline is None:
                            self._control_condition.wait()
                            continue

                        remain = deadline - time.time()
                        if remain <= 0:
                            action_dir = 0
                            current_dir = 0
                            deadline = None
                            break
                        self._control_condition.wait(timeout=remain)

                    if action_dir is None:
                        if not self._fishing_active:
                            break

                        signal = self._pending_control_signal
                        self._pending_control_signal = None
                        now = time.time()
                        if signal is None:
                            continue

                        if signal.direction == 0 or signal.expires_at <= now:
                            deadline = None
                            if current_dir != 0:
                                action_dir = 0
                                current_dir = 0
                        else:
                            # 同向信号直接改写截止时间；反向信号会立即打断当前按键。
                            # Same-direction signals rewrite the deadline; opposite signals interrupt immediately.
                            deadline = signal.expires_at
                            if signal.direction != current_dir:
                                action_dir = signal.direction
                                current_dir = signal.direction

                if action_dir is not None:
                    self._apply_control_direction(action_dir)
        finally:
            self._release()
            logger.info("Fish control thread stopped")

    def fish(self):
        missing_green_bar_count = 0
        x1, y1, x2, y2 = self.FISH_BAR_RECT

        # 初始化状态变量
        last_time = None
        last_green_center = None
        green_vel = 0.0

        # 记录每帧识别到的绿条长度，用于中位数滤波
        # Record the length of the green bar detected in each frame for median filtering.
        detected_bar_lengths = []
        
        self._input_history = [(time.time(), 0.0)]
        self._fishing_active = True
        self._fish_lock = threading.Lock()
        self._control_condition = threading.Condition()
        self._pending_control_signal: FishControlSignal | None = None
        
        self._right_pushed = False
        self._left_pushed = False
        
        # 启动异步控制线程
        control_thread = threading.Thread(target=self._control_loop, daemon=True)
        control_thread.start()

        try:
            with self.device.temporary_screenshot_interval(0):
                while True:
                    t_before = time.time()
                    self.device.screenshot()
                    t_after = time.time()
                    t_shot = (t_before + t_after) / 2.0

                    roi = self.device.image[y1:y2, x1:x2]
                    green_bar = self._get_green_bar(roi)

                    if green_bar is None:
                        missing_green_bar_count += 1
                        # 连续 10 帧检测不到绿条才认为钓鱼结束。
                        # Treat fishing as finished only after 10 consecutive missing green-bar frames.
                        if missing_green_bar_count > 10:
                            break
                        continue

                    missing_green_bar_count = 0
                    left, right = green_bar

                    cursor = self._get_yellow_cursor(roi)
                    if cursor is None:
                        continue

                    # 过滤绿条长度异常的帧，以防由于检测噪点产生误判
                    # Filter out frames with abnormal green bar lengths to prevent misjudgment caused by detection noise.
                    if self.green_bar_length_tolerance > 0:
                        bar_len = right - left
                        if len(detected_bar_lengths) >= 10:
                            median_len = np.median(detected_bar_lengths)
                            if abs(bar_len - median_len) > median_len * self.green_bar_length_tolerance:
                                continue
                        detected_bar_lengths.append(bar_len)

                    # 计算时间差 dt。
                    # Calculate frame delta time.
                    if last_time is not None:
                        dt = max(0.001, t_shot - last_time)
                    else:
                        dt = max(0.001, t_after - t_before)

                    last_time = t_shot

                    # 估算并平滑绿条的速度
                    # Estimate and smooth green bar velocity.
                    green_center = (left + right) / 2.0
                    if last_green_center is not None:
                        raw_green_vel = (green_center - last_green_center) / dt
                        raw_green_vel = max(-300.0, min(300.0, raw_green_vel))

                        is_abrupt = abs(raw_green_vel - green_vel) > self.green_bar_velocity_abrupt_threshold
                        if is_abrupt:
                            green_vel = raw_green_vel
                        else:
                            green_vel = 0.3 * raw_green_vel + 0.7 * green_vel
                    else:
                        green_vel = 0.0
                    last_green_center = green_center

                    t_now = time.time()
                    signal = self._calculate_control_signal(cursor, green_bar, green_vel, t_shot, t_now)
                    self._send_control_signal(signal)
        finally:
            with self._control_condition:
                self._fishing_active = False
                self._control_condition.notify()
            control_thread.join()
            self._release()
