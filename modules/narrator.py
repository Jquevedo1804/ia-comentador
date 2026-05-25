"""Narrador inteligente para Minecraft Skywars con reglas robustas."""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Configuracion semantica para detectar escenas y contexto
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "inicio": [
        "spawn",
        "starting island",
        "island spawn",
        "jaula",
        "cage",
        "countdown",
        "start",
        "begin",
        "pre game",
        "lobby",
        "skywars begins",
    ],
    "loot": [
        "chest",
        "cofre",
        "loot",
        "inventory",
        "inventario",
        "item",
        "armor",
        "armadura",
        "helmet",
        "casco",
        "chestplate",
        "leggings",
        "boots",
        "sword",
        "espada",
        "pickaxe",
        "potion",
        "flechas",
        "enchanted",
        "diamond",
        "iron",
        "gold",
    ],
    "puenteo": [
        "bridge",
        "bridging",
        "speed bridge",
        "ninja bridge",
        "placing blocks",
        "building over void",
        "crossing to island",
        "bloques",
        "puente",
        "island to island",
    ],
    "centro": [
        "mid",
        "center",
        "centro",
        "middle",
        "middle island",
        "control mid",
        "rotating to mid",
    ],
    "combate": [
        "fight",
        "fighting",
        "combat",
        "duel",
        "pvp",
        "attacking",
        "hits",
        "trading hits",
        "enemy",
        "rival",
        "crosshair",
        "aim",
        "critical hit",
        "knockback",
        "rod",
        "sword",
        "melee",
        "projectile",
        "snowball",
        "snowballs",
        "egg",
        "eggs",
        "throwing",
        "duelo melee",
        "intercambio corto",
        "presion con snowballs",
        "presion con huevos",
    ],
    "eliminacion": [
        "killed",
        "kill",
        "eliminated",
        "slain",
        "dead",
        "death",
        "final kill",
        "void kill",
        "wins the fight",
    ],
    "peligro_vacio": [
        "void",
        "falling",
        "fell",
        "fall off",
        "edge",
        "borde",
        "knocked",
        "clutch",
        "pearled",
        "mlg water",
        "riesgo al borde del vacio",
        "knockback cerca del borde",
        "caida al vacio",
    ],
    "cierre": [
        "endgame",
        "late game",
        "deathmatch",
        "final phase",
        "border closing",
        "last players",
        "top 4",
        "top 3",
        "top 2",
        "1v1",
        "duelo final 1v1",
    ],
    "victoria": [
        "victory",
        "winner",
        "won",
        "you win",
        "win screen",
        "game over winner",
        "champion",
    ],
}

_CATEGORY_WEIGHTS: dict[str, int] = {
    "inicio": 2,
    "loot": 2,
    "puenteo": 3,
    "centro": 2,
    "combate": 3,
    "eliminacion": 5,
    "peligro_vacio": 4,
    "cierre": 3,
    "victoria": 6,
}

_INVALID_CAPTION_SIGNALS = {
    "",
    "none",
    "null",
    "n/a",
    "error al procesar frame",
    "error processing frame",
    "unable to generate caption",
}

_ITEM_KEYWORDS: dict[str, str] = {
    "diamond sword": "espada de diamante",
    "iron sword": "espada de hierro",
    "stone sword": "espada de piedra",
    "gold sword": "espada de oro",
    "netherite sword": "espada de netherite",
    "sword": "espada",
    "rod": "cana",
    "axe": "hacha",
    "pickaxe": "pico",
    "ender pearl": "ender pearl",
    "pearl": "ender pearl",
    "snowball": "snowballs",
    "egg": "huevos",
    "golden apple": "manzana dorada",
    "gapple": "manzana dorada",
    "apple": "manzana",
    "potion": "pocion",
    "lava bucket": "cubo de lava",
    "water bucket": "cubo de agua",
    "tnt": "tnt",
    "diamond armor": "armadura de diamante",
    "iron armor": "armadura de hierro",
    "chain armor": "armadura de cota",
    "armor": "armadura",
}

_PROJECTILE_ITEMS = {"snowballs", "huevos"}

