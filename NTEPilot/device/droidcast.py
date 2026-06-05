import re
import time
import typing as t
from functools import wraps

import cv2
import numpy as np
import requests
from adbutils.errors import AdbError

from utils.timer import Timer
from utils.exceptions import EmulatorNotRunningError, RequestHumanTakeover
from utils.logger import logger
from utils.decorators import cached_property, del_cached_property
from .utils import (
    ImageTruncated, PackageNotInstalled, RETRY_TRIES, handle_adb_error, handle_unknown_host_service, retry_sleep, handle_image_truncated)
from .connection import Connection

DROIDCAST_FILEPATH_LOCAL = './bin/DroidCast/DroidCast_raw-release-1.1.apk'
DROIDCAST_FILEPATH_REMOTE = '/data/local/tmp/DroidCast_raw.apk'

class DroidCastVersionIncompatible(Exception):
    pass


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (DroidCast):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    time.sleep(retry_sleep(_))
                    init()
                return func(self, *args, **kwargs)
            # 无法处理
            except RequestHumanTakeover:
                break
            # ADB 服务被终止时
            except ConnectionResetError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
            # ADB 错误
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
                        self.adb_reconnect()
                else:
                    break
            # 应用未安装
            except PackageNotInstalled:
                raise
            # DroidCast 未运行
            # requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
            # ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=20482): Read timed out. (read timeout=3)
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                logger.error(e)

                def init():
                    self.droidcast_init()
            # DroidCast 版本不兼容
            except DroidCastVersionIncompatible as e:
                logger.error(e)

                def init():
                    self.droidcast_init()
            # 图像数据截断
            except ImageTruncated as e:
                handle_image_truncated(self, e)

                def init():
                    pass
            # 无法处理 - 必须向上抛出以触发模拟器重启
            except EmulatorNotRunningError:
                raise
            # 未知异常
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        if func.__name__ in ['screenshot_droidcast', 'screenshot_droidcast_raw']:
            logger.critical(f'重试 {func.__name__}() 失败')
            raise EmulatorNotRunningError
        logger.critical(f'重试 {func.__name__}() 失败')
        raise RequestHumanTakeover

    return retry_wrapper


