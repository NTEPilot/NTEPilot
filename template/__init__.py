import cv2
import numpy as np
import random

from utils.image import get_color, color_similar
from utils.exceptions import ScriptError

class Template:
    def __init__(self, name, image, rect, method):
        self.name = name
        self.image = image
        self.rect = rect
        self.method = method
        x1, y1, x2, y2 = rect
        self._pos = ((x1 + x2) // 2, (y1 + y2) // 2)
        self._last_pos = None
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        self.width = self.gray_image.shape[1]
        self.height = self.gray_image.shape[0]
        self.color = cv2.mean(self.image)[:3]

    def __str__(self):
        return self.name

    @property
    def pos(self):
        x1, y1, x2, y2 = self.rect
        orig_cx = (x1 + x2) // 2
        orig_cy = (y1 + y2) // 2
        
        # Calculate offset from the original center to the matched position
        dx = self._pos[0] - orig_cx
        dy = self._pos[1] - orig_cy
        
        rx1, ry1, rx2, ry2 = x1 + dx, y1 + dy, x2 + dx, y2 + dy
        
        if rx1 > rx2:
            rx1, rx2 = rx2, rx1
        if ry1 > ry2:
            ry1, ry2 = ry2, ry1
            
        width = rx2 - rx1
        height = ry2 - ry1
        
        total_points = (width + 1) * (height + 1)
        if total_points <= 1:
            return (rx1, ry1)
            
        while True:
            rx = random.randint(rx1, rx2)
            ry = random.randint(ry1, ry2)
            if (rx, ry) != self._last_pos:
                self._last_pos = (rx, ry)
                return (rx, ry)

    def match_template_gray(self, screenshot, offset=10, similarity=0.85):
        if screenshot is None or self.image is None:
            return False
            
        x1, y1, x2, y2 = self.rect
        
        h_img, w_img = screenshot.shape[:2]
        x1 = max(0, x1 - offset)
        y1 = max(0, y1 - offset)
        x2 = min(w_img, x2 + offset)
        y2 = min(h_img, y2 + offset)
        
        roi = screenshot[y1:y2, x1:x2]
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        
        res = cv2.matchTemplate(roi_gray, self.gray_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= similarity:
            self._pos = (x1 + max_loc[0] + self.width // 2, y1 + max_loc[1] + self.height // 2)
            return True
            
        return False

    def match_all_template_gray(self, screenshot, rect=None, offset=10, similarity=0.85):
        if screenshot is None or self.image is None:
            return []
            
        x1, y1, x2, y2 = rect if rect is not None else self.rect
        
        h_img, w_img = screenshot.shape[:2]
        x1 = max(0, x1 - offset)
        y1 = max(0, y1 - offset)
        x2 = min(w_img, x2 + offset)
        y2 = min(h_img, y2 + offset)
        
        if x2 <= x1 or y2 <= y1:
            return []
            
        roi = screenshot[y1:y2, x1:x2]
        if roi.shape[0] < self.height or roi.shape[1] < self.width:
            return []
            
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        res = cv2.matchTemplate(roi_gray, self.gray_image, cv2.TM_CCOEFF_NORMED)
        
        loc = np.where(res >= similarity)
        points = []
        for y, x in zip(*loc):
            points.append((x, y, res[y, x]))
            
        # Sort by match score descending to process best matches first
        points = sorted(points, key=lambda p: p[2], reverse=True)
        
        results = []
        # Non-maximum suppression to filter out overlapping matching regions
        min_dist = max(10, min(self.width, self.height) // 2)
        for x, y, score in points:
            too_close = False
            for rx, ry in results:
                if abs(x - rx) < min_dist and abs(y - ry) < min_dist:
                    too_close = True
                    break
            if not too_close:
                results.append((x, y))
                
        # Return center positions of matches in the original screenshot coordinates
        final_positions = []
        for rx, ry in results:
            center_x = int(x1 + rx + self.width // 2)
            center_y = int(y1 + ry + self.height // 2)
            final_positions.append((center_x, center_y))
            
        return final_positions

    def match_avg_color(self, screenshot, threshold=10, **kwargs):
        if screenshot is None or self.image is None:
            return False
            
        screenshot_color = get_color(screenshot, self.rect)
        
        return color_similar(screenshot_color, self.color, threshold)

    def match(self, screenshot, *args, **kwargs):
        if self.method == 'template_gray':
            return self.match_template_gray(screenshot, *args, **kwargs)
        elif self.method == 'avg_color':
            return self.match_avg_color(screenshot, *args, **kwargs)
        else:
            raise ScriptError(f"Invalid template method: {self.method}")

    def match_all(self, screenshot, *args, **kwargs):
        if self.method == 'template_gray':
            return self.match_all_template_gray(screenshot, *args, **kwargs)
        else:
            raise ScriptError(f"match_all not implemented for method: {self.method}")