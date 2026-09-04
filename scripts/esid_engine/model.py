"""Input schema and immutable domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import InputError, normalize_json
from .constants import BRANCHES, SCHEMA_VERSION, STEMS


POSITIONS = ("year", "month", "day", "hour")
SEX_ALIASES = {
    "男": "male",
    "male": "male",
    "m": "male",
    "女": "female",
    "female": "female",
    "f": "female",
    "未指定": "unspecified",
    "unspecified": "unspecified",
    "unknown": "unspecified",
}


def _only(mapping: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise InputError(f"unknown field(s) in {where}: {', '.join(unknown)}")


@dataclass(frozen=True)
class Pillar:
    text: str
    stem: str
    branch: str

    @classmethod
    def parse(cls, value: Any, field: str) -> "Pillar":
        if not isinstance(value, str):
            raise InputError(f"{field} must be a two-character pillar")
        text = value.strip()
        if len(text) != 2 or text[0] not in STEMS or text[1] not in BRANCHES:
            raise InputError(f"{field} is not a valid stem-branch pillar: {value!r}")
        stem_index = STEMS[text[0]]["index"]
        branch_index = BRANCHES[text[1]]["index"]
        if (stem_index - branch_index) % 2:
            raise InputError(f"{field} is not one of the 60 valid sexagenary pillars: {text}")
        return cls(text=text, stem=text[0], branch=text[1])


@dataclass(frozen=True)
class Chart:
    id: str
    sex: str
    pillars: dict[str, Pillar | None]

    @property
    def day_master(self) -> str:
        day = self.pillars["day"]
        assert day is not None
        return day.stem

    @property
    def month_branch(self) -> str:
        month = self.pillars["month"]
        assert month is not None
        return month.branch

    @property
    def complete(self) -> bool:
        return all(self.pillars[position] is not None for position in POSITIONS)


@dataclass(frozen=True)
class Request:
    record_id: str
    mode: str
    charts: tuple[Chart, ...]
    luck: dict[str, Pillar]
    year: Pillar | None
    normalized_input: dict[str, Any]

    @property
    def effective_mode(self) -> str:
        prefix = "SINGLE" if self.mode == "single" else "COMPAT"
        if self.year is not None:
            return f"{prefix}-Y"
        if self.luck:
            return f"{prefix}-D"
        return f"{prefix}-R"

    @property
    def layers(self) -> tuple[str, ...]:
        result = ["R"]
        if self.luck:
            result.append("D")
        if self.year is not None:
            result.append("Y")
        return tuple(result)


def _parse_chart(value: Any, index: int) -> Chart:
    where = f"charts[{index}]"
    if not isinstance(value, dict):
        raise InputError(f"{where} must be an object")
    _only(value, {"id", "sex", "pillars"}, where)
    chart_id = value.get("id")
    if not isinstance(chart_id, str) or not chart_id.strip():
        raise InputError(f"{where}.id must be a non-empty string")
    chart_id = chart_id.strip()
    sex_raw = value.get("sex", "unspecified")
    if not isinstance(sex_raw, str):
        raise InputError(f"{where}.sex must be male, female, 男, 女, or unspecified")
    sex_key = sex_raw.strip()
    sex = SEX_ALIASES.get(sex_key, SEX_ALIASES.get(sex_key.lower()))
    if sex is None:
        raise InputError(f"{where}.sex must be male, female, 男, 女, or unspecified")
    pillars_raw = value.get("pillars")
    if not isinstance(pillars_raw, dict):
        raise InputError(f"{where}.pillars must be an object")
    _only(pillars_raw, set(POSITIONS), f"{where}.pillars")
    missing = [name for name in ("year", "month", "day") if name not in pillars_raw]
    if missing:
        raise InputError(f"missing required pillar(s) in {where}: {', '.join(missing)}")
    parsed: dict[str, Pillar | None] = {}
    for position in POSITIONS:
        raw = pillars_raw.get(position)
        if raw is None:
            if position != "hour":
                raise InputError(f"{where}.pillars.{position} cannot be null")
            parsed[position] = None
        else:
            parsed[position] = Pillar.parse(raw, f"{where}.pillars.{position}")
    return Chart(id=chart_id, sex=sex, pillars=parsed)


def parse_request(payload: Any) -> Request:
    if not isinstance(payload, dict):
        raise InputError("input must be a JSON object")
    _only(payload, {"schema", "record_id", "mode", "charts", "timing"}, "input")
    if payload.get("schema") != SCHEMA_VERSION:
        raise InputError(f"schema must equal {SCHEMA_VERSION!r}")
    record_id = payload.get("record_id")
    if not isinstance(record_id, str) or not record_id.strip():
        raise InputError("record_id must be a non-empty string")
    mode = payload.get("mode")
    if mode not in {"single", "compatibility"}:
        raise InputError("mode must be 'single' or 'compatibility'")
    charts_raw = payload.get("charts")
    if not isinstance(charts_raw, list):
        raise InputError("charts must be an array")
    expected = 1 if mode == "single" else 2
    if len(charts_raw) != expected:
        raise InputError(f"{mode} mode requires exactly {expected} chart(s)")
    charts = tuple(_parse_chart(item, index) for index, item in enumerate(charts_raw))
    ids = [chart.id for chart in charts]
    if len(set(ids)) != len(ids):
        raise InputError("chart ids must be unique")
    if mode == "compatibility" and set(ids) != {"A", "B"}:
        raise InputError("compatibility chart ids must be exactly A and B")
    if mode == "single" and ids != ["A"]:
        raise InputError("single chart id must be A")

    timing = payload.get("timing", {})
    if not isinstance(timing, dict):
        raise InputError("timing must be an object")
    _only(timing, {"luck", "year"}, "timing")
    luck_raw = timing.get("luck", {})
    if not isinstance(luck_raw, dict):
        raise InputError("timing.luck must be an object keyed by chart id")
    unknown_luck = sorted(set(luck_raw) - set(ids))
    if unknown_luck:
        raise InputError(f"luck supplied for unknown chart id(s): {', '.join(unknown_luck)}")
    luck = {key: Pillar.parse(value, f"timing.luck.{key}") for key, value in luck_raw.items()}
    if luck and set(luck) != set(ids):
        raise InputError("a dynamic layer requires a luck pillar for every chart")
    year_raw = timing.get("year")
    year = Pillar.parse(year_raw, "timing.year") if year_raw is not None else None
    if year is not None and not luck:
        raise InputError("an annual layer requires the complete luck layer")

    normalized = {
        "schema": SCHEMA_VERSION,
        "record_id": record_id.strip(),
        "mode": mode,
        "charts": [
            {
                "id": chart.id,
                "sex": chart.sex,
                "pillars": {
                    position: chart.pillars[position].text if chart.pillars[position] else None
                    for position in POSITIONS
                },
            }
            for chart in charts
        ],
        "timing": {
            "luck": {key: luck[key].text for key in sorted(luck)},
            "year": year.text if year else None,
        },
    }
    return Request(
        record_id=record_id.strip(),
        mode=mode,
        charts=charts,
        luck=luck,
        year=year,
        normalized_input=normalize_json(normalized),
    )
