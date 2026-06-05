import cv2

class Template:
    def __init__(self, name, image, rect):
        self.name = name
        self.image = image
        self.rect = rect
        x1, y1, x2, y2 = rect
        self.pos = ((x1 + x2) // 2, (y1 + y2) // 2)
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        self.width = x2 - x1
        self.height = y2 - y1

    def __str__(self):
        return self.name
    
    def match(self, screenshot, offset=10, similarity=0.85):
        if screenshot is None or self.image is None:
            return False
            
        x1, y1, x2, y2 = self.rect
        
        h_img, w_img = screenshot.shape[:2]
        x1 = max(0, x1 - offset)
        y1 = max(0, y1 - offset)
        x2 = min(w_img, x2 + offset)
        y2 = min(h_img, y2 + offset)
        
        roi = screenshot[y1:y2, x1:x2]
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        res = cv2.matchTemplate(roi_gray, self.gray_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= similarity:
            self.pos = (x1 + max_loc[0] + self.width // 2, y1 + max_loc[1] + self.height // 2)
            return True
            
        return False