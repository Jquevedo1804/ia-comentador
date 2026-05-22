"""Comentarista IA de Valorant — Aplicación principal Streamlit."""

import io
import os
import sys

import streamlit as st

os.environ["TQDM_DISABLE"] = "1"

from modules.capture import extract_frames
from modules.heuristic import filter_frames_to_comment
from modules.narrator import CATEGORY_EMOJI, NarratorModel, narrate_frames
from modules.tts import TTSModel, synthesize_comments
from modules.vision import VisionModel, analyze_frames


def _load_safe(factory):
    """Carga un modelo redirigiendo stdout/stderr para evitar OSError en Windows."""
    _stdout = sys.stdout
    _stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        return factory()
    finally:
        sys.stdout = _stdout
        sys.stderr = _stderr


# ── Configuración de página (DEBE ser la primera llamada Streamlit) ──────
st.set_page_config(
    page_title="Comentarista IA de Valorant",
    layout="wide",
    page_icon="🎮",
)

# ── Carga de modelos ─────────────────────────────────────────────────────
if "vision_model" not in st.session_state:
    with st.spinner("🔍 Cargando modelo de visión (BLIP)..."):
        st.session_state.vision_model = _load_safe(VisionModel)

if "narrator_model" not in st.session_state:
    # El narrador ya no usa modelo ML — inicialización instantánea
    st.session_state.narrator_model = NarratorModel()

if "tts_model" not in st.session_state:
    with st.spinner("🔊 Cargando modelo de voz (MMS-TTS español)..."):
        st.session_state.tts_model = _load_safe(TTSModel)

vision_model = st.session_state.vision_model
narrator_model = st.session_state.narrator_model
tts_model = st.session_state.tts_model

# ── Encabezado ───────────────────────────────────────────────────────────
st.title("🎮 Comentarista IA de Valorant")
st.caption(
    "Sube un video de Valorant y obtén comentarios automáticos con voz, "
    "como si tuvieras un caster profesional narrando tu partida."
)

# ── Barra lateral ────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Configuración")

fps_sample = st.sidebar.slider(
    "Frames por segundo a analizar",
    min_value=1,
    max_value=5,
    value=2,
    help="Más FPS = más frames analizados, más detalle pero más lento.",
)
cooldown_frames = st.sidebar.slider(
    "Cooldown entre comentarios (frames)",
    min_value=2,
    max_value=10,
    value=4,
    help="Mínimo de frames entre comentarios para evitar saturar.",
)
similarity_threshold = st.sidebar.slider(
    "Umbral de similitud de escena",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.05,
    help="Menor valor = más sensible a cambios de escena.",
)

st.sidebar.divider()
st.sidebar.markdown(
    "**Categorías de momentos:**\n"
    "- ⚔️ Combate\n"
    "- 💀 Eliminación\n"
    "- ✨ Habilidad\n"
    "- 🏃 Movimiento\n"
    "- 🎮 General"
)

# ── Carga de video ───────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📁 Sube un archivo de video .mp4",
    type=["mp4"],
)

if uploaded_file is None:
    st.info("👆 Sube un archivo .mp4 de tu partida de Valorant para comenzar.")
    st.stop()

with open("temp_video.mp4", "wb") as f:
    f.write(uploaded_file.read())

st.video("temp_video.mp4")

# ── Análisis ─────────────────────────────────────────────────────────────
if st.button("🎬 Analizar video", type="primary"):
    try:
        with st.spinner("🎞️ Extrayendo frames del video..."):
            frames = extract_frames("temp_video.mp4", fps_sample)
        st.success(f"✅ {len(frames)} frames extraídos")

        with st.spinner("👁️ Analizando frames con inteligencia artificial..."):
            analyzed = analyze_frames(frames, vision_model)
        st.success(f"✅ {len(analyzed)} frames analizados")

        with st.spinner("🔎 Filtrando momentos relevantes..."):
            filtered = filter_frames_to_comment(
                analyzed, cooldown_frames, similarity_threshold
            )
        st.success(f"✅ {len(filtered)} momentos seleccionados para comentar")

        with st.spinner("🎙️ Generando comentarios de narrador..."):
            narrated = narrate_frames(filtered, narrator_model)

        with st.spinner("🔊 Convirtiendo comentarios a audio..."):
            final_results = synthesize_comments(narrated, tts_model)

        # ── Resultados ───────────────────────────────────────────────
        st.divider()
        st.subheader("🏆 Comentarios generados")

        for frame_data in final_results:
            idx = frame_data["frame_idx"]
            category = frame_data.get("category", "general")
            emoji = CATEGORY_EMOJI.get(category, "🎮")

            with st.container(border=True):
                col_img, col_info = st.columns([1, 2])

                with col_img:
                    if idx < len(frames):
                        st.image(
                            frames[idx],
                            caption=f"Frame {idx}",
                            use_container_width=True,
                        )

                with col_info:
                    st.markdown(
                        f"**{emoji} {category.upper()}** — "
                        f"_{frame_data['reason']}_"
                    )
                    st.markdown(f"**Escena detectada:** {frame_data['caption']}")
                    st.markdown(f"### 🎙️ {frame_data['comment']}")

                    if frame_data.get("audio_path") is not None:
                        st.audio(frame_data["audio_path"])

            st.divider()

        st.balloons()

    except Exception as e:
        st.error(f"❌ Error durante el análisis: {e}")
