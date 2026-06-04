
import socket
import time
import random

from utils.logger import logger
from adbutils import AdbTimeout, AdbConnection

RETRY_TRIES = 5
RETRY_DELAY = 3

class PackageNotInstalled(Exception):
    pass

class ImageTruncated(Exception):
    pass

def retry_sleep(trial):
    # First trial
    if trial == 0:
        return 0
    # Failed once, fast retry
    elif trial == 1:
        return 0
    # Failed twice
    elif trial == 2:
        return 1
    # Failed more
    else:
        return RETRY_DELAY

def possible_reasons(*args):
    """
    Show possible reasons

        Possible reason #1: <reason_1>
        Possible reason #2: <reason_2>
    """
    for index, reason in enumerate(args):
        index += 1
        logger.critical(f'Possible reason #{index}: {reason}')

def handle_adb_error(e):
    """
    Args:
        e (Exception):

    Returns:
        bool: If should retry
    """
    text = str(e)
    if 'not found' in text:
        # When you call `adb disconnect <serial>`
        # Or when adb server was killed (low possibility)
        # AdbError(device '127.0.0.1:59865' not found)
        logger.error(e)
        return True
    elif 'timeout' in text:
        # AdbTimeout(adb read timeout)
        logger.error(e)
        return True
    elif 'closed' in text:
        # AdbError(closed)
        # Usually after AdbTimeout(adb read timeout)
        # Disconnect and re-connect should fix this.
        logger.error(e)
        return True
    elif 'device offline' in text:
        # AdbError(device offline)
        # When a device that has been connected wirelessly is disconnected passively,
        # it does not disappear from the adb device list,
        # but will be displayed as offline.
        # In many cases, such as disconnection and recovery caused by network fluctuations,
        # or after VMOS reboot when running Alas on a phone,
        # the device is still available, but it needs to be disconnected and re-connected.
        logger.error(e)
        return True
    elif 'is offline' in text:
        # RuntimeError: USB device 127.0.0.1:7555 is offline
        # Raised by uiautomator2 when current adb service is killed by another version of adb service.
        logger.error(e)
        return True
    elif text == 'rest':
        # AdbError(rest)
        # Response telling adbd service has reset, client should reconnect
        logger.error(e)
        return True
    else:
        # AdbError()
        logger.exception(e)
        possible_reasons(
            'If you are using BlueStacks or LD player or WSA, please enable ADB in the settings of your emulator',
            'Emulator died, please restart emulator',
            'Serial incorrect, no such device exists or emulator is not running'
        )
        return False

def handle_unknown_host_service(e):
    """
    Args:
        e (Exception):

    Returns:
        bool: If should retry
    """
    text = str(e)
    if 'unknown host service' in text:
        # AdbError(unknown host service)
        # Another version of ADB service started, current ADB service has been killed.
        # Usually because user opened a Chinese emulator, which uses ADB from the Stone Age.
        logger.error(e)
        return True
    else:
        return False

IMAGE_TRUNCATED_THRESHOLD = 3
_image_truncated_counts: dict = {}

def report_image_truncated(serial: str) -> int:
    if serial is None:
        return 0
    cnt = _image_truncated_counts.get(serial, 0) + 1
    _image_truncated_counts[serial] = cnt
    return cnt

def reset_image_truncated(serial: str) -> None:
    if serial in _image_truncated_counts:
        del _image_truncated_counts[serial]

def handle_image_truncated(obj, exc: Exception) -> None:
    """
    Central handler for ImageTruncated: increment counter and try recovery when
    threshold reached. `obj` is expected to be a device/connection instance
    that may implement `droidcast_init`, `adb_reconnect`, `ascreencap_init`, etc.
    This function performs immediate recovery actions and resets the counter.
    """
    serial = getattr(obj, 'serial', None)
    cnt = report_image_truncated(serial)
    logger.error(f'ImageTruncated occurred ({cnt}) for device {serial}: {exc}')

    if cnt >= IMAGE_TRUNCATED_THRESHOLD:
        logger.warning(f'ImageTruncated reached threshold ({IMAGE_TRUNCATED_THRESHOLD}) for {serial}, attempting recovery')
        # Try specific recoveries in order of likelihood
        try:
            if hasattr(obj, 'droidcast_init'):
                logger.info('Attempting to restart DroidCast service')
                try:
                    obj.droidcast_init()
                except Exception:
                    logger.exception('Failed to restart DroidCast')
            # Try ascreencap init if available
            if hasattr(obj, 'ascreencap_init'):
                try:
                    obj.ascreencap_init()
                except Exception:
                    logger.exception('Failed to init ascreencap')
            # Reconnect adb as a final attempt
            if hasattr(obj, 'adb_reconnect'):
                try:
                    obj.adb_reconnect()
                except Exception:
                    logger.exception('Failed to adb_reconnect')
        finally:
            reset_image_truncated(serial)

def recv_all(stream, chunk_size=4096, recv_interval=0.000) -> bytes:
    """
    Args:
        stream:
        chunk_size:
        recv_interval (float): Default to 0.000, use 0.001 if receiving as server

    Returns:
        bytes:

    Raises:
        AdbTimeout
    """
    if isinstance(stream, AdbConnection):
        stream = stream.conn
        stream.settimeout(10)
    else:
        stream.settimeout(10)

    try:
        fragments = []
        while 1:
            chunk = stream.recv(chunk_size)
            if chunk:
                fragments.append(chunk)
                # See https://stackoverflow.com/questions/23837827/python-server-program-has-high-cpu-usage/41749820#41749820
                time.sleep(recv_interval)
            else:
                break
        return b''.join(fragments)
    except socket.timeout:
        raise AdbTimeout('adb read timeout')

def is_port_using(port_num):
    """ if port is using by others, return True. else return False """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    try:
        s.bind(('127.0.0.1', port_num))
        return False
    except OSError:
        # Address already bind
        return True
    finally:
        s.close()

def random_port(port_range):
    """ get a random port from port set """
    new_port = random.choice(list(range(*port_range)))
    if is_port_using(new_port):
        return random_port(port_range)
    else:
        return new_port