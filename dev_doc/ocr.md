# OCR 系统

基于 ONNX Runtime 的文字识别，支持 DirectML (GPU) 和 CPU 推理。

---

## 模型

**目录**: `./models/ocr/`

| 模型 | 文件 | 用途 |
|------|------|------|
| 英文 | `en.onnx` + `en.txt` | 英文字符识别 |
| 中文 | `cn.onnx` + `cn.txt` | 中文字符识别 |

---

## OcrModel 数据类

```python
OcrModel(
    name: str,           # 模型名称
    characters: list,    # 字符列表
    session,             # ONNX 推理会话
    input_name: str,     # 输入张量名
    output_name: str,    # 输出张量名
    input_height: int = 48,  # 输入高度
    class_count: int,    # 类别数
    blank_index: int,    # CTC blank 索引
    char_offset: int,    # 字符偏移量
)
```

---

## OCR 流程

`ocr(target, model, letter_color, screenshot)` — 完整 OCR 流程：

1. **截图** — 获取当前屏幕截图
2. **裁剪** — 根据 target 区域裁剪
3. **提取字母** — `extract_letters(image, letter)` 根据颜色提取文字（白色字母提取为黑色，背景为白色）
4. **预处理** — `_preprocess(image, model)` 缩放到 48px 高，宽度 8 对齐，归一化到 [-1, 1]
5. **推理** — ONNX Runtime 推理
6. **解码** — `_decode(output, model)` CTC 贪心解码（去重 + 去 blank）

---

## 使用方式

```python
from NTEPilot.ocr import Ocr

class MyTool(UI, Ocr):
    def run(self):
        text = self.ocr(target=(x, y, w, h), model="cn", letter_color="white")
```

---

## 角色名 OCR 纠错

`NTEPilot/bond/ocr.py` 中的 `CharaOcr` 继承 `Ocr`，覆盖 `ocr()` 方法，纠正常见 OCR 错误：
- "驱" → "翳"
- "得" → "浔"
- "小" → "小吱"
