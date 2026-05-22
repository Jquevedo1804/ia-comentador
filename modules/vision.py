from typing import Any

import numpy as np
import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor


class VisionModel:
    """Modelo de visión para describir frames con BLIP."""

    def __init__(self):
        """Carga procesador y modelo una sola vez en el dispositivo disponible."""
        model_name = "Salesforce/blip-image-captioning-base"
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def describe_frame(self, frame: np.ndarray) -> str:
        """Genera una descripción textual de un frame RGB."""
        image = Image.fromarray(frame)
        inputs = self.processor(image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        output = self.model.generate(**inputs, max_new_tokens=30)
        caption = self.processor.decode(output[0], skip_special_tokens=True)
        return caption


def analyze_frames(frames: list, model: VisionModel) -> list[dict]:
    """Analiza frames y retorna captions por índice."""
    results: list[dict[str, Any]] = []

    for i, frame in enumerate(frames):
        try:
            caption = model.describe_frame(frame)
            results.append({"frame_idx": i, "caption": caption})
        except Exception:
            results.append({"frame_idx": i, "caption": "error al procesar frame"})

    return results
