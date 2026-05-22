from pathlib import Path

import numpy as np
import torch
from scipy.io.wavfile import write
from transformers import VitsModel, VitsTokenizer


class TTSModel:
    """Modelo TTS para convertir texto en audio WAV."""

    def __init__(self):
        """Carga tokenizer y modelo una sola vez en el dispositivo disponible."""
        model_name = "facebook/mms-tts-spa"
        self.tokenizer = VitsTokenizer.from_pretrained(model_name)
        self.model = VitsModel.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def synthesize(self, text: str, output_path: str) -> str:
        """Sintetiza audio desde texto y lo guarda en un archivo WAV."""
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            waveform = self.model(**inputs).waveform

        waveform_np = waveform.cpu().numpy().squeeze()
        waveform_np = np.asarray(waveform_np)

        write(
            output_path,
            rate=self.model.config.sampling_rate,
            data=waveform_np,
        )
        return output_path


def synthesize_comments(
    narrated_frames: list[dict],
    model: TTSModel,
    output_dir: str = "outputs/audio",
) -> list[dict]:
    """Genera audios para comentarios narrados y agrega su ruta."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    synthesized_frames: list[dict] = []

    for frame in narrated_frames:
        updated = dict(frame)
        try:
            output_path = f"{output_dir}/frame_{frame['frame_idx']}.wav"
            updated["audio_path"] = model.synthesize(frame["comment"], output_path)
        except Exception:
            updated["audio_path"] = None
        synthesized_frames.append(updated)

    return synthesized_frames
