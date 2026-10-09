"""Localised evidence labels for display.

The detector writes evidence labels in English and they are part of the facts (ids, values, windows). Translation
happens only here, at the view layer, from the English label: values, windows and event ids are never touched, so
switching language cannot change a fact. Unknown labels are returned unchanged.
"""
from __future__ import annotations

import re

from .i18n import RULE_NAME

CH = {"tr": {"left": "Sol", "centre": "Merkez", "right": "Sağ"}, "es": {"left": "izquierdo", "centre": "central", "right": "derecho"}}
WHEN = {"tr": {"before": "önce", "after": "sonra"}, "es": {"before": "antes", "after": "después"}}
METRIC = {
    "shots": ("Şut", "Tiros"),
    "box entries": ("Ceza sahası girişi", "Llegadas al área"),
    "final-third entries": ("Son üçte bir girişi", "Entradas al último tercio"),
    "high pressures": ("Önde baskı", "Presión alta"),
    "recoveries": ("Top kazanma", "Recuperaciones"),
    "dangerous sequences": ("Tehlikeli atak", "Secuencias peligrosas"),
    "pass share": ("Pas payı", "Cuota de pases"),
    "progressive actions": ("İleri aksiyonlar", "Acciones progresivas"),
}
FIXED = {
    "Build-up sequence": ("Hücum organizasyonu", "Secuencia de construcción"),
    "Key events in the window": ("Penceredeki kilit olaylar", "Eventos clave de la ventana"),
    "Mean momentum (team-positive) previous 5' -> last 5'": ("Ortalama momentum (takım lehine): önceki 5' → son 5'",
                                                             "Inercia media (a favor del equipo): 5' previos → últimos 5'"),
}
_TYPE_BY_SPACED = {k.replace("_", " "): k for k in RULE_NAME["en"]}


def _i(locale: str) -> int:
    return 0 if locale == "tr" else 1


def _metric(name: str, locale: str) -> str | None:
    pair = METRIC.get(name.lower())
    return pair[_i(locale)] if pair else None


def localise_label(label: str, locale: str) -> str:
    if locale not in ("tr", "es") or not label:
        return label
    tr = locale == "tr"
    if label in FIXED:
        return FIXED[label][_i(locale)]
    if m := re.fullmatch(r"(Left|Centre|Right)-channel share of progressive actions (before|after)", label):
        ch, w = CH[locale][m[1].lower()], WHEN[locale][m[2]]
        return f"{ch} kanal: ileri aksiyon payı ({w})" if tr else f"Carril {ch}: cuota de acciones progresivas ({w})"
    if m := re.fullmatch(r"(Left|Centre|Right)-channel progressive actions after the change", label):
        ch = CH[locale][m[1].lower()]
        return f"{ch} kanal: değişiklik sonrası ileri aksiyonlar" if tr else f"Carril {ch}: acciones progresivas tras el cambio"
    if m := re.fullmatch(r"(Left|Centre|Right)-channel progressive actions (before|after)", label):
        ch, w = CH[locale][m[1].lower()], WHEN[locale][m[2]]
        return f"{ch} kanal: ileri aksiyonlar ({w})" if tr else f"Carril {ch}: acciones progresivas ({w})"
    if m := re.fullmatch(r"Most involved in the (left|centre|right) channel: (.+)", label):
        ch = CH[locale][m[1]]
        return f"{ch} kanalda en etkili oyuncu: {m[2]}" if tr else f"Más participativo en el carril {ch}: {m[2]}"
    if m := re.fullmatch(r"Before (\S+) vs after (\S+?)( \(after window still open\))?", label):
        tail = (" (sonrası penceresi hâlâ açık)" if tr else " (la ventana posterior sigue abierta)") if m[3] else ""
        return (f"Önce {m[1]} · sonra {m[2]}" if tr else f"Antes {m[1]} · después {m[2]}") + tail
    if m := re.fullmatch(r"Substitution (\S+): (.+) on for (.+)", label):
        return f"Oyuncu değişikliği {m[1]}: {m[2]} girdi, {m[3]} çıktı" if tr else f"Cambio {m[1]}: entra {m[2]}, sale {m[3]}"
    if m := re.fullmatch(r"Goal by (.+) at (\S+)", label):
        return f"Gol: {m[1]}, {m[2]}" if tr else f"Gol de {m[1]}, {m[2]}"
    if m := re.fullmatch(r"Red card: (.+)", label):
        return f"Kırmızı kart: {m[1]}" if tr else f"Tarjeta roja: {m[1]}"
    if m := re.fullmatch(r"Also triggered: (.+) at (\S+)", label):
        name = RULE_NAME[locale].get(_TYPE_BY_SPACED.get(m[1], ""), m[1])
        return f"Ayrıca tetiklendi: {name}, {m[2]}" if tr else f"También detectado: {name}, {m[2]}"
    if m := re.fullmatch(r"(.+) high pressures before/after", label):
        return f"{m[1]}: önde baskı (önce/sonra)" if tr else f"{m[1]}: presión alta (antes/después)"
    if m := re.fullmatch(r"(?:(.+) )?(pass share|final-third entries|Pass share|Final-third entries|Shots|Box entries|High pressures"
                         r"|Recoveries|Dangerous sequences|Progressive actions) (before|after)", label):
        name, w = _metric(m[2], locale), WHEN[locale][m[3]]
        if name:
            return f"{m[1]}: {name} ({w})" if m[1] else f"{name} ({w})"
    return label
