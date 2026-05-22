"""Narrador inteligente de Valorant con sistema de plantillas por categoría."""

import random
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Palabras clave para clasificar la escena
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "eliminacion": [
        "eliminado", "eliminación", "muerte", "muerto", "caído", "baja",
        "kill", "dead", "down", "headshot",
    ],
    "combate": [
        "arma", "rifle", "pistola", "disparo", "apuntando", "disparando",
        "mira", "francotirador", "escopeta", "cuchillo", "gun", "shooting",
        "aiming", "weapon", "crosshair", "scope", "bala",
    ],
    "habilidad": [
        "humo", "fuego", "destello", "flash", "granada", "habilidad",
        "utilidad", "smoke", "fire", "ability", "verde", "naranja",
        "esfera", "poder", "objeto", "explosión", "bomba", "spike",
        "definitiva", "plantando", "desactivando",
    ],
    "movimiento": [
        "corriendo", "moviéndose", "saltando", "agachado", "caminando",
        "posición", "escondido", "running", "jumping", "crouching",
        "walking", "esquina", "pasillo", "rotación",
    ],
}

# ---------------------------------------------------------------------------
# Plantillas de comentarios — español auténtico de esports
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, list[str]] = {
    "eliminacion": [
        "¡ELIMINACIÓN! ¡Lo baja sin piedad con un disparo certero!",
        "¡CAE EL RIVAL! ¡Tremendo tiro que deja al enemigo fuera de la ronda!",
        "¡BAJA CONFIRMADA! ¡Qué puntería, esto es de otro nivel!",
        "¡LO LIQUIDA! ¡El rival no tuvo ni tiempo de reaccionar!",
        "¡HEADSHOT BRUTAL! ¡Se lo lleva con un tiro limpio a la cabeza!",
        "¡Eliminación clave! ¡Eso abre la ronda para el equipo!",
        "¡QUÉ BAJA! ¡El rival cae fulminado y la ventaja numérica es enorme!",
        "¡Disparo letal! ¡No hay defensa posible contra esa precisión!",
        "¡Lo despacha con estilo! ¡El público estalla con esa eliminación!",
        "¡FUERA! ¡Un tiro, una baja, así de simple y así de letal!",
    ],
    "combate": [
        "¡CONTACTO! ¡Se encuentra al enemigo y empieza el tiroteo!",
        "¡Ahí está el duelo! ¡Levanta el {arma} y busca el headshot!",
        "¡Se desata el combate! ¡Apunta con todo y el trigger finger no falla!",
        "¡Pelea directa! ¡No hay tiempo para pensar, es matar o morir!",
        "¡Toma posición y apunta! ¡Este duelo puede definir la ronda!",
        "¡Tiene el {arma} lista! ¡Un click puede cambiar todo el round!",
        "¡Se enfrenta cara a cara! ¡Qué valentía en este duelo a muerte!",
        "¡Desenfunda y a por todas! ¡No hay piedad en esta ronda!",
        "¡Crosshair en posición! ¡Está listo para el disparo certero!",
        "¡Combate cerrado! ¡Solo uno va a quedar en pie después de esto!",
        "¡Ahí viene la pelea! ¡El {arma} apunta directo al ángulo enemigo!",
        "¡Se activa el tiroteo! ¡Las balas vuelan y la tensión es máxima!",
        "¡Duelo a muerte! ¡Los reflejos van a decidir quién sobrevive!",
        "¡Intercambio de disparos! ¡Esto está al rojo vivo!",
        "¡Apunta y dispara! ¡La mecánica individual brilla en este momento!",
    ],
    "habilidad": [
        "¡Utilidad al campo! ¡Despliega la habilidad para controlar la zona!",
        "¡Ahí va la utilidad! ¡Corta la visión y cambia toda la jugada!",
        "¡Habilidad activada! ¡El control del mapa es fundamental!",
        "¡Despliega poder! ¡La utilidad marca la diferencia en esta ronda!",
        "¡Ejecuta la estrategia! ¡La habilidad cae justo donde la necesitaba!",
        "¡Activa la utilidad! ¡Con esto busca la ventaja táctica completa!",
        "¡Tremenda utilidad! ¡Eso corta toda la rotación del equipo enemigo!",
        "¡Uso perfecto de la habilidad! ¡El timing es impecable!",
        "¡Lanza la utilidad! ¡La zona queda completamente controlada!",
        "¡Habilidad decisiva! ¡Eso puede definir toda la ronda!",
        "¡Utilidad maestra! ¡El equipo ejecuta la estrategia a la perfección!",
        "¡Despliega y avanza! ¡La habilidad abre camino hacia el site!",
    ],
    "movimiento": [
        "¡Se reposiciona! ¡Busca el ángulo perfecto para el siguiente duelo!",
        "¡Rotación inteligente! ¡Cambia de posición buscando la ventaja!",
        "¡Se mueve con cuidado! ¡Cada paso puede ser el último en esta ronda!",
        "¡Reposición táctica! ¡Sabe exactamente dónde tiene que estar!",
        "¡Avanza con determinación! ¡No hay marcha atrás, va a por todo!",
        "¡Toma el control de la zona! ¡Se posiciona para la jugada definitiva!",
        "¡Movimiento silencioso! ¡El enemigo no sabe que lo están flanqueando!",
        "¡Rotación al otro site! ¡Cambia el plan sobre la marcha!",
        "¡Se desliza por el mapa! ¡Lectura perfecta de la situación!",
        "¡Posición agresiva! ¡Presiona al rival sin darle respiro!",
    ],
    "general": [
        "¡Momento de tensión! ¡La ronda está que arde y todo puede pasar!",
        "¡Qué situación! ¡El siguiente movimiento es crucial para la ronda!",
        "¡Atención! ¡Esto se pone cada vez más intenso en la partida!",
        "¡La presión sube! ¡Cada segundo cuenta y los nervios se sienten!",
        "¡Increíble lo que estamos viendo! ¡Este juego no decepciona!",
        "¡Vamos con todo! ¡La acción no para ni un segundo en esta ronda!",
        "¡Se siente la tensión en el ambiente! ¡El clutch es posible!",
        "¡Partido electrizante! ¡No se pueden perder ni un momento de esto!",
        "¡Qué nivel de juego! ¡Esto es Valorant de alto calibre!",
        "¡La ronda se calienta! ¡Ambos equipos lo están dando todo!",
        "¡Concentración máxima! ¡Un error aquí puede costar toda la ronda!",
        "¡Acción pura! ¡Estamos viendo una partida para recordar!",
    ],
}

# Mapeo de armas detectables en la descripción
_WEAPON_KEYWORDS: dict[str, str] = {
    "rifle": "rifle",
    "pistola": "pistola",
    "francotirador": "francotirador",
    "escopeta": "escopeta",
    "cuchillo": "cuchillo",
    "arma": "arma",
    "vandal": "Vandal",
    "phantom": "Phantom",
    "operator": "Operator",
    "sheriff": "Sheriff",
    "spectre": "Spectre",
    "judge": "Judge",
    "marshal": "Marshal",
    "guardian": "Guardian",
    "ghost": "Ghost",
    "classic": "Classic",
    "frenzy": "Frenzy",
    "stinger": "Stinger",
    "bucky": "Bucky",
    "bulldog": "Bulldog",
    "odin": "Odin",
    "ares": "Ares",
}

# Emojis por categoría (para la UI)
CATEGORY_EMOJI: dict[str, str] = {
    "eliminacion": "💀",
    "combate": "⚔️",
    "habilidad": "✨",
    "movimiento": "🏃",
    "general": "🎮",
}


class NarratorModel:
    """Narrador inteligente de Valorant basado en plantillas contextuales."""

    def __init__(self):
        """Inicializa el narrador sin modelos de ML — solo lógica de plantillas."""
        self._used_recently: list[str] = []
        self._max_memory = 6  # Recordar últimas N plantillas para evitar repetir

    def _classify_scene(self, caption: str) -> str:
        """Clasifica la escena en una categoría basándose en palabras clave."""
        lower = caption.lower()

        # Contar coincidencias por categoría
        scores: dict[str, int] = {}
        for category, keywords in _CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                scores[category] = score

        if not scores:
            return "general"

        # Devolver la categoría con más coincidencias
        return max(scores, key=scores.get)

    def _extract_weapon(self, caption: str) -> str:
        """Extrae el nombre del arma de la descripción, o devuelve genérico."""
        lower = caption.lower()
        for keyword, name in _WEAPON_KEYWORDS.items():
            if keyword in lower:
                return name
        return "arma"

    def _pick_template(self, category: str) -> str:
        """Elige una plantilla no usada recientemente de la categoría."""
        templates = _TEMPLATES[category]
        available = [t for t in templates if t not in self._used_recently]

        if not available:
            # Si todas fueron usadas recientemente, resetear y usar cualquiera
            self._used_recently.clear()
            available = templates

        chosen = random.choice(available)
        self._used_recently.append(chosen)

        # Mantener solo las últimas N en memoria
        if len(self._used_recently) > self._max_memory:
            self._used_recently = self._used_recently[-self._max_memory :]

        return chosen

    def generate_comment(self, caption: str) -> tuple[str, str]:
        """Genera un comentario y su categoría a partir de una descripción.

        Returns:
            Tupla (comentario, categoría).
        """
        category = self._classify_scene(caption)
        weapon = self._extract_weapon(caption)
        template = self._pick_template(category)

        # Insertar arma si la plantilla lo requiere
        comment = template.format(arma=weapon)

        return comment, category


def narrate_frames(
    filtered_frames: list[dict], model: NarratorModel
) -> list[dict]:
    """Agrega comentario narrado y categoría a cada frame filtrado."""
    narrated_frames: list[dict] = []

    for frame in filtered_frames:
        updated = dict(frame)
        try:
            comment, category = model.generate_comment(frame["caption"])
            updated["comment"] = comment
            updated["category"] = category
        except Exception:
            updated["comment"] = "¡Acción intensa en la partida!"
            updated["category"] = "general"
        narrated_frames.append(updated)

    return narrated_frames