class DroidCast(Connection):
    """
    DroidCast 截图方案，https://github.com/rayworks/DroidCast
    DroidCast_raw，DroidCast 的修改版本，发送原始位图和 PNG，https://github.com/Torther/DroidCastS
    """

    _droidcast_port: int = 0
    droidcast_width: int = 0
    droidcast_height: int = 0

    @cached_property
    def droidcast_session(self):
        session = requests.Session()
        session.trust_env = False  # 忽略代理
        self._droidcast_port = self.adb_forward('tcp:53516')
        return session

    """
    可用 API 参考源码：
    https://github.com/Torther/DroidCast_raw/blob/DroidCast_raw/app/src/main/java/ink/mol/droidcast_raw/KtMain.kt
    可用接口：
    - /screenshot
        获取 RGB565 位图
    - /preview
        获取 PNG 截图
    """

    def droidcast_url(self, url='/screenshot'):
        if self.is_mumu_over_version_356:
            w, h = self.droidcast_width, self.droidcast_height
            if self.orientation == 0:
                return f'http://127.0.0.1:{self._droidcast_port}{url}?width={w}&height={h}'
            elif self.orientation == 1:
                return f'http://127.0.0.1:{self._droidcast_port}{url}?width={h}&height={w}'
            else:
                # logger.warning('DroidCast receives invalid device orientation')
                pass

        return f'http://127.0.0.1:{self._droidcast_port}{url}'

    def droidcast_init(self):
        logger.hr('DroidCast init')
        self.droidcast_stop()
        self._droidcast_update_resolution()

        logger.info('Pushing DroidCast apk')
        self.adb_push(DROIDCAST_FILEPATH_LOCAL, DROIDCAST_FILEPATH_REMOTE)

        logger.info('Starting DroidCast apk')
        # DroidCast_raw-release-1.1.apk
        # CLASSPATH=/data/local/tmp/DroidCast_raw.apk app_process / ink.mol.droidcast_raw.Main > /dev/null
        # adb shell CLASSPATH=/data/local/tmp/DroidCast_raw.apk app_process / ink.mol.droidcast_raw.Main
        self.adb_shell([
            'sh', '-c',
            f"setsid sh -c 'CLASSPATH={DROIDCAST_FILEPATH_REMOTE} app_process / ink.mol.droidcast_raw.Main > /dev/null 2>&1 &' || CLASSPATH={DROIDCAST_FILEPATH_REMOTE} app_process / ink.mol.droidcast_raw.Main > /dev/null 2>&1 &"
        ])
        del_cached_property(self, 'droidcast_session')
        _ = self.droidcast_session

        logger.attr('DroidCast_raw', self.droidcast_url())
        self.droidcast_wait_startup()

    def _droidcast_update_resolution(self):
        if self.is_mumu_over_version_356:
            logger.info('Update droidcast resolution')
            try:
                res = self.adb_shell(['wm', 'size'])
                sizes = re.findall(r'(\d+)x(\d+)', res)
                if sizes:
                    w, h = int(sizes[-1][0]), int(sizes[-1][1])
                else:
                    w, h = 720, 1280
            except Exception as e:
                logger.error(f"Failed to get resolution via adb: {e}")
                w, h = 720, 1280
            self.get_orientation()
            # 720, 1280
            # mumu12 > 3.5.6 始终为竖屏设备
            self.droidcast_width, self.droidcast_height = w, h
            logger.info(f'Droicast resolution: {(w, h)}')

    @retry
    def screenshot_droidcast(self):
        shape = (720, 1280)
        if self.is_mumu_over_version_356:
            if not self.droidcast_width or not self.droidcast_height:
                self._droidcast_update_resolution()
            if self.droidcast_height and self.droidcast_width:
                shape = (self.droidcast_height, self.droidcast_width)

        rotate = self.is_mumu_over_version_356 and self.orientation == 1

        resp = self.droidcast_session.get(self.droidcast_url(), timeout=3)
        image = resp.content
        # DroidCast_raw 返回 RGB565 位图

        # 防止空内容导致 np.frombuffer 抛出 TypeError
        if image is None or len(image) == 0:
            raise ImageTruncated('Empty image content from DroidCast_raw')

        # DroidCast 返回了短错误信息而非原始位图数据
        # 例如 b':(  Failed to generate the screenshot on device / emulator: ...'
        # 抛出 ConnectionError 以在重试处理器中立即触发 droidcast_init
        if len(image) < 500:
            logger.warning(f'Unexpected screenshot: {image}')
            raise requests.exceptions.ConnectionError(f'DroidCast service error: {image!r}')

        try:
            arr = np.frombuffer(image, dtype=np.uint16)
            if rotate:
                arr = arr.reshape(shape)
                # arr = cv2.rotate(arr, cv2.ROTATE_90_CLOCKWISE)
                # 稍微快一点？
                arr = cv2.transpose(arr)
                cv2.flip(arr, 1, dst=arr)
            else:
                arr = arr.reshape(shape)
        except ValueError as e:
            # ValueError: cannot reshape array of size 0 into shape (720,1280)
            raise ImageTruncated(str(e)+'\nIf your emulator resolution not 1280x720, please set emulator resolution to 1280x720')

        # 将 RGB565 转换为 RGB888
        # https://blog.csdn.net/happy08god/article/details/10516871

        # r = (arr & 0b1111100000000000) >> (11 - 3)
        # g = (arr & 0b0000011111100000) >> (5 - 2)
        # b = (arr & 0b0000000000011111) << 3
        # r |= (r & 0b11100000) >> 5
        # g |= (g & 0b11000000) >> 6
        # b |= (b & 0b11100000) >> 5
        # r = r.astype(np.uint8)
        # g = g.astype(np.uint8)
        # b = b.astype(np.uint8)
        # image = cv2.merge([r, g, b])

        # 与上方代码功能相同，但耗时约 2.7ms 而非 16ms。
        # 注意 cv2.convertScaleAbs 比 cv2.multiply 快 5 倍，cv2.add 比 cv2.convertScaleAbs 快 8 倍
        # 注意 cv2.convertScaleAbs 包含四舍五入
        tmp = np.empty_like(arr)
        cv2.bitwise_and(arr, 0b1111100000000000, dst=tmp)
        r = cv2.convertScaleAbs(tmp, alpha=0.0040283203125)  # 0.00390625 * 1.03125
        cv2.bitwise_and(arr, 0b0000011111100000, dst=tmp)
        g = cv2.convertScaleAbs(tmp, alpha=0.126953125)  # 0.125 * 1.015625
        cv2.bitwise_and(arr, 0b0000000000011111, dst=tmp)
        b = cv2.convertScaleAbs(tmp, alpha=8.25)  # 8 * 1.03125

        image = cv2.merge([r, g, b])

        return image

    def droidcast_wait_startup(self):
        """等待 DroidCast 启动完成。"""
        timeout = Timer(10)
        while 1:
            time.sleep(0.25)
            if timeout.reached:
                break

            try:
                resp = self.droidcast_session.get(self.droidcast_url('/'), timeout=3)
                # 路由 `/` 不可用，但 404 表示启动已完成
                if resp.status_code == 404:
                    logger.attr('DroidCast', 'online')
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                logger.attr('DroidCast', 'offline')

        logger.warning('Wait DroidCast startup timeout, assume started')
        return False

    def droidcast_uninstall(self):
        """
        停止 DroidCast 进程并删除 DroidCast APK。
        DroidCast 并非真正安装，而是通过 JAVA 类调用，卸载即删除文件。
        """
        self.droidcast_stop()
        logger.info('Removing DroidCast')
        self.adb_shell(["rm", DROIDCAST_FILEPATH_REMOTE])

    def _iter_droidcast_proc(self) -> t.Iterable[int]:
        """列出所有 DroidCast 进程。"""
        cmd = 'for p in /proc/[0-9]*; do [ -f "$p/cmdline" ] && echo "${p##*/}:$(cat "$p/cmdline")"; done'
        try:
            output = self.adb_shell(['sh', '-c', cmd])
        except Exception as e:
            logger.error(f"Failed to list processes via adb shell: {e}")
            output = ""

        if not output:
            return

        for line in output.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
            parts = line.split(':', 1)
            pid_str, cmdline = parts[0], parts[1]
            if not pid_str.isdigit():
                continue
            pid = int(pid_str)
            cmdline = cmdline.replace('\x00', ' ').strip()

            if 'com.rayworks.droidcast.Main' in cmdline:
                yield pid
            elif 'com.torther.droidcasts.Main' in cmdline:
                yield pid
            elif 'ink.mol.droidcast_raw.Main' in cmdline:
                yield pid

    def droidcast_stop(self):
        """停止 DroidCast 进程。"""
        logger.info('Stopping DroidCast')
        for pid in self._iter_droidcast_proc():
            logger.info(f'Kill pid={pid}')
            self.adb_shell(['kill', '-s', '9', str(pid)])