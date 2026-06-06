import cv2
import numpy as np
from PIL import Image

class ImageNotSupported(Exception):
    """当无法对图像执行计算操作时抛出此异常。"""
    pass

def limit_in(x, lower, upper):
    """
    将 x 限制在 [lower, upper] 范围内。

    Args:
        x: 待限制的值。
        lower: 下限。
        upper: 上限。

    Returns:
        int, float: 限制后的值。
    """
    return max(min(x, upper), lower)

def xywh2xyxy(area):
    """将 (x, y, 宽度, 高度) 格式转换为 (x1, y1, x2, y2) 格式。"""
    x, y, w, h = area
    return x, y, x + w, y + h

def xyxy2xywh(area):
    """将 (x1, y1, x2, y2) 格式转换为 (x, y, 宽度, 高度) 格式。"""
    x1, y1, x2, y2 = area
    return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)

def load_image(file, area=None):
    """
    加载图像并移除 alpha 通道，类似 pillow 的行为。

    Args:
        file (str): 图像文件路径。
        area (tuple): 裁剪区域。

    Returns:
        np.ndarray: 图像数组。
    """
    # 始终记得关闭 Image 对象
    with Image.open(file) as f:
        if area is not None:
            f = f.crop(area)
        f = f.convert('RGB')
        image = np.array(f)

    return image


def save_image(image, file):
    """
    保存图像，类似 pillow 的行为。

    Args:
        image (np.ndarray): 图像数组。
        file (str): 保存路径。
    """
    # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # cv2.imwrite(file, image)
    Image.fromarray(image).save(file)


def copy_image(src):
    """
    等效于 image.copy() 但速度略快。

    复制 1280*720*3 图像的时间开销：
        image.copy()      0.743ms
        copy_image(image) 0.639ms

    Args:
        src: 源图像数组。

    Returns:
        np.ndarray: 图像副本。
    """
    dst = np.empty_like(src)
    cv2.copyTo(src, None, dst)
    return dst


def crop(image, area, copy=True):
    """
    裁剪图像，类似 pillow 的 crop 行为，适用于 opencv/numpy。
    当裁剪区域超出图像边界时，使用黑色填充。

    Args:
        image (np.ndarray): 图像数组。
        area: 裁剪区域 (x1, y1, x2, y2)。
        copy (bool): 是否复制裁剪结果。

    Returns:
        np.ndarray: 裁剪后的图像数组。
    """
    # map(round, area)
    x1, y1, x2, y2 = area
    x1 = round(x1)
    y1 = round(y1)
    x2 = round(x2)
    y2 = round(y2)
    # h, w = image.shape[:2]
    shape = image.shape
    h = shape[0]
    w = shape[1]
    # 上, 下, 左, 右
    # border = np.maximum((0 - y1, y2 - h, 0 - x1, x2 - w), 0)
    overflow = False
    if y1 >= 0:
        top = 0
        if y1 >= h:
            overflow = True
    else:
        top = -y1
    if y2 > h:
        bottom = y2 - h
    else:
        bottom = 0
        if y2 <= 0:
            overflow = True
    if x1 >= 0:
        left = 0
        if x1 >= w:
            overflow = True
    else:
        left = -x1
    if x2 > w:
        right = x2 - w
    else:
        right = 0
        if x2 <= 0:
            overflow = True
    # 如果溢出，返回空图像
    if overflow:
        if len(shape) == 2:
            size = (y2 - y1, x2 - x1)
        else:
            size = (y2 - y1, x2 - x1, shape[2])
        return np.zeros(size, dtype=image.dtype)
    # x1, y1, x2, y2 = np.maximum((x1, y1, x2, y2), 0)
    if x1 < 0:
        x1 = 0
    if y1 < 0:
        y1 = 0
    if x2 < 0:
        x2 = 0
    if y2 < 0:
        y2 = 0
    # 裁剪图像
    image = image[y1:y2, x1:x2]
    # 如果需要填充边界
    if top or bottom or left or right:
        if len(shape) == 2:
            value = 0
        else:
            value = tuple(0 for _ in range(image.shape[2]))
        return cv2.copyMakeBorder(image, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT, value=value)
    elif copy:
        return copy_image(image)
    else:
        return image