_CONTEXT_KEYWORDS: dict[str, list[str]] = {
    "mid": ["mid", "center", "centro", "middle island", "middle"],
    "bridge": ["bridge", "bridging", "placing blocks", "speed bridge", "ninja bridge"],
    "void": ["void", "falling", "fell", "edge", "knocked", "clutch", "mlg water"],
    "height": ["high ground", "tower", "top", "elevated", "above", "altura"],
    "pressure": ["rush", "pushing", "chasing", "sprinting", "aggressive"],
    "defense": ["hiding", "cover", "wall", "holding angle", "camping", "sneak"],
    "low_health": ["low health", "one heart", "half heart", "critical health", "hearts low"],
}

_PLAYERS_HINTS: dict[str, list[str]] = {
    "top2": ["top 2", "two players left", "2 players left", "1v1", "last two"],
    "top3": ["top 3", "three players left", "3 players left", "last three"],
    "top4": ["top 4", "four players left", "4 players left", "last four"],
}

_TEMPLATES: dict[str, list[str]] = {
    "inicio": [
        "Arranca Skywars y ya esta trazando su plan inicial.",
        "Inicio de ronda: primeros segundos clave para marcar el ritmo.",
        "Se abre la partida y cada decision temprana pesa muchisimo.",
        "Comienzo limpio, toca decidir entre loot rapido o rush directo.",
    ],
    "loot": [
        "Loot bien administrado, no regala timing en la salida.",
        "Gestion de inventario solida para preparar el siguiente choque.",
        "Buena lectura de cofres, sale mejor equipado para pelear.",
        "Se equipa con {item} y sube su amenaza de inmediato.",
        "Recupera recursos clave y optimiza su ventana de combate.",
        "Microgestion excelente del inventario, esta preparando la siguiente ventana de agresion.",
        "Loot rapido y ordenado: cada segundo ganado aqui se paga en combate.",
        "Ajuste fino de recursos, esta construyendo ventaja antes del trade directo.",
    ],
    "puenteo": [
        "Puenteando bajo tension, este cruce define el siguiente duelo.",
        "Construye paso entre islas con riesgo total al vacio.",
        "Cruce agresivo: quiere iniciativa antes que el rival.",
        "Speed bridge en marcha, precision absoluta en cada bloque.",
    ],
    "centro": [
        "Toma espacio en mid y eso cambia el control de recursos.",
        "Ya pisa centro: posicion clave para dominar la partida.",
        "Rotacion al medio bien medida, busca ventaja de mapa.",
        "Mid controlado, ahora puede castigar a quien rote tarde.",
    ],
    "combate": [
        "Duelo abierto en Skywars, mecanica al limite.",
        "Intercambio fuerte de golpes, este trade puede romper el mapa.",
        "PVP intenso, timing y knockback lo son todo aqui.",
        "Pelea cerrada: cualquier microerror cuesta la vida.",
        "Presiona con {item} y obliga respuesta inmediata.",
        "Entrada agresiva al intercambio, quiere cerrar la pelea en esta rotacion.",
        "Combate de alto ritmo: lectura de rango, click timing y posicion milimetrica.",
        "Trade muy tecnico, ambos jugadores buscan el primer error del rival.",
        "Duelo al limite, cada hit cambia por completo la ventaja del enfrentamiento.",
        "Pelea muy viva en pantalla, esto se decide por mecanica pura.",
    ],
    "eliminacion": [
        "Eliminacion confirmada, ventaja enorme en el cierre.",
        "Baja importante: limpia espacio y gana control del mapa.",
        "Convierte la presion en kill, jugada muy eficiente.",
        "Cae un rival y cambia por completo la lectura del round.",
    ],
    "peligro_vacio": [
        "Momento critico al borde del vacio, no hay margen de error.",
        "Situacion de alto riesgo: un toque define todo.",
        "Se juega la partida en el filo del mapa.",
        "Knockback peligroso, sobrevivir aqui ya es ganancia.",
    ],
    "cierre": [
        "Entramos al endgame y cada decision vale oro.",
        "Cierre encendido: posicion y paciencia mandan.",
        "Tramo final, los microdetalles ahora deciden ganador.",
        "Late game total, la presion esta al maximo.",
    ],
    "victoria": [
        "Victoria asegurada con una ejecucion muy limpia.",
        "Se lleva el Skywars con autoridad.",
        "Win confirmado: buena lectura, buena mecanica y control mental.",
        "Cierra la partida de forma contundente.",
    ],
    "general": [
        "Skywars muy tenso, cualquier jugada puede cambiar todo.",
        "La partida sigue abierta y el siguiente movimiento es clave.",
        "Ritmo alto en el mapa, no hay espacio para errores.",
        "Momento de maxima concentracion en esta ronda.",
    ],
    "fallback_error": [
        "Escena confusa, pero la partida sigue intensa y abierta.",
        "No se ve claro el detalle, mantenemos foco en el ritmo del juego.",
        "Frame ambiguo, seguimos leyendo la siguiente accion clave.",
    ],
}

