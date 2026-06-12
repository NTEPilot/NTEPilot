from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from NTEPilot.instance import Instance
from template import Template
from utils.image import crop, crop_to_text, extract_letters
from utils.logger import logger


MODEL_PATH = Path('./models/ocr/en.onnx')
DICT_PATH = Path('./models/ocr/en.txt')


class Ocr(Instance):
    INPUT_HEIGHT = 48
    WIDTH_ALIGNMENT = 8

    def __init__(self):
        self.characters = DICT_PATH.read_text(encoding="utf-8").split("\n")
        self.session = self._create_session(MODEL_PATH)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        input_shape = self.session.get_inputs()[0].shape
        if len(input_shape) >= 3 and isinstance(input_shape[2], int):
            self.input_height = input_shape[2]
        else:
            self.input_height = self.INPUT_HEIGHT

        output_shape = self.session.get_outputs()[0].shape
        self.class_count = output_shape[-1] if isinstance(output_shape[-1], int) else len(self.characters) + 1
        self.blank_index = 0 if self.class_count == len(self.characters) + 1 else None
        self.char_offset = 1 if self.blank_index == 0 else 0

        self.warmup()

    def ocr(self, target) -> str:
        image = getattr(self.device, "image", None)
        if image is None:
            raise RuntimeError("OCR requires a cached screenshot in self.device.image")

        rect = self._get_rect(target)
        roi = crop(image, rect, copy=False)
        letters = extract_letters(roi)
        text_image = crop_to_text(letters)
        input_tensor = self._preprocess(text_image)
        output = self.session.run([self.output_name], {self.input_name: input_tensor})[0]
        return self._decode(output)

    def warmup(self, widths=(64, 160, 320)) -> None:
        for width in widths:
            input_tensor = np.zeros((1, 3, self.input_height, width), dtype=np.float32)
            self.session.run([self.output_name], {self.input_name: input_tensor})

    def _create_session(self, model_path: Path) -> ort.InferenceSession:
        if not model_path.exists():
            raise FileNotFoundError(f"OCR model not found: {model_path}")

        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.enable_mem_pattern = False
        options.log_severity_level = 3

        available = ort.get_available_providers()
        providers = []
        if "DmlExecutionProvider" in available:
            providers.append("DmlExecutionProvider")
        providers.append("CPUExecutionProvider")

        try:
            session = ort.InferenceSession(str(model_path), sess_options=options, providers=providers)
        except Exception:
            if providers == ["CPUExecutionProvider"]:
                raise
            logger.exception("Failed to create OCR session with DirectML, falling back to CPU")
            session = ort.InferenceSession(
                str(model_path),
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )

        logger.info(f"OCR providers: {session.get_providers()}")
        return session

    @staticmethod
    def _get_rect(target):
        if isinstance(target, Template):
            return target.rect
        if len(target) != 4:
            raise ValueError(f"OCR target rect must contain 4 values, got {target!r}")
        x1, y1, x2, y2 = target
        return x1, y1, x2, y2

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        if image.size == 0:
            raise ValueError("OCR input image is empty")

        height, width = image.shape[:2]
        if height <= 0 or width <= 0:
            raise ValueError(f"OCR input image has invalid shape: {image.shape}")

        resized_width = max(8, round(width * self.input_height / height))
        padded_width = self._align_width(resized_width)
        interpolation = cv2.INTER_AREA if resized_width < width else cv2.INTER_LINEAR
        resized = cv2.resize(image, (resized_width, self.input_height), interpolation=interpolation)

        normalized = resized.astype(np.float32)
        normalized *= 1.0 / 127.5
        normalized -= 1.0

        input_tensor = np.zeros((1, 3, self.input_height, padded_width), dtype=np.float32)
        input_tensor[0, 0, :, :resized_width] = normalized
        input_tensor[0, 1, :, :resized_width] = normalized
        input_tensor[0, 2, :, :resized_width] = normalized
        return input_tensor

    def _decode(self, output: np.ndarray) -> str:
        if output.ndim == 3:
            output = output[0]
        indices = np.argmax(output, axis=-1)

        result: list[str] = []
        previous = -1
        for index in indices:
            index = int(index)
            if index == previous:
                continue
            previous = index

            if self.blank_index is not None and index == self.blank_index:
                continue

            char_index = index - self.char_offset
            if 0 <= char_index < len(self.characters):
                char = self.characters[char_index]
                if char:
                    result.append(char)

        return "".join(result)

    def _align_width(self, width: int) -> int:
        alignment = self.WIDTH_ALIGNMENT
        return ((width + alignment - 1) // alignment) * alignment
