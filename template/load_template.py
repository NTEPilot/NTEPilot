import os

from utils.logger import logger
from utils.image import load_image, get_bbox
from . import Template

class LoadTemplate(Template):
    def __init__(self, filename: str, rect=None):
        name = os.path.basename(filename).split('.')[0]
        img = load_image(filename)
        if img is None:
            logger.error(f"Failed to load template: {filename}")
            raise FileNotFoundError(f"Template file not found: {filename}")
        x1, y1, x2, y2 = get_bbox(img) if rect is None else rect
        super().__init__(name, img[y1:y2, x1:x2], (x1, y1, x2, y2))