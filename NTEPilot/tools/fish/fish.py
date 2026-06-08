import time
import threading
import numpy as np

from NTEPilot.ui.ui import UI
from NTEPilot.device.control import Control
from NTEPilot.ui.page import FISH_MAIN_PAGE, FISH_SHOP, FISH_STORAGE_PAGE
from template.fish import *
from template.ui import GET_ITEM

from utils.logger import logger

SAFE_AREA = (600, 700)

class Fish(UI):
    FISH_BAR_RECT = (404, 44, 880, 55)

    GREEN_BAR_RGB = (58, 240, 177)
    YELLOW_CURSOR_RGB = (255, 253, 160)
    @property
    def green_bar_left(self):
        return 0.5 - self.config["tools.fish.green_bar_safe_proportion"] / 2

    @property
    def green_bar_right(self):
        return 0.5 + self.config["tools.fish.green_bar_safe_proportion"] / 2

    def run(self):
        logger.hr('FISH', level=1)
        self.wait_until_appear(HOOK)

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

    def _find_matching_cols(self, roi, target_rgb, threshold=30):
        diff = roi.astype(np.int16) - target_rgb
        color_diff = np.maximum(diff, 0).max(axis=-1) - np.minimum(diff, 0).min(axis=-1)
        mask = color_diff <= threshold
        col_counts = np.sum(mask, axis=0)
        cols = np.where(col_counts > 0)[0]
        if len(cols) > 0:
            return cols
        return None

    def _get_green_bar(self, roi):
        cols = self._find_matching_cols(roi, self.GREEN_BAR_RGB)
        if cols is None:
            return None
        left, right = cols[0], cols[-1]
        width = right - left
        return (int(left + width * self.green_bar_left), int(left + width * self.green_bar_right))
    
    def _get_yellow_cursor(self, roi):
        cols = self._find_matching_cols(roi, self.YELLOW_CURSOR_RGB)
        if cols is None:
            return None
        return int((cols[0] + cols[-1]) // 2)

    _right_pushed = False
    _left_pushed = False

    def _release(self):
        if self._right_pushed or self._left_pushed:
            self.device.release()
            self._right_pushed = False
            self._left_pushed = False
    
    def _press_right(self):
        if self._left_pushed:
            self._release()
        if not self._right_pushed:
            self.device.press(BUTTON_RIGHT)
            self._right_pushed = True

    def _press_left(self):
        if self._right_pushed:
            self._release()
        if not self._left_pushed:
            self.device.press(BUTTON_LEFT)
            self._left_pushed = True

    def _integrate_input_velocity(self, t_start, t_end):
        with self._fish_lock:
            history = list(self._input_history)
        
        if not history:
            return 0.0
        
        total = 0.0
        for i in range(len(history)):
            t_curr, v_curr = history[i]
            t_next = history[i+1][0] if i + 1 < len(history) else t_end
            
            # Clip interval [t_curr, t_next] to [t_start, t_end]
            start = max(t_curr, t_start)
            end = min(t_next, t_end)
            
            if start < end:
                total += v_curr * (end - start)
                
        return total

    def _control_loop(self):
        """
        Asynchronous control loop running in a daemon thread.
        Calculates predicted positions 0.25s into the future and sends commands.
        """
        logger.info("Fish control thread started")
        current_dir = 0  # 0: release, 1: right, -1: left
        last_action_time = 0.0
        
        while True:
            with self._fish_lock:
                if not self._fishing_active:
                    break
                latest_cursor = self._latest_cursor
                latest_green_bar = self._latest_green_bar
                latest_green_vel = self._latest_green_vel
                latest_t_shot = self._latest_t_shot
            
            if latest_cursor is None or latest_green_bar is None or latest_t_shot is None:
                time.sleep(0.01)
                continue
            
            t_now = time.time()
            dt_shot = t_now - latest_t_shot
            
            # 1. 预测未来时刻绿条的安全区间
            green_center = (latest_green_bar[0] + latest_green_bar[1]) / 2.0
            pred_green_center = green_center + latest_green_vel * (dt_shot + 0.25)
            w = latest_green_bar[1] - latest_green_bar[0]
            
            # 考虑边界限制：绿条到达最左端或最右端时不能继续移动
            roi_width = self.FISH_BAR_RECT[2] - self.FISH_BAR_RECT[0]
            pred_green_center = max(w / 2.0, min(roi_width - w / 2.0, pred_green_center))
            
            pred_left = pred_green_center - w * (self.config["tools.fish.green_bar_safe_proportion"] / 2.0)
            pred_right = pred_green_center + w * (self.config["tools.fish.green_bar_safe_proportion"] / 2.0)
            
            # 2. 预测未来时刻光标的位置 (结合 0.25s 前开始直到当前的输入指令积分)
            displacement = self._integrate_input_velocity(latest_t_shot - 0.25, t_now)
            pred_cursor = latest_cursor + displacement
            # 考虑光标边界限制
            pred_cursor = max(0.0, min(roi_width, pred_cursor))
            
            # 3. 决定目标动作 (限流最小间隔 0.15s)
            if t_now - last_action_time >= 0.15:
                if pred_cursor < pred_left:
                    target_dir = 1  # 右
                elif pred_cursor > pred_right:
                    target_dir = -1  # 左
                else:
                    target_dir = 0  # 释放
                
                if target_dir != current_dir:
                    current_dir = target_dir
                    last_action_time = t_now
                    vel = 0.0
                    if current_dir == 1:
                        vel = 200.0
                    elif current_dir == -1:
                        vel = -200.0
                    
                    with self._fish_lock:
                        self._input_history.append((t_now, vel))
                        while len(self._input_history) > 1 and self._input_history[1][0] < t_now - 2.0:
                            self._input_history.pop(0)
                    
                    if current_dir == 1:
                        self._press_right()
                    elif current_dir == -1:
                        self._press_left()
                    else:
                        self._release()
            
            time.sleep(0.01)
            
        self._release()
        logger.info("Fish control thread stopped")

    def fish(self):
        missing_green_bar_count = 0
        x1, y1, x2, y2 = self.FISH_BAR_RECT

        # 初始化状态变量
        last_time = None
        last_green_center = None
        green_vel = 0.0

        self._latest_t_shot = None
        self._latest_cursor = None
        self._latest_green_bar = None
        self._latest_green_vel = 0.0
        
        self._input_history = [(time.time(), 0.0)]
        self._fishing_active = True
        self._fish_lock = threading.Lock()
        
        self._right_pushed = False
        self._left_pushed = False
        
        # 启动异步控制线程
        control_thread = threading.Thread(target=self._control_loop, daemon=True)
        control_thread.start()

        try:
            while True:
                t_before = time.time()
                self.device.screenshot()
                t_shot = (t_before + time.time()) / 2.0
                
                roi = self.device.image[y1:y2, x1:x2]
                green_bar = self._get_green_bar(roi)
                
                if green_bar is None:
                    missing_green_bar_count += 1
                    if missing_green_bar_count > 10: # 连续 10 帧检测不到绿条才认为结束
                        break
                    continue
                
                missing_green_bar_count = 0
                left, right = green_bar
                cursor = self._get_yellow_cursor(roi)

                if cursor is None:
                    continue

                # 计算时间差 dt
                if last_time is not None:
                    dt = max(0.05, t_shot - last_time)
                else:
                    dt = 0.1
                last_time = t_shot

                # 估算并平滑绿条的速度
                green_center = (left + right) / 2.0
                if last_green_center is not None:
                    raw_green_vel = (green_center - last_green_center) / dt
                    raw_green_vel = max(-180.0, min(180.0, raw_green_vel))
                    green_vel = 0.3 * raw_green_vel + 0.7 * green_vel
                else:
                    green_vel = 0.0
                last_green_center = green_center

                # 更新共享状态变量，供控制线程读取
                with self._fish_lock:
                    self._latest_t_shot = t_shot
                    self._latest_cursor = cursor
                    self._latest_green_bar = green_bar
                    self._latest_green_vel = green_vel
        finally:
            with self._fish_lock:
                self._fishing_active = False
            control_thread.join()
            self._release()

if __name__ == "__main__":
    fish = Fish(None)
    fish.run()
