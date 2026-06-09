import cv2

from utils.image import get_color, color_similar
from utils.exceptions import ScriptError

class Template:
    def __init__(self, name, image, rect, method):
        self.name = name
        self.image = image
        self.rect = rect
        self.method = method
        x1, y1, x2, y2 = rect
        self.pos = ((x1 + x2) // 2, (y1 + y2) // 2)
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        self.width = self.gray_image.shape[1]
        self.height = self.gray_image.shape[0]
        self.color = cv2.mean(self.image)[:3]

    def __str__(self):
        return self.name
    
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
            self.pos = (x1 + max_loc[0] + self.width // 2, y1 + max_loc[1] + self.height // 2)
            return True
            
        return False

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