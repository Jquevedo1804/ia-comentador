from difflib import SequenceMatcher


def filter_frames_to_comment(
    analyzed_frames: list[dict],
    cooldown_frames: int = 4,
    similarity_threshold: float = 0.7,
) -> list[dict]:
    """Selecciona solo frames con cambio de escena relevante."""
    selected_frames: list[dict] = []
    last_selected_caption = ""
    last_selected_idx = None

    for frame_data in analyzed_frames:
        current_idx = frame_data.get("frame_idx")
        current_caption = frame_data.get("caption", "")

        if current_idx is None:
            continue

        if last_selected_idx is None:
            selected = dict(frame_data)
            selected["reason"] = "inicio de la partida"
            selected_frames.append(selected)
            last_selected_idx = current_idx
            last_selected_caption = current_caption
            continue

        similarity = SequenceMatcher(None, last_selected_caption, current_caption).ratio()
        frames_since_last = current_idx - last_selected_idx
        cooldown_reached = frames_since_last > cooldown_frames

        strong_change_threshold = max(0.0, similarity_threshold - 0.2)
        is_strong_change = similarity < strong_change_threshold
        is_scene_change = similarity < similarity_threshold

        if is_strong_change:
            selected = dict(frame_data)
            selected["reason"] = "cambio de acción"
            selected_frames.append(selected)
            last_selected_idx = current_idx
            last_selected_caption = current_caption
            continue

        if cooldown_reached and is_scene_change:
            selected = dict(frame_data)
            selected["reason"] = "nuevo momento detectado"
            selected_frames.append(selected)
            last_selected_idx = current_idx
            last_selected_caption = current_caption

    return selected_frames
