# 此文件定义了 Device 类，是脚本与设备交互的综合管理入口。
# 负责整合截图、点击、输入功能，并由于内置了防卡死检测和点击频率控制，能有效提高脚本自动化运行的稳定性。
import collections

import cv2

from utils.timer import Timer
from .control import Control
from .screenshot import Screenshot
from utils.exceptions import (EmulatorNotRunningError, GameNotRunningError, GameStuckError, GameTooManyClickError,
                              RequestHumanTakeover)
from utils.logger import logger

def show_function_call():
    """
    INFO     21:07:31.554 │ Function calls:
                       <string>   L1 <module>
                   spawn.py L116 spawn_main()
                   spawn.py L129 _main()
                 process.py L314 _bootstrap()
                 process.py L108 run()
         process_manager.py L149 run_process()
                    alas.py L285 loop()
                    alas.py  L69 run()
                     src.py  L55 rogue()
                   rogue.py  L36 run()
                   rogue.py  L18 rogue_once()
                   entry.py L335 rogue_world_enter()
                    path.py L193 rogue_path_select()
    """
    import os
    import traceback
    stack = traceback.extract_stack()
    func_list = []
    for row in stack:
        filename, line_number, function_name, _ = row
        filename = os.path.basename(filename)
        # 示例: /tasks/character/switch.py:64 character_update()
        func_list.append([filename, str(line_number), function_name])
    max_filename = max([len(row[0]) for row in func_list])
    max_linenum = max([len(row[1]) for row in func_list]) + 1

    def format_(file, line, func):
        file = file.rjust(max_filename, " ")
        line = f'L{line}'.rjust(max_linenum, " ")
        if not func.startswith('<'):
            func = f'{func}()'
        return f'{file} {line} {func}'

    func_list = [f'\n{format_(*row)}' for row in func_list]
    logger.info('Function calls:' + ''.join(func_list))


class Device(Screenshot, Control):
    """
    设备交互管理类，整合截图、控制、应用管理和输入功能。

    通过多重继承组合 Screenshot、Control、AppControl、Input 四个模块，
    并通过 Platform 委托模拟器管理操作。
    """
    _screen_size_checked = False
    detect_record = set()
    click_record = collections.deque(maxlen=15)
    stuck_timer = Timer(60)
    stuck_timer_long = Timer(195)
    _prev_fingerprint = None
    _stuck_image_timer = Timer(30)

    def __init__(self, *args, **kwargs):
        # 初始化模拟器管理平台
        # self._platform = None

        for trial in range(4):
            try:
                super().__init__(*args, **kwargs)
                break
            except EmulatorNotRunningError:
                if trial >= 3:
                    logger.critical('错误 3 次尝试后未能启动模拟器')
                    raise RequestHumanTakeover
                # # 尝试启动模拟器
                # if self.emulator_instance is not None:
                #     self.emulator_start()
                # else:
                #     logger.critical(
                #         f'错误 未找到序列号为 "{self.config.Emulator_Serial}" 的模拟器，'
                #         f'请设置一个正确的序列号'
                #     )
                #     raise RequestHumanTakeover

        # 确保 package 属性存在（部分连接模式可能不会设置它）
        # AppControl.app_is_running() 会用到此属性
        if not hasattr(self, 'package'):
            # 回退到配置值；如果是 'auto'，后续检测会更新它
            self.package = self.config.package_name

        # # 自动填充模拟器信息
        # if IS_WINDOWS and self.config.EmulatorInfo_Emulator == 'auto':
        #     _ = self.emulator_instance

        # # Mac 上提升运行中模拟器的优先级
        # if IS_MACINTOSH:
        #     try:
        #         self.platform.boost_running_emulator_priority()
        #     except Exception as e:
        #         logger.warning(f'Failed to boost emulator priority: {e}')

        self.screenshot_interval_set()
    # 暂时取消模拟器控制功能

    # @property
    # def platform(self):
    #     """
    #     获取模拟器管理平台实例。

    #     惰性初始化，首次访问时创建 Platform 实例。
    #     """
    #     if self._platform is None:
    #         # 当模拟器离线时（通常是需要自动启动的场景），
    #         # 必须避免在此触发完整的 ADB 连接，否则 Platform 会再次抛出
    #         # EmulatorNotRunningError，而此时 Device.__init__ 正在处理该异常。
    #         #
    #         # 因此使用 connect=False 构造 Platform，仅执行轻量初始化
    #         # （config/adb_client/serial），足以发现 emulator_instance 和
    #         # 调用 emulator_start()；真正的 ADB 连接在 Device 初始化完成后
    #         # 由 Connection 完成。
    #         self._platform = Platform(self.config, connect=False)
    #     return self._platform

    # @property
    # def emulator_instance(self):
    #     """
    #     获取当前模拟器实例。

    #     Returns:
    #         模拟器实例对象，未找到时返回 None。
    #     """
    #     return self.platform.emulator_instance

    # def emulator_start(self):
    #     """
    #     启动模拟器，委托给平台特定实现。
    #     """
    #     return self.platform.emulator_start()

    # def emulator_stop(self):
    #     """
    #     停止模拟器，委托给平台特定实现。
    #     """
    #     return self.platform.emulator_stop()

    def screenshot(self):
        """
        截取屏幕截图，包含卡死检测和夜间委托处理。

        Returns:
            截图图像，numpy 数组格式。
        """
        super().screenshot()
        self._check_image_stuck()
        return self.image

    def _check_image_stuck(self):
        if self.image is None:
            return

        small = cv2.resize(self.image, (16, 16))
        fp = hash(small.tobytes())

        if self._prev_fingerprint is not None and fp == self._prev_fingerprint:
            if self._stuck_image_timer.reached:
                show_function_call()
                logger.warning(f'Screenshot unchanged for over {self._stuck_image_timer.duration}s')
                if self.app_is_running():
                    raise GameStuckError('Screenshot not changing')
                else:
                    raise GameNotRunningError('Game died')
        else:
            self._prev_fingerprint = fp
            self._stuck_image_timer.reset()