CATEGORY_EMOJI: dict[str, str] = {
    "inicio": "🚀",
    "loot": "📦",
    "puenteo": "🧱",
    "centro": "🎯",
    "combate": "⚔️",
    "eliminacion": "💀",
    "peligro_vacio": "🌌",
    "cierre": "🔥",
    "victoria": "🏆",
    "general": "🎮",
}

_PRIORITY_CATEGORIES = ["victoria", "eliminacion", "peligro_vacio"]
_MAX_COMMENT_WORDS = 30


@dataclass
class SceneContext:
    item: str = "su equipo"
    is_ranged: bool = False
    in_mid: bool = False
    bridging: bool = False
    void_risk: bool = False
    has_height: bool = False
    is_pressuring: bool = False
    is_defensive: bool = False
    low_health: bool = False
    players_hint: str = ""
    is_caption_invalid: bool = False


class NarratorModel:
    """Narrador de Skywars basado en plantillas con heuristicas robustas."""

    def __init__(self):
        self._used_recently: list[str] = []
        self._max_memory = 10
        self._last_category = "general"
        self._last_comment = ""
        self._category_streak = 0

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()

    def _contains(self, text: str, keyword: str) -> bool:
        if " " in keyword:
            return keyword in text
        return bool(re.search(rf"\b{re.escape(keyword)}\b", text))

    def _is_invalid_caption(self, caption: str) -> bool:
        lower = self._normalize(caption)
        if lower in _INVALID_CAPTION_SIGNALS:
            return True
        return lower.startswith("error ") or "traceback" in lower

    def _extract_item(self, caption: str) -> str:
        lower = self._normalize(caption)
        has_stable_action_read = "lectura en espanol" in lower
        if not has_stable_action_read:
            return "su equipo"

        if "curacion con manzana dorada" in lower or "eating golden apple" in lower:
            return "manzana dorada"
        if "curacion con pocion" in lower or "drinking healing potion" in lower:
            return "pocion"
        if "presion con snowballs" in lower or "throwing snowballs" in lower:
            return "snowballs"
        if "presion con huevos" in lower or "throwing eggs" in lower:
            return "huevos"
        return "su equipo"

    def _extract_players_hint(self, lower: str) -> str:
        if any(self._contains(lower, token) for token in _PLAYERS_HINTS["top2"]):
            return "Quedan muy pocos jugadores, cualquier trade define todo."
        if any(self._contains(lower, token) for token in _PLAYERS_HINTS["top3"]):
            return "Estamos en top 3, cada rotacion tiene impacto directo."
        if any(self._contains(lower, token) for token in _PLAYERS_HINTS["top4"]):
            return "Entrando al tramo final, posicion y recursos son vitales."
        return ""

    def _extract_context(self, caption: str) -> SceneContext:
        lower = self._normalize(caption)
        item = self._extract_item(caption)
        return SceneContext(
            item=item,
            is_ranged=item in _PROJECTILE_ITEMS,
            in_mid=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["mid"]),
            bridging=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["bridge"]),
            void_risk=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["void"]),
            has_height=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["height"]),
            is_pressuring=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["pressure"]),
            is_defensive=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["defense"]),
            low_health=any(self._contains(lower, k) for k in _CONTEXT_KEYWORDS["low_health"]),
            players_hint=self._extract_players_hint(lower),
            is_caption_invalid=self._is_invalid_caption(caption),
        )

    def _score_categories(self, caption: str, context: SceneContext) -> dict[str, int]:
        lower = self._normalize(caption)
        scores: dict[str, int] = {}

        for category, keywords in _CATEGORY_KEYWORDS.items():
            hits = sum(1 for kw in keywords if self._contains(lower, kw))
            if hits:
                scores[category] = hits * _CATEGORY_WEIGHTS[category]

        if context.in_mid:
            scores["centro"] = scores.get("centro", 0) + 2
        if context.bridging:
            scores["puenteo"] = scores.get("puenteo", 0) + 3
        if context.void_risk:
            scores["peligro_vacio"] = scores.get("peligro_vacio", 0) + 3
        if context.low_health:
            scores["peligro_vacio"] = scores.get("peligro_vacio", 0) + 1
        if context.is_pressuring and context.item != "su equipo":
            scores["combate"] = scores.get("combate", 0) + 2
        if context.is_defensive and context.in_mid:
            scores["centro"] = scores.get("centro", 0) + 1
        if context.item != "su equipo":
            scores["loot"] = scores.get("loot", 0) + 1

        # Si hay victoria o kill explicita, forzar alta prioridad.
        for category in _PRIORITY_CATEGORIES:
            if any(self._contains(lower, kw) for kw in _CATEGORY_KEYWORDS[category]):
                scores[category] = scores.get(category, 0) + 20

        # Evitar que "loot" tape peleas reales.
        has_combat_signal = any(
            self._contains(lower, kw) for kw in _CATEGORY_KEYWORDS["combate"]
        )
        if has_combat_signal and context.item != "su equipo":
            scores["combate"] = scores.get("combate", 0) + 4

        # Si hay "last players" sin kill/victoria, reforzar cierre.
        if context.players_hint and "victoria" not in scores:
            scores["cierre"] = scores.get("cierre", 0) + 3

        return scores

    def _classify_scene(self, caption: str, context: SceneContext) -> str:
        if context.is_caption_invalid:
            return "general"

        scores = self._score_categories(caption, context)
        if not scores:
            return "general"

        sorted_candidates = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_category, best_score = sorted_candidates[0]

        # Estabilizador: si la diferencia es minima, conservar la categoria anterior.
        if len(sorted_candidates) > 1:
            second_score = sorted_candidates[1][1]
            if self._last_category in scores and (best_score - second_score) <= 2:
                if scores[self._last_category] >= second_score:
                    best_category = self._last_category

        return best_category

    def _pick_template(self, category: str, allow_item_template: bool = True) -> str:
        templates = _TEMPLATES.get(category, _TEMPLATES["general"])
        if not allow_item_template:
            templates = [template for template in templates if "{item}" not in template]
            if not templates:
                templates = _TEMPLATES.get(category, _TEMPLATES["general"])
        available = [template for template in templates if template not in self._used_recently]

        if not available:
            self._used_recently.clear()
            available = templates

        chosen = random.choice(available)
        self._used_recently.append(chosen)
        if len(self._used_recently) > self._max_memory:
            self._used_recently = self._used_recently[-self._max_memory :]
        return chosen

    def _build_detail_line(self, category: str, ctx: SceneContext) -> str:
        options: list[str] = []

        if category == "loot":
            if ctx.item != "su equipo":
                options.append(f"Item detectado: {ctx.item}.")
            if ctx.in_mid:
                options.append("Con esa ruta puede disputar centro de inmediato.")
            if ctx.low_health:
                options.append("Necesita estabilizar vida antes del siguiente choque.")
        elif category == "puenteo":
            if ctx.void_risk:
                options.append("Un paso mal en puente y se va al vacio.")
            if ctx.is_pressuring:
                options.append("Cruza con ritmo alto para tomar iniciativa.")
            if ctx.players_hint:
                options.append(ctx.players_hint)
        elif category == "centro":
            if ctx.has_height:
                options.append("La altura en mid le da ventaja de intercambio.")
            if ctx.is_defensive:
                options.append("Se cubre bien para no regalar dano gratuito.")
            if ctx.players_hint:
                options.append(ctx.players_hint)
        elif category == "combate":
            if ctx.item != "su equipo":
                if "manzana" in ctx.item:
                    options.append("Usa curacion en pleno trade para no perder el tempo del duelo.")
                elif "pocion" in ctx.item:
                    options.append("Activa recurso de curacion y busca reentrar con ventaja de vida.")
                elif "snowballs" in ctx.item or "huevos" in ctx.item:
                    options.append(f"Presiona con {ctx.item} para forzar knockback y abrir eliminacion.")
                    options.append(f"Usa {ctx.item} para cortar el avance rival.")
                elif not ctx.is_ranged:
                    options.append(f"Juega melee con {ctx.item} buscando knockback.")
            if ctx.void_risk:
                options.append("El borde del vacio vuelve esta pelea mucho mas peligrosa.")
            if ctx.low_health:
                options.append("Con vida baja, cualquier hit puede cerrar el duelo.")
            if ctx.has_height:
                options.append("La altura puede decidir este intercambio.")
        elif category == "eliminacion":
            if ctx.void_risk:
                options.append("La baja en zona de vacio abre totalmente el mapa.")
            if ctx.in_mid:
                options.append("Eliminar en centro da control y recursos al instante.")
            if ctx.players_hint:
                options.append(ctx.players_hint)
        elif category == "peligro_vacio":
            if ctx.bridging:
                options.append("La exposicion en puente sube muchisimo el riesgo.")
            if ctx.low_health:
                options.append("Llega tocado y necesita una jugada defensiva perfecta.")
            if ctx.players_hint:
                options.append(ctx.players_hint)
        elif category == "cierre":
            if ctx.has_height:
                options.append("La altura en endgame suele definir ganador.")
            if ctx.in_mid:
                options.append("Controlar centro en cierre vale media partida.")
            if ctx.players_hint:
                options.append(ctx.players_hint)
        elif category == "victoria":
            if ctx.item != "su equipo":
                options.append(f"Cierra con gran uso de {ctx.item}.")
            if ctx.players_hint:
                options.append("Lo consigue en el tramo mas tenso de la ronda.")
        elif category == "general":
            if ctx.players_hint:
                options.append(ctx.players_hint)
            if ctx.low_health:
                options.append("Escenario delicado por la vida baja.")

        return random.choice(options) if options else ""

    def _transition_line(self, category: str) -> str:
        if self._last_category == category:
            self._category_streak += 1
        else:
            self._category_streak = 1

        if self._last_category != category:
            if category == "combate" and self._last_category in {"loot", "puenteo", "centro"}:
                return " Se transforma posicion en pelea inmediata."
            if category == "eliminacion":
                return " Conversion limpia de presion a resultado."
            if category == "cierre":
                return " Entramos en fase decisiva del match."
            if category == "victoria":
                return " Cierre total de partida."

        if self._category_streak >= 3 and category in {"combate", "peligro_vacio"}:
            return " La tension se mantiene al maximo."
        return ""

    def _finalize_comment(self, base_comment: str, detail_line: str, transition: str) -> str:
        comment = base_comment
        if detail_line:
            comment = f"{comment} {detail_line}"
        if transition:
            comment = f"{comment}{transition}"
        if comment == self._last_comment:
            comment = f"{comment} Sigue siendo un punto critico."
        comment = self._compact_comment(comment)
        self._last_comment = comment
        return comment

    def _compact_comment(self, text: str) -> str:
        clean = re.sub(r"\s+", " ", text.strip())
        words = clean.split()
        if len(words) <= _MAX_COMMENT_WORDS:
            return clean
        trimmed = " ".join(words[:_MAX_COMMENT_WORDS]).rstrip(",;:")
        if not trimmed.endswith((".", "!", "?")):
            trimmed += "."
        return trimmed

    def generate_comment(self, caption: str) -> tuple[str, str]:
        context = self._extract_context(caption)
        if context.is_caption_invalid:
            template = self._pick_template("fallback_error")
            self._last_category = "general"
            return template, "general"

        category = self._classify_scene(caption, context)
        template = self._pick_template(category, allow_item_template=context.item != "su equipo")
        base_comment = template.format(item=context.item)
        detail_line = self._build_detail_line(category, context)
        transition = self._transition_line(category)
        comment = self._finalize_comment(base_comment, detail_line, transition)
        self._last_category = category
        return comment, category


def narrate_frames(filtered_frames: list[dict], model: NarratorModel) -> list[dict]:
    """Agrega comentario narrado y categoria a cada frame filtrado."""
    narrated_frames: list[dict] = []

    for frame in filtered_frames:
        updated = dict(frame)
        try:
            caption = str(frame.get("caption", ""))
            comment, category = model.generate_comment(caption)
            updated["comment"] = comment
            updated["category"] = category
        except Exception:
            updated["comment"] = "Partida intensa de Skywars en este momento."
            updated["category"] = "general"
        narrated_frames.append(updated)

    return narrated_frames