def resize(image, size):
    """
    调整图像大小，类似 pillow 的 image.resize()，使用 opencv 实现。
    pillow 默认使用 PIL.Image.NEAREST 插值。

    Args:
        image (np.ndarray): 图像数组。
        size: 目标大小 (宽, 高)。

    Returns:
        np.ndarray: 调整大小后的图像数组。
    """
    return cv2.resize(image, size, interpolation=cv2.INTER_NEAREST)


def image_channel(image):
    """获取图像的通道数。

    Args:
        image (np.ndarray): 图像数组。

    Returns:
        int: 0 表示灰度图，3 表示 RGB 图像。
    """
    return image.shape[2] if len(image.shape) == 3 else 0


def image_size(image):
    """获取图像的尺寸。

    Args:
        image (np.ndarray): 图像数组。

    Returns:
        int, int: 宽度和高度。
    """
    shape = image.shape
    return shape[1], shape[0]

def get_color(image, area):
    """计算图像指定区域的平均颜色。

    Args:
        image (np.ndarray): 截图。
        area (tuple): (左上角 x, 左上角 y, 右下角 x, 右下角 y)。

    Returns:
        tuple: (r, g, b) 平均颜色值。
    """
    temp = crop(image, area, copy=False)
    color = cv2.mean(temp)
    return color[:3]

def get_bbox(image, threshold=0):
    """
    获取图像内容的外接边界框。
    pillow getbbox() 的 opencv 实现。

    Args:
        image (np.ndarray): 图像数组。
        threshold (int): 颜色阈值。
            color > threshold 视为内容，color <= threshold 视为背景。

    Returns:
        tuple[int, int, int, int]: 边界框区域 (x1, y1, x2, y2)。

    Raises:
        ImageNotSupported: 获取边界框失败时抛出。
    """
    channel = image_channel(image)
    # 转换为灰度图
    if channel == 3:
        # RGB
        mask = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY, dst=mask)
    elif channel == 0:
        # 灰度图
        _, mask = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    elif channel == 4:
        # RGBA
        mask = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY, dst=mask)
    else:
        raise ImageNotSupported(f'shape={image.shape}')

    # 查找边界框
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_y, min_x = mask.shape
    max_x = 0
    max_y = 0
    # 全黑图像
    if not contours:
        raise ImageNotSupported(f'Cannot get bbox from a pure black image')
    for contour in contours:
        # x, y, w, h
        x1, y1, x2, y2 = cv2.boundingRect(contour)
        x2 += x1
        y2 += y1
        if x1 < min_x:
            min_x = x1
        if y1 < min_y:
            min_y = y1
        if x2 > max_x:
            max_x = x2
        if y2 > max_y:
            max_y = y2
    if min_x < max_x and min_y < max_y:
        return min_x, min_y, max_x, max_y
    else:
        # 正常情况下不应出现
        raise ImageNotSupported(f'Empty bbox {(min_x, min_y, max_x, max_y)}')

def color_similar(color1, color2, threshold=10):
    """
    判断两个颜色是否相似，当容差小于等于阈值时视为相似。
    容差 = Max(正差值_rgb) + Max(-负差值_rgb)
    与 Photoshop 中的容差计算方式相同。

    Args:
        color1 (tuple): 颜色1 (r, g, b)。
        color2 (tuple): 颜色2 (r, g, b)。
        threshold (int): 容差阈值，默认为 10。

    Returns:
        bool: 两颜色相似返回 True。
    """
    # print(color1, color2)
    # diff = np.array(color1).astype(int) - np.array(color2).astype(int)
    # diff = np.max(np.maximum(diff, 0)) - np.min(np.minimum(diff, 0))
    diff_r = color1[0] - color2[0]
    diff_g = color1[1] - color2[1]
    diff_b = color1[2] - color2[2]

    max_positive = 0
    max_negative = 0
    if diff_r > max_positive:
        max_positive = diff_r
    elif diff_r < max_negative:
        max_negative = diff_r
    if diff_g > max_positive:
        max_positive = diff_g
    elif diff_g < max_negative:
        max_negative = diff_g
    if diff_b > max_positive:
        max_positive = diff_b
    elif diff_b < max_negative:
        max_negative = diff_b

    diff = max_positive - max_negative
    return diff <= threshold