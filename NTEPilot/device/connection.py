from adbutils import AdbClient
import re
import time
import json
import sys
from functools import cached_property, wraps
from concurrent.futures import ThreadPoolExecutor

from adbutils import adb, AdbDevice, ForwardItem, ReverseItem
from adbutils.errors import AdbError, AdbTimeout

from utils.logger import logger
from utils.timer import Timer
from utils.decorators import del_cached_property, run_once
from utils.exceptions import EmulatorNotRunningError, RequestHumanTakeover
from .utils import (
    RETRY_TRIES,
    retry_sleep,
    possible_reasons,
    handle_adb_error,
    handle_unknown_host_service,
    PackageNotInstalled,
    recv_all,
    random_port
)

IS_WINDOWS = sys.platform == 'win32'
IS_MACINTOSH = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

FORWARD_PORT_RANGE = (20000, 21000)

def retry(func):
    """带自动重试的装饰器，处理 ADB 连接和设备相关异常。

    对指定函数进行最多 RETRY_TRIES 次重试，根据不同的异常类型
    采取不同的恢复策略（重连 ADB、重启服务、检测包等）。
    """
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Adb): ADB 设备实例。
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    time.sleep(retry_sleep(_))
                    init()
                return func(self, *args, **kwargs)
            # 无法处理的异常，直接中断重试
            except RequestHumanTakeover:
                break
            # 无法处理，必须向上传播以触发模拟器重启
            except EmulatorNotRunningError:
                raise
            # ADB 服务被杀死时触发
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
            # 包未安装
            except PackageNotInstalled:
                raise
            # 未知异常，可能是损坏的图像数据
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        if func.__name__ in [
            'adb_connect', 'adb_reconnect', 'adb_start_server',
            'screenshot', 'screenshot_adb', 'screenshot_ascreencap',
            'screenshot_droidcast', 'screenshot_droidcast_raw',
            'screenshot_nemu_ipc', 'screenshot_ldopengl',
        ]:
            logger.critical(f'重试 {func.__name__}() 失败')
            raise EmulatorNotRunningError
        logger.critical(f'重试 {func.__name__}() 失败')
        raise RequestHumanTakeover

    return retry_wrapper

class AdbDeviceWithStatus:
    def __init__(self, serial, status):
        self.serial = serial
        self.status = status

