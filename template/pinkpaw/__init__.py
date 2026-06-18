"""粉爪大劫案模板定义，专用图片可后续补入。
PinkPaw Heist template definitions; dedicated images can be added later.

作者: NTEPilot Contributors
Author: NTEPilot Contributors
日期: 2026-06-18
Date: 2026-06-18
"""

from __future__ import annotations

from pathlib import Path

from template import Template
from template.load_template import load_template


ASSET_DIR = Path("./template/pinkpaw/assets")


def _optional_template(filename: str, rect: tuple[int, int, int, int] | None = None, similarity_method: str | None = None) -> Template | None:
    """按需加载可选粉爪模板，图片未补时返回 None。
    Load an optional PinkPaw template, returning None when the image is not provided.

    Args:
        filename: 模板图片文件名。
                  Template image file name.
        rect: 识别区域，None 时使用图片自身区域。
              Recognition rectangle, or None to use the image bbox.
        similarity_method: 模板匹配方法。
                           Template matching method.

    Returns:
        已加载模板；图片不存在时返回 None。
        Loaded template, or None when the file does not exist.
    """
    path = ASSET_DIR / filename
    if not path.exists():
        return None
    return load_template(str(path), rect=rect, method=similarity_method)


INTERACTABLE = _optional_template("INTERACTABLE.png", rect=(680, 250, 1110, 680))
HEIST_INTERAC_LOCK_PICK = _optional_template("HEIST_INTERAC_LOCK_PICK.png", rect=(680, 250, 1110, 680))
HEIST_LOCK_PICK = _optional_template("HEIST_LOCK_PICK.png", rect=(720, 260, 1080, 520))
