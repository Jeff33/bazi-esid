"""Canonical serialization, rounding and integrity helpers."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from . import constants as c


class InputError(ValueError):
    """Raised when an input cannot be normalized without guessing."""


def _duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(source: str | Path) -> Any:
    """Load JSON while rejecting duplicate keys and non-finite numbers."""

    text = Path(source).read_text(encoding="utf-8") if isinstance(source, Path) else source

    def reject_constant(value: str) -> None:
        raise InputError(f"non-finite JSON number is not allowed: {value}")

    try:
        return json.loads(
            text,
            object_pairs_hook=_duplicate_guard,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}") from exc


def _normalized_key(key: Any) -> str:
    if isinstance(key, frozenset):
        return "·".join(sorted(key))
    return unicodedata.normalize("NFC", str(key))


def normalize_json(value: Any) -> Any:
    """Return a JSON-safe NFC value with deterministic mapping/set order."""

    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InputError("non-finite number is not allowed")
        return float(Decimal(str(value)))
    if isinstance(value, Decimal):
        return float(value) if value != value.to_integral() else int(value)
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.strip())
    if isinstance(value, dict):
        return {
            _normalized_key(key): normalize_json(item)
            for key, item in sorted(value.items(), key=lambda pair: _normalized_key(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [normalize_json(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [normalize_json(item) for item in value]
        return sorted(normalized, key=lambda item: canonical_json(item))
    raise TypeError(f"cannot canonicalize {type(value).__name__}")


def canonical_json(value: Any, *, pretty: bool = False) -> str:
    normalized = normalize_json(value)
    if pretty:
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def round1(value: float) -> float | int:
    rounded = Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return int(rounded) if rounded == rounded.to_integral() else float(rounded)


def round2(value: float) -> float | int:
    rounded = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(rounded) if rounded == rounded.to_integral() else float(rounded)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def rule_pack() -> dict[str, Any]:
    """Return every frozen table that can change a numerical result."""

    return {
        "method_version": c.METHOD_VERSION,
        "engine_version": c.ENGINE_VERSION,
        "elements": c.ELEMENTS,
        "generates": c.GENERATES,
        "controls": c.CONTROLS,
        "stems": c.STEMS,
        "branches": c.BRANCHES,
        "source_weights": c.SOURCE_WEIGHTS,
        "stem_position_weights": c.STEM_POSITION_WEIGHTS,
        "branch_position_weights": c.BRANCH_POSITION_WEIGHTS,
        "season_coefficients": c.SEASON_COEFFICIENTS,
        "pillar_relation_modifier": c.PILLAR_RELATION_MODIFIER,
        "stem_combines": c.STEM_COMBINES,
        "stem_clashes": c.STEM_CLASHES,
        "branch_combines": c.BRANCH_COMBINES,
        "branch_clashes": c.BRANCH_CLASHES,
        "branch_harms": c.BRANCH_HARMS,
        "branch_breaks": c.BRANCH_BREAKS,
        "three_harmonies": c.THREE_HARMONIES,
        "three_meetings": c.THREE_MEETINGS,
        "three_punishments": c.THREE_PUNISHMENTS,
        "pair_punishments": c.PAIR_PUNISHMENTS,
        "self_punishments": c.SELF_PUNISHMENTS,
        "storage_branch": c.STORAGE_BRANCH,
        "ten_god_names": {f"{key[0]}:{key[1]}": value for key, value in c.TEN_GOD_NAMES.items()},
        "scoring": c.SCORING,
        "single_weights": c.SINGLE_WEIGHTS,
        "cfs_weights": c.CFS_WEIGHTS,
        "rafs_weights": c.RAFS_WEIGHTS,
        "afs_bands": c.AFS_BANDS,
        "activation_bands": c.ACTIVATION_BANDS,
        "notes": c.RULESET_NOTES,
    }


RULESET_SHA256 = sha256_json(rule_pack())


def evidence_id(kind: str, payload: Any) -> str:
    return f"{kind}-{sha256_json(payload)[:16]}"