class Connection:
    CLIENT = {
        '异环': ('com.hottagames.yh.laohu', 'com.epicgames.ue.LaunchActivity'),
        '云·异环': ('com.pwrd.cloud.yh.laohu', 'com.pwrd.cloudgame.client_core.LaunchActivity')
    }
    def __init__(self, config):
        self.config = config
        self.serial = self.config["general.serial"]
        # 连接设备
        self.adb_connect(wait_device=False)
        logger.attr('AdbDevice', self.adb)

        # 检测包名和Activity
        self.package = self.CLIENT[self.config["general.client"]][0]
        self.activity = self.CLIENT[self.config["general.client"]][1]
        logger.attr('PackageName', self.package)
        logger.attr('ActivityName', self.activity)

        self.check_mumu_app_keep_alive()

    @cached_property
    def adb_client(self) -> AdbClient:
        return adb

    @cached_property
    def adb(self):
        return self.adb_client.device(self.serial)

    @cached_property
    def port(self) -> int:
        if ':' in self.serial:
            try:
                return int(self.serial.split(':')[-1])
            except ValueError:
                pass
        return 0

    @cached_property
    def is_emulator(self):
        return '127.0.0.1:' in self.serial or 'localhost:' in self.serial or self.serial.startswith('emulator-')

    @cached_property
    def is_mumu12_family(self):
        return 16384 <= self.port <= 16484

    @cached_property
    def is_mumu_family(self):
        if '127.0.0.1:7555' in self.serial or self.is_mumu12_family:
            return True
        if self.nemud_player_version != '':
            return True
        return False

    @cached_property
    def is_network_device(self):
        if ':' in self.serial:
            host = self.serial.split(':')[0]
            if host not in ('127.0.0.1', 'localhost'):
                return True
        return False

    @cached_property
    def is_bluestacks_hyperv(self):
        return False

    def adb_start_server(self):
        """启动 ADB 服务。"""
        logger.info('Start adb server')
        self.adb_client.server_version()

    def adb_shell(self, cmd, stream=False, recvall=True, timeout=10, rstrip=True):
        """执行 ADB shell 命令，等价于 `adb -s <serial> shell <*cmd>`。

        Args:
            cmd (list, str): shell 命令或命令参数列表。
            stream (bool): 为 True 时返回流对象而非字符串。默认 False。
            recvall (bool): stream=True 时是否接收全部数据。默认 True。
            timeout (int): 超时时间（秒）。默认 10。
            rstrip (bool): 是否去除末尾空行。默认 True。

        Returns:
            stream=False 时返回 str。
            stream=True 且 recvall=True 时返回 bytes。
            stream=True 且 recvall=False 时返回 socket。
        """
        if not isinstance(cmd, str):
            cmd = list(map(str, cmd))

        if stream:
            result = self.adb.shell(cmd, stream=stream, timeout=timeout, rstrip=rstrip)
            if recvall:
                try:
                    # 返回 bytes
                    return recv_all(result)
                finally:
                    try:
                        if hasattr(result, 'close'):
                            result.close()
                        elif hasattr(result, 'conn') and hasattr(result.conn, 'close'):
                            result.conn.close()
                    except Exception:
                        pass
            else:
                # 返回 socket
                return result
        else:
            result = self.adb.shell(cmd, stream=stream, timeout=timeout, rstrip=rstrip)
            return result

    def adb_getprop(self, name):
        """获取 Android 系统属性，等价于 `getprop <name>`。

        Args:
            name (str): 属性名称。

        Returns:
            str: 属性值。
        """
        return self.adb_shell(['getprop', name]).strip()

    def adb_find_pids(self, *keywords) -> list[int]:
        """寻找包含指定关键字的进程 PID 列表。"""
        cmd = 'for p in /proc/[0-9]*; do [ -f "$p/cmdline" ] && echo "${p##*/}:$(cat "$p/cmdline")"; done'
        try:
            output = self.adb_shell(['sh', '-c', cmd])
        except Exception as e:
            logger.error(f"Failed to list processes via adb shell: {e}")
            return []

        if not output:
            return []

        pids = []
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

            if any(keyword in cmdline for keyword in keywords):
                pids.append(pid)
        return pids

    def adb_kill_processes(self, pids: list[int]):
        """终止设备上的指定 PID 进程。"""
        if not pids:
            return
        kill_cmd = f"kill -s 9 {' '.join(map(str, pids))}"
        try:
            self.adb_shell(kill_cmd)
        except Exception as e:
            logger.error(f"Failed to kill processes: {e}")

    def close_stream(self, stream):
        """安全关闭 ADB 套接字或套接字流。"""
        if stream is None:
            return
        try:
            if hasattr(stream, 'close'):
                stream.close()
            elif hasattr(stream, 'conn') and hasattr(stream.conn, 'close'):
                stream.conn.close()
        except Exception as e:
            logger.error(f'Failed to close stream: {e}')

    @cached_property
    @retry
    def cpu_abi(self) -> str:
        """获取设备的 CPU ABI 类型。

        Returns:
            str: CPU ABI，如 arm64-v8a、armeabi-v7a、x86、x86_64。
        """
        abi = self.adb_getprop('ro.product.cpu.abi')
        if not len(abi):
            logger.error(f'CPU ABI invalid: "{abi}"')
        return abi

    @cached_property
    @retry
    def sdk_ver(self) -> int:
        """获取 Android SDK/API 版本号，详见 https://apilevels.com/。"""
        sdk = self.adb_getprop('ro.build.version.sdk')
        try:
            return int(sdk)
        except ValueError:
            logger.error(f'SDK version invalid: {sdk}')

        return 0

    @cached_property
    @retry
    def is_avd(self):
        if 'ranchu' in self.adb_getprop('ro.hardware'):
            return True
        if 'goldfish' in self.adb_getprop('ro.hardware.audio.primary'):
            return True
        return False

    @cached_property
    @retry
    def is_waydroid(self):
        res = self.adb_getprop('ro.product.brand')
        logger.attr('ro.product.brand', res)
        return 'waydroid' in res.lower()

    @cached_property
    @retry
    def is_bluestacks_air(self):
        if not IS_MACINTOSH:
            return False
        if not (5555 <= self.port <= 5875):
            return False
        res = self.adb_getprop('bst.installed_images')
        logger.attr('bst.installed_images', res)
        if 'Tiramisu64' in res:
            return True
        return False

    @cached_property
    @retry
    def is_mumu_pro(self):
        if not IS_MACINTOSH:
            return False
        if not self.is_mumu_family:
            return False
        logger.attr('is_mumu_pro', True)
        return True

    @cached_property
    @retry
    def nemud_app_keep_alive(self) -> str:
        res = self.adb_getprop('nemud.app_keep_alive')
        logger.attr('nemud.app_keep_alive', res)
        return res

    @cached_property
    @retry
    def nemud_player_version(self) -> str:
        res = self.adb_getprop('nemud.player_version')
        logger.attr('nemud.player_version', res)
        return res

    @cached_property
    @retry
    def nemud_player_engine(self) -> str:
        res = self.adb_getprop('nemud.player_engine')
        logger.attr('nemud.player_engine', res)
        return res

    def check_mumu_app_keep_alive(self):
        if not self.is_mumu_family:
            return False

        res = self.nemud_app_keep_alive
        if res == '':
            return True
        elif res == 'false':
            return True
        elif res == 'true':
            logger.critical('请在MuMu模拟器设置内关闭 "后台挂机时保活运行"')
            raise RequestHumanTakeover
        else:
            logger.warning(f'Invalid nemud.app_keep_alive value: {res}')
            return False

    @cached_property
    def is_mumu_over_version_400(self) -> bool:
        if not self.is_mumu_family:
            return False
        if self.nemud_player_version == '':
            return True
        return False

    @cached_property
    def is_mumu_over_version_356(self) -> bool:
        if not self.is_mumu_family:
            return False
        if self.is_mumu_over_version_400:
            return True
        if self.nemud_app_keep_alive != '':
            return True
        if IS_MACINTOSH:
            if 'MACPRO' in self.nemud_player_engine:
                return True
        return False

    def adb_forward(self, remote):
        port = 0
        for forward in self.adb.forward_list():
            if forward.serial == self.serial and forward.remote == remote and forward.local.startswith('tcp:'):
                if not port:
                    logger.info(f'Reuse forward: {forward}')
                    port = int(forward.local[4:])
                else:
                    logger.info(f'Remove redundant forward: {forward}')
                    self.adb_forward_remove(forward.local)

        if port:
            return port
        else:
            port = random_port(FORWARD_PORT_RANGE)
            forward = ForwardItem(self.serial, f'tcp:{port}', remote)
            logger.info(f'Create forward: {forward}')
            self.adb.forward(forward.local, forward.remote)
            return port

    def _adb_reverse_transport(self, remote: str, local: str, norebind: bool = False):
        args = ["reverse:forward"]
        if norebind:
            args.append("norebind")
        args.append(remote + ";" + local)
        cmd = ":".join(args)
        with self.adb_client.make_connection() as c:
            c.send_command(f'host:transport:{self.serial}')
            c.check_okay()
            c.send_command(cmd)
            c.check_okay()

    def adb_reverse(self, remote):
        port = 0
        for reverse in self.adb.reverse_list():
            if reverse.remote == remote and reverse.local.startswith('tcp:'):
                if not port:
                    logger.info(f'Reuse reverse: {reverse}')
                    port = int(reverse.local[4:])
                else:
                    logger.info(f'Remove redundant reverse: {reverse}')
                    self.adb_reverse_remove(reverse.remote)

        if port:
            return port
        else:
            port = random_port(FORWARD_PORT_RANGE)
            reverse = ReverseItem(remote, f'tcp:{port}')
            logger.info(f'Create reverse: {reverse}')
            self._adb_reverse_transport(reverse.remote, reverse.local)
            return port

    def adb_forward_remove(self, local):
        try:
            with self.adb_client.make_connection() as c:
                list_cmd = f"host-serial:{self.serial}:killforward:{local}"
                c.send_command(list_cmd)
                c.check_okay()
        except AdbError as e:
            msg = str(e)
            if re.search(r'listener .*? not found', msg):
                logger.warning(f'{type(e).__name__}: {msg}')
            else:
                raise

    def adb_reverse_remove(self, local):
        try:
            with self.adb_client.make_connection() as c:
                c.send_command(f"host:transport:{self.serial}")
                c.check_okay()
                list_cmd = f"reverse:killforward:{local}"
                c.send_command(list_cmd)
                c.check_okay()
        except AdbError as e:
            msg = str(e)
            if re.search(r'listener .*? not found', msg):
                logger.warning(f'{type(e).__name__}: {msg}')
            else:
                raise

    def adb_push(self, local, remote):
        """推送文件到设备，等价于 `adb push <local> <remote>`。"""
        logger.info(f'Pushing {local} to {remote}')
        return self.adb.push(local, remote)

    @retry
    def list_device(self):
        """列出所有 ADB 设备。"""
        return [AdbDeviceWithStatus(d.serial, d.state) for d in self.adb_client.list()]

    def _wait_device_appear(self, serial, first_devices=None):
        timeout = Timer(5.2)
        first_log = True
        while 1:
            if first_devices is not None:
                devices = first_devices
                first_devices = None
            else:
                devices = self.list_device()
            for device in devices:
                if device.serial == serial and device.status == 'device':
                    return True
            if timeout.reached:
                break
            if first_log:
                logger.info(f'Waiting device appear: {serial}')
                first_log = False
            time.sleep(0.05)

        return False

    def adb_connect(self, wait_device=True):
        devices = self.list_device()
        for device in devices:
            if device.status == 'offline':
                logger.warning(f'Device {device.serial} is offline, disconnect it before connecting')
                msg = self.adb_client.disconnect(device.serial)
                if msg:
                    logger.info(msg)
            elif device.status == 'unauthorized':
                logger.error(f'Device {device.serial} is unauthorized, please accept ADB debugging on your device')
            elif device.status == 'device':
                pass
            else:
                logger.warning(f'Device {device.serial} is is having a unknown status: {device.status}')

        if 'emulator-' in self.serial:
            if wait_device:
                if self._wait_device_appear(self.serial, first_devices=devices):
                    logger.info(f'Serial {self.serial} connected')
                    return True
                else:
                    logger.info(f'Serial {self.serial} is not connected')
                    return False
            logger.info(f'"{self.serial}" is a `emulator-*` serial, skip adb connect')
            return True
        if re.match(r'^[a-zA-Z0-9]+$', self.serial):
            if wait_device:
                if self._wait_device_appear(self.serial, first_devices=devices):
                    logger.info(f'Serial {self.serial} connected')
                    return True
                else:
                    logger.info(f'Serial {self.serial} is not connected')
                    return False
            logger.info(f'"{self.serial}" seems to be a Android serial, skip adb connect')
            return True

        for _ in range(3):
            msg = self.adb_client.connect(self.serial)
            logger.info(msg)
            if 'connected' in msg:
                return True
            elif 'bad port' in msg:
                possible_reasons('Serial incorrect, might be a typo')
                raise RequestHumanTakeover
            elif '(10061)' in msg:
                run_once(self.check_mumu_bridge_network)()
                logger.warning('No such device exists, please restart the emulator or set a correct serial')
                logger.warning('该模拟器 Serial 不存在，请重启模拟器或设置正确的 Serial。')
                logger.warning('ADB 无法连接至该模拟器，或是模拟器未启动。')
                raise EmulatorNotRunningError

        logger.warning(f'Failed to connect {self.serial} after 3 trial, assume connected')
        return False

    def check_mumu_bridge_network(self):
        if not self.is_mumu12_family:
            return True
        if not hasattr(self, 'find_emulator_instance'):
            return False
        instance = self.find_emulator_instance(
            serial=self.serial,
        )
        if instance is None:
            logger.warning(f'Failed to check check_mumu_bridge_network, emulator instance not found')
            return False
        file = instance.mumu_vms_config('customer_config.json')
        try:
            with open(file, mode='r', encoding='utf-8') as f:
                s = f.read()
                data = json.loads(s)
        except FileNotFoundError:
            logger.warning(f'Failed to check check_mumu_bridge_network, file {file} not exists')
            return False
        value = data.get('customer', {}).get('network_bridge_opened', None)
        logger.attr('customer.network_bridge_opened', value)
        if str(value).lower() == 'true':
            logger.critical('Please turn off "Network Bridging" in the settings of MuMuPlayer')
            logger.critical('请在MuMU模拟器设置中关闭 网络桥接')
            raise RequestHumanTakeover
        return True

    def release_resource(self):
        if hasattr(self, 'droidcast_stop'):
            try:
                self.droidcast_stop()
            except Exception:
                pass
        if hasattr(self, 'minitouch_stop'):
            try:
                self.minitouch_stop()
            except Exception:
                pass
        del_cached_property(self, 'droidcast_session')
        del_cached_property(self, '_minitouch_builder')

    def adb_disconnect(self):
        msg = self.adb_client.disconnect(self.serial)
        if msg:
            logger.info(msg)
        self.release_resource()

    def adb_restart(self):
        logger.info('Restart adb')
        self.adb_client.server_kill()
        del_cached_property(self, 'adb_client')
        self.release_resource()
        _ = self.adb_client

    def adb_reconnect(self):
        if len(self.list_device()) == 0:
            self.adb_restart()
            self.adb_connect()
        else:
            self.adb_disconnect()
            self.adb_connect()

    _orientation_description = {
        0: '正常',
        1: 'HOME 键在右侧',
        2: 'HOME 键在顶部',
        3: 'HOME 键在左侧',
    }
    orientation = 0

    @retry
    def get_orientation(self):
        """获取设备屏幕方向。

        Returns:
            int: 屏幕方向值：
                0: 正常
                1: HOME 键在右侧
                2: HOME 键在顶部
                3: HOME 键在左侧
        """
        _DISPLAY_RE = re.compile(
            r'.*DisplayViewport{.*valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*'
        )
        output = self.adb_shell(['dumpsys', 'display'])

        res = _DISPLAY_RE.search(output, 0)

        if res:
            o = int(res.group('orientation'))
            if o in Connection._orientation_description:
                pass
            else:
                o = 0
                logger.warning(f'Invalid device orientation: {o}, assume it is normal')
        else:
            o = 0
            logger.warning('Unable to get device orientation, assume it is normal')

        self.orientation = o
        logger.attr('Device Orientation', f'{o} ({Connection._orientation_description.get(o, "Unknown")})')
        return o

    @retry
    def app_current_adb(self):
        """
        获取当前前台应用的包名。

        Returns:
            当前前台应用的包名。

        Raises:
            OSError: 无法获取前台应用时抛出。

        """
        # 参考常见 dumpsys window/current focus 解析方式。
        # $ adb shell dumpsys window windows
        # 输出示例:
        #   mCurrentFocus=Window{41b37570 u0 com.incall.apps.launcher/com.incall.apps.launcher.Launcher}
        #   mFocusedApp=AppWindowToken{422df168 token=Token{422def98 ActivityRecord{422dee38 u0 com.example/.UI.play.PlayActivity t14}}}
        # 正则表达式
        #   r'mFocusedApp=.*ActivityRecord{\w+ \w+ (?P<package>.*)/(?P<activity>.*) .*'
        #   r'mCurrentFocus=Window{\w+ \w+ (?P<package>.*)/(?P<activity>.*)\}')
        _focusedRE = re.compile(
            r'mCurrentFocus=Window{.*\s+(?P<package>[^\s]+)/(?P<activity>[^\s]+)\}'
        )
        m = _focusedRE.search(self.adb_shell(['dumpsys', 'window', 'windows']))
        if m:
            return m.group('package')

        # 尝试: adb shell dumpsys activity top
        _activityRE = re.compile(
            r'ACTIVITY (?P<package>[^\s]+)/(?P<activity>[^/\s]+) \w+ pid=(?P<pid>\d+)'
        )
        output = self.adb_shell(['dumpsys', 'activity', 'top'])
        ms = _activityRE.finditer(output)
        ret = None
        for m in ms:
            ret = m.group('package')
        if ret:  # 取最后一个结果
            return ret
        raise OSError("Couldn't get focused app")

    def app_is_running(self) -> bool:
        package = self.app_current_adb()
        logger.attr('Package_name', package)
        return package == self.package

    def app_start_adb(self, package_name=None, activity_name=None, allow_failure=False):
        """
        启动应用，依次尝试 am start 和 monkey 方式。

        Args:
            package_name: 应用包名，为 None 时从配置获取。
            activity_name: Activity 名称，为 None 时从 config.ACTIVITY_NAME 获取，
                仍为 None 时通过 monkey 启动，monkey 失败后再通过 am 启动。
            allow_failure: 为 True 时不抛出 PackageNotInstalled 异常，直接返回 False。

        Returns:
            是否成功启动。

        Raises:
            PackageNotInstalled: 应用未安装且 allow_failure 为 False 时抛出。
        """
        if not package_name:
            package_name = self.package
        if not activity_name:
            activity_name = self.activity

        if activity_name:
            if self._app_start_adb_am(package_name, activity_name, allow_failure):
                return True
        if self._app_start_adb_monkey(package_name, allow_failure):
            return True
        if self._app_start_adb_am(package_name, activity_name, allow_failure):
            return True

        logger.error('app_start_adb: All trials failed')
        return False

    def _app_start_adb_am(self, package_name, activity_name=None, allow_failure=False):
        if not activity_name:
            return False
        if activity_name.startswith('.'):
            activity_name = package_name + activity_name

        output = self.adb_shell(['am', 'start', '-n', f'{package_name}/{activity_name}'])
        if 'Error' in output or 'Exception' in output:
            logger.warning(output)
            if 'does not exist' in output or 'not found' in output or 'Unknown package' in output:
                if allow_failure:
                    return False
                raise PackageNotInstalled(package_name)
            return False
        return True

    def _app_start_adb_monkey(self, package_name, allow_failure=False):
        output = self.adb_shell([
            'monkey', '-p', package_name,
            '-c', 'android.intent.category.LAUNCHER',
            '1'
        ])
        if 'No activities found' in output or 'monkey aborted' in output:
            logger.warning(output)
            if allow_failure:
                return False
            raise PackageNotInstalled(package_name)
        return True

    @retry
    def app_stop_adb(self, package_name=None):
        """停止应用：am force-stop。"""
        if not package_name:
            package_name = self.package
        self.adb_shell(['am', 'force-stop', package_name])
