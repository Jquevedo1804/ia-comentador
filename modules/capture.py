import cv2
import numpy as np


def extract_frames(video_path: str, fps_sample: int = 2) -> list:
    """Extrae frames RGB redimensionados de un video MP4."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el archivo de video: {video_path}")

    frames: list[np.ndarray] = []
    frame_idx = 0

    try:
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0:
            raise ValueError("No se pudo obtener un FPS válido del video.")
        if fps_sample <= 0:
            raise ValueError("fps_sample debe ser mayor que 0.")

        frame_interval = int(video_fps / fps_sample)
        if frame_interval <= 0:
            frame_interval = 1

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (384, 384))
                frames.append(frame_resized)

            frame_idx += 1
    finally:
        cap.release()

    return frames
