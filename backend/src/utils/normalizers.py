"""Normalization helpers for extracted entities.

Provides robust date normalization (ISO YYYY-MM-DD) using dateparser when available
with a dateutil fallback. Also includes simple heuristics to avoid normalizing obvious
non-date tokens.
"""
from typing import Optional

from backend.src.ml.ner.base_ner import Entity

try:
    from dateparser import parse as _parse_date
    _PARSER = "dateparser"
except Exception:
    try:
        from dateutil.parser import parse as _parse_date  # type: ignore
        _PARSER = "dateutil"
    except Exception:
        _parse_date = None  # type: ignore
        _PARSER = None

# Spanish month hints to quickly detect likely date strings
_MONTH_HINTS = {
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
}


def _looks_like_date(s: str) -> bool:
    """Heuristic to decide if a string likely contains a date.

    Returns True for strings containing month names or digit-heavy patterns
    like 2023, 12/03/2020, or 2023-03-12.
    """
    if not s:
        return False
    t = s.lower()
    # month name present
    if any(m in t for m in _MONTH_HINTS):
        return True
    # numeric patterns: long digit sequences or common separators
    digits = [c for c in t if c.isdigit()]
    if len(digits) >= 3 and ("/" in t or "-" in t):
        return True
    if len(digits) >= 4:  # e.g., year like 2023
        return True
    return False


def normalize_date(text: str) -> Optional[str]:
    """Normalize a free-text date to ISO YYYY-MM-DD.

    Returns None if parsing fails or no parser is available.
    """
    if not text or not _parse_date:
        return None
    try:
        if _PARSER == "dateparser":
            dt = _parse_date(text, languages=["es", "en"])  # prefer Spanish
        else:
            # dateutil fallback; use fuzzy parsing to tolerate surrounding words
            dt = _parse_date(text, fuzzy=True)
        if not dt:
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def should_normalize_entity(ent: Entity, min_confidence: float = 0.0) -> bool:
    """Decide whether to attempt normalization for an entity dict.

    ent is expected to contain 'label', 'text', and optionally 'confidence'.
    """
    if ent.label != "DATE":
        return False
    text = ent.text.strip()
    if not _looks_like_date(text):
        return False
    conf = ent.confidence
    if conf is None:
        return True
    try:
        return float(conf) >= float(min_confidence)
    except Exception:
        return True
