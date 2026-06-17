import math
from dataclasses import dataclass

import cv2
import numpy as np

from template import Template


@dataclass(frozen=True)
class NavigationState:
    route_angle: float | None
    route_pixels: int
    nearest_distance: float
    distance: float

    @property
    def has_route(self) -> bool:
        return self.route_angle is not None


@dataclass(frozen=True)
class MinimapTemplateOffset:
    """小地图终点模板相对当前截图的像素偏移。
    Pixel offset of a minimap target template relative to the current screenshot.

    Attributes:
        dx: 当前截图相对终点模板的水平偏移，正数表示目标在小地图右侧。
            Horizontal offset; positive means the target is to the right on the minimap.
        dy: 当前截图相对终点模板的垂直偏移，正数表示目标在小地图下方。
            Vertical offset; positive means the target is downward on the minimap.
        score: 模板匹配分数，越接近 1 表示越可信。
               Template matching score; closer to 1 means more reliable.
    """

    dx: int
    dy: int
    score: float

    @property
    def aligned(self) -> bool:
        """判断当前截图是否已和终点模板逐像素对齐。
        Return whether the current screenshot is pixel-aligned with the target template.
        """
        return self.dx == 0 and self.dy == 0


class MinimapNavigation:
    CENTER = (111, 97)
    RADIUS = 78
    INNER_MASK_RADIUS = 17
    ARRIVAL_NEAREST_DISTANCE = 18
    TEMPLATE_CURSOR_MASK_RADIUS = 26
    TEMPLATE_SEARCH_RADIUS = 28
    TEMPLATE_MIN_SCORE = 0.85

    def __init__(self, camera_angle: float):
        self.camera_angle = camera_angle
        # 上一次计算的移动角度。 The last calculated move angle.
        self.last_move_angle: float | None = None

    def analyze(self, image: np.ndarray) -> NavigationState:
        route_mask = self._route_mask(image)
        route_angle, nearest_distance, distance = self._route_angle(route_mask)

        if route_angle is not None:
            self.last_route_angle = route_angle

        # 过滤距离中心 70 像素以外的边缘噪点，只统计内部路线像素。
        # Filter out edge noise beyond 70 pixels from the center, only counting inner route pixels.
        ys, xs = np.where(route_mask > 0)
        route_pixels = int(np.count_nonzero(np.hypot(xs - self.CENTER[0], ys - self.CENTER[1]) <= 70.0))

        return NavigationState(
            route_angle=route_angle,
            route_pixels=route_pixels,
            nearest_distance=nearest_distance,
            distance=distance,
        )

    def move_angle(self, state: NavigationState) -> float | None:
        route_angle = state.route_angle
        if route_angle is None:
            move_angle = None
        else:
            move_angle = (route_angle - self.camera_angle) % 360
            # 记录最后移动的角度。 Record the last move angle.
            self.last_move_angle = move_angle
        return move_angle

    def arrived(self, state: NavigationState) -> bool:
        return state.route_pixels < 15

    def template_offset(self, image: np.ndarray, template: Template) -> MinimapTemplateOffset | None:
        """计算当前小地图与终点模板之间的像素级偏移。
        Calculate the pixel-level offset between the current minimap and a target template.

        Args:
            image: 当前屏幕截图。
                   Current screen screenshot.
            template: 人物站在真实终点时截取的小地图模板。
                      Minimap template captured while the character stands at the real endpoint.

        Returns:
            匹配成功时返回偏移和分数，匹配分数过低时返回 None。
            Offset and score when matching succeeds, otherwise None for low-confidence matches.
        """
        x1, y1, x2, y2 = template.rect
        height, width = image.shape[:2]
        search_x1 = max(0, x1 - self.TEMPLATE_SEARCH_RADIUS)
        search_y1 = max(0, y1 - self.TEMPLATE_SEARCH_RADIUS)
        search_x2 = min(width, x2 + self.TEMPLATE_SEARCH_RADIUS)
        search_y2 = min(height, y2 + self.TEMPLATE_SEARCH_RADIUS)

        roi = image[search_y1:search_y2, search_x1:search_x2]
        if roi.shape[0] < template.height or roi.shape[1] < template.width:
            return None

        roi_gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        target_gray = cv2.cvtColor(template.image, cv2.COLOR_RGB2GRAY)
        mask = self._template_mask(template)
        result: np.ndarray = cv2.matchTemplate(roi_gray, target_gray, cv2.TM_CCORR_NORMED, mask=mask)
        result = np.asarray(np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0), dtype=np.float32)
        _, max_score, _, max_loc = cv2.minMaxLoc(result)
        if max_score < self.TEMPLATE_MIN_SCORE:
            return None

        matched_x = search_x1 + max_loc[0]
        matched_y = search_y1 + max_loc[1]
        return MinimapTemplateOffset(
            dx=matched_x - x1,
            dy=matched_y - y1,
            score=float(max_score),
        )

    def _minimap_circle(self, shape: tuple[int, int]) -> np.ndarray:
        height, width = shape
        cx, cy = self.CENTER
        yy, xx = np.ogrid[:height, :width]
        return (xx - cx) ** 2 + (yy - cy) ** 2 <= self.RADIUS ** 2

    def _template_mask(self, template: Template) -> np.ndarray:
        """生成终点模板匹配掩码，屏蔽小地图中心的角色光标朝向。
        Build a template matching mask that hides the minimap center cursor direction.
        """
        x1, y1, _, _ = template.rect
        mask = np.full((template.height, template.width), 255, dtype=np.uint8)
        cursor_x = self.CENTER[0] - x1
        cursor_y = self.CENTER[1] - y1
        if 0 <= cursor_x < template.width and 0 <= cursor_y < template.height:
            cv2.circle(mask, (cursor_x, cursor_y), self.TEMPLATE_CURSOR_MASK_RADIUS, 0, -1)
        return mask

    def _route_mask(self, image: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        height, width = image.shape[:2]
        cx, cy = self.CENTER
        yy, xx = np.ogrid[:height, :width]
        circle = self._minimap_circle((height, width))
        inner = (xx - cx) ** 2 + (yy - cy) ** 2 <= self.INNER_MASK_RADIUS ** 2
        blue = (
            (hsv[:, :, 0] >= 78)
            & (hsv[:, :, 0] <= 105)
            & (hsv[:, :, 1] >= 110)
            & (hsv[:, :, 2] >= 115)
        )
        mask = (circle & ~inner & blue).astype(np.uint8) * 255
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    def _route_angle(self, mask: np.ndarray) -> tuple[float | None, float, float]:
        cx, cy = self.CENTER
        route_points = np.column_stack(np.where(mask > 0))
        if len(route_points) == 0:
            return None, 0.0, 0.0
        route_distance = np.hypot(route_points[:, 1] - cx, route_points[:, 0] - cy)
        nearest_distance = float(np.min(route_distance))
        farthest_distance = float(np.max(route_distance))

        labels_count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        candidates = []
        for label in range(1, labels_count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < 8:
                continue
            ys, xs = np.where(labels == label)
            min_distance = float(np.min(np.hypot(xs - cx, ys - cy)))
            if min_distance > 75:
                continue
            candidates.append((min_distance, area, xs, ys))

        if not candidates:
            return None, nearest_distance, farthest_distance

        candidates.sort(key=lambda item: (item[0], -item[1]))
        _, _, xs, ys = candidates[0]
        dx = xs.astype(float) - cx
        dy = ys.astype(float) - cy
        distance = np.hypot(dx, dy)

        nearest_distance = float(np.min(distance))
        farthest_distance = float(np.max(distance))

        if farthest_distance < self.ARRIVAL_NEAREST_DISTANCE:
            return None, nearest_distance, farthest_distance

        near_limit = min(farthest_distance, max(22.0, float(np.percentile(distance, 40))))
        selected = distance <= near_limit
        if int(np.count_nonzero(selected)) < 8:
            selected = distance <= float(np.percentile(distance, 80))
        weights = 1.0 / np.maximum(distance[selected], 1.0)
        x = float(np.average(dx[selected], weights=weights))
        y = float(np.average(dy[selected], weights=weights))
        return self._screen_vector_to_angle(x, y), nearest_distance, farthest_distance

    @staticmethod
    def _screen_vector_to_angle(x: float, y: float) -> float:
        return math.degrees(math.atan2(x, -y)) % 360

    @staticmethod
    def angle_delta(target: float, current: float) -> float:
        return (target - current + 180) % 360 - 180
