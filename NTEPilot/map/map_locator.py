import cv2
import numpy as np

from .map_data import map_data
from .utils import MapView, MapMatchError, CROP
from utils.image import image_size, crop, limit_in


class MapLocator:
    SCALE = 0.1736
    MIN_SCORE = 0.2
    EARLY_SCORE = 0.6
                
    def __init__(self):
        self._cache = {}

    @property
    def big_rgb(self) -> np.ndarray:
        return map_data.big_map

    @staticmethod
    def preprocess(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Most map roads/buildings are low-saturation gray. This rejects colorful
        # icons and keeps enough white/gray road structure for matching.
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]
        mask = ((saturation < 80) & (value < 170)).astype(np.uint8) * 255

        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(gray, 30, 100)
        return cv2.bitwise_and(edges, mask)

    def _scaled_big(self, scale: float) -> np.ndarray:
        cached = self._cache.get(scale)
        if cached is not None:
            return cached
        scaled = cv2.resize(self.big_rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        prepared = self.preprocess(scaled)
        self._cache[scale] = prepared
        return prepared

    def locate(self, screenshot: np.ndarray) -> MapView:
        width, height = image_size(screenshot)
        crop_rect = self._fit_crop(CROP, width, height)
        left, top, right, bottom = crop_rect
        query = self.preprocess(crop(screenshot, crop_rect, copy=False))

        if np.count_nonzero(query) < 1000:
            raise MapMatchError("Not enough map detail in screenshot crop")

        prepared = self._scaled_big(self.SCALE)
        if prepared.shape[0] < query.shape[0] or prepared.shape[1] < query.shape[1]:
            raise MapMatchError("Big map shape is smaller than query shape")
            
        result = cv2.matchTemplate(prepared, query, cv2.TM_CCOEFF_NORMED)
        _, best_score, _, best_loc = cv2.minMaxLoc(result)

        if best_score < self.MIN_SCORE:
            raise MapMatchError(f"Map match score too low: {best_score:.3f}")

        origin_x = (best_loc[0] - left) / self.SCALE
        origin_y = (best_loc[1] - top) / self.SCALE
        view = MapView(origin_x, origin_y, self.SCALE, best_score, crop_rect, (width, height))

        return view

    @staticmethod
    def _fit_crop(crop: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
        left, top, right, bottom = crop
        return (
            int(limit_in(left, 0, width - 1)),
            int(limit_in(top, 0, height - 1)),
            int(limit_in(right, left + 1, width)),
            int(limit_in(bottom, top + 1, height)),
        )

map_locator = MapLocator()