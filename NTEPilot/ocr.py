from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from NTEPilot.instance import Instance
from template import Template
from utils.image import crop, crop_to_text, extract_letters, save_image
from utils.logger import logger


MODEL_DIR = Path('./models/ocr')


@dataclass(frozen=True)
class OcrModel:
    name: str
    characters: list[str]
    session: ort.InferenceSession
    input_name: str
    output_name: str
    input_height: int
    class_count: int
    blank_index: int | None
    char_offset: int


class Ocr(Instance):
    INPUT_HEIGHT = 48
    WIDTH_ALIGNMENT = 8
    MODEL_FILES = {
        'en': (MODEL_DIR / 'en.onnx', MODEL_DIR / 'en.txt'),
        'cn': (MODEL_DIR / 'cn.onnx', MODEL_DIR / 'cn.txt'),
    }

    def __init__(self, config, device=None):
        super().__init__(config=config, device=device)

        self.models = {
            name: self._load_model(name, model_path, dict_path)
            for name, (model_path, dict_path) in self.MODEL_FILES.items()
        }

        self.warmup()

    def ocr(self, target, model='en', letter_color=(255, 255, 255), screenshot=True, save_debug_image=False) -> str:
        if screenshot:
            self.device.screenshot()
        ocr_model = self._get_model(model)
        rect = self._get_rect(target)
        roi = crop(self.device.image, rect, copy=False)
        letters = extract_letters(roi, letter=letter_color)
        text_image = crop_to_text(letters)
        if save_debug_image:
            save_image(text_image, f'./debug/ocr_{model}.png')
        input_tensor = self._preprocess(text_image, ocr_model)
        output = ocr_model.session.run([ocr_model.output_name], {ocr_model.input_name: input_tensor})[0]
        result = self._decode(output, ocr_model)
        logger.attr(f'OCR {ocr_model.name} result', result)
        return result

    def warmup(self, widths=(64, 160, 320)) -> None:
        for ocr_model in self.models.values():
            for width in widths:
                input_tensor = np.zeros((1, 3, ocr_model.input_height, width), dtype=np.float32)
                ocr_model.session.run([ocr_model.output_name], {ocr_model.input_name: input_tensor})

    def _load_model(self, name: str, model_path: Path, dict_path: Path) -> OcrModel:
        if not dict_path.exists():
            raise FileNotFoundError(f"OCR dict not found: {dict_path}")

        characters = dict_path.read_text(encoding="utf-8").split("\n")
        session = self._create_session(name, model_path)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name

        input_shape = session.get_inputs()[0].shape
        if len(input_shape) >= 3 and isinstance(input_shape[2], int):
            input_height = input_shape[2]
        else:
            input_height = self.INPUT_HEIGHT

        output_shape = session.get_outputs()[0].shape
        class_count = output_shape[-1] if isinstance(output_shape[-1], int) else len(characters) + 1
        blank_index = 0 if class_count == len(characters) + 1 else None
        char_offset = 1 if blank_index == 0 else 0

        return OcrModel(
            name=name,
            characters=characters,
            session=session,
            input_name=input_name,
            output_name=output_name,
            input_height=input_height,
            class_count=class_count,
            blank_index=blank_index,
            char_offset=char_offset,
        )

    def _create_session(self, name: str, model_path: Path) -> ort.InferenceSession:
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

        logger.info(f"OCR model={name} providers: {session.get_providers()}")
        return session

    def _get_model(self, model: str) -> OcrModel:
        model = model.lower()
        if model not in self.models:
            raise ValueError(f"Unsupported OCR model {model!r}, available models: {', '.join(sorted(self.models))}")
        return self.models[model]

    @staticmethod
    def _get_rect(target):
        if isinstance(target, Template):
            return target.rect
        if len(target) != 4:
            raise ValueError(f"OCR target rect must contain 4 values, got {target!r}")
        x1, y1, x2, y2 = target
        return x1, y1, x2, y2

    def _preprocess(self, image: np.ndarray, model: OcrModel) -> np.ndarray:
        if image.size == 0:
            raise ValueError("OCR input image is empty")

        height, width = image.shape[:2]
        if height <= 0 or width <= 0:
            raise ValueError(f"OCR input image has invalid shape: {image.shape}")

        resized_width = max(8, round(width * model.input_height / height))
        padded_width = self._align_width(resized_width)
        interpolation = cv2.INTER_AREA if resized_width < width else cv2.INTER_LINEAR
        resized = cv2.resize(image, (resized_width, model.input_height), interpolation=interpolation)

        normalized = resized.astype(np.float32)
        normalized *= 1.0 / 127.5
        normalized -= 1.0

        input_tensor = np.zeros((1, 3, model.input_height, padded_width), dtype=np.float32)
        input_tensor[0, 0, :, :resized_width] = normalized
        input_tensor[0, 1, :, :resized_width] = normalized
        input_tensor[0, 2, :, :resized_width] = normalized
        return input_tensor

    def _decode(self, output: np.ndarray, model: OcrModel) -> str:
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

            if model.blank_index is not None and index == model.blank_index:
                continue

            char_index = index - model.char_offset
            if 0 <= char_index < len(model.characters):
                char = model.characters[char_index]
                if char:
                    result.append(char)

        return "".join(result)

    def _align_width(self, width: int) -> int:
        alignment = self.WIDTH_ALIGNMENT
        return ((width + alignment - 1) // alignment) * alignment
