import os

from utils.logger import logger
from utils.image import load_image, get_bbox
from . import Template

def load_template(filename, rect=None, method=None):
    name = os.path.basename(filename).split('.')[0]
    img = load_image(filename)
    if img is None:
        logger.error(f"Failed to load template: {filename}")
        raise FileNotFoundError(f"Template file not found: {filename}")
    x1, y1, x2, y2 = get_bbox(img)
    return Template(
        name,
        img[y1:y2, x1:x2],
        rect = rect or (x1, y1, x2, y2),
        method = method or 'template_gray'
    )