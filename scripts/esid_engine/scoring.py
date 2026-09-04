"""Canonical deterministic scoring for a single chart."""

from __future__ import annotations

import math
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from .canonical import clamp, round1, round2
from .constants import (
    ACTIVATION_BANDS,
    AFS_BANDS,
    BRANCHES,
    CONTROLS,
    ELEMENTS,
    GENERATES,
    SCORING,
    SINGLE_WEIGHTS,
    STEMS,
)
from .facts import Node, element_role, layer_facts
from .model import Chart, Pillar, Request


def band(value: float, table: Iterable[tuple[int, str]]) -> str:
    for upper, label in table:
        if value < upper:
            return label
    raise AssertionError("band table must end above the score maximum")


def dss_band(value: float) -> str:
    if value < 0.65:
        return "极弱"
    if value < 0.80:
        return "明显偏弱"
    if value < 0.95:
        return "偏弱"
    if value < 1.10:
        return "中和"
    if value < 1.30:
        return "偏旺"
    return "旺"


def _branch_totals(nodes: list[Node]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for node in nodes:
        if node.kind == "hidden" and node.parent:
            totals[node.parent] += node.base_weight
    return dict(totals)


def calculate_energy(nodes: list[Node], interactions: list[dict[str, Any]]) -> dict[str, float]:
    energy = {element: 0.0 for element in ELEMENTS}
    visible_stems = {node.value for node in nodes if node.kind == "stem" and node.base_weight > 0}
    disruption: dict[str, float] = defaultdict(lambda: 1.0)
    attacked_luck_roots: set[str] = set()
    for event in interactions:
        factor = SCORING["disruption_energy"].get(event["type"])
        if factor is None:
            continue
        for member in event["members"]:
            if member.endswith(".branch"):
                disruption[member] *= 1.0 - factor * event["strength"]
                if (
                    "Y" in event["sources"]
                    and "D" in event["sources"]
                    and event["type"] in {"冲", "刑", "害", "破"}
                    and "_D.luck.branch" in member
                ):
                    attacked_luck_roots.add(member)

    for node in nodes:
        if node.kind not in {"stem", "hidden"}:
            continue
        modifier = 1.0
        if node.kind == "hidden" and node.value in visible_stems:
            modifier *= 1.10
        if node.kind == "hidden" and node.source in {"D", "Y"} and node.ten_god in {"比肩", "劫财", "正印", "偏印"}:
            modifier *= SCORING["dynamic_support_root_multiplier"]
        if node.parent:
            modifier *= max(0.45, disruption[node.parent])
            if node.parent in attacked_luck_roots and node.ten_god in {"比肩", "劫财", "正印", "偏印"}:
                modifier *= SCORING["annual_attack_on_luck_root"]
        energy[node.element] += node.base_weight * modifier

    branch_totals = _branch_totals(nodes)
    by_id = {node.id: node for node in nodes}
    for event in interactions:
        coefficient = SCORING["interaction_energy"].get(event["type"])
        target = event.get("result_element")
        if coefficient is None or target not in ELEMENTS:
            continue
        material = 0.0
        for member_id in event["members"]:
            node = by_id[member_id]
            material += branch_totals.get(member_id, node.base_weight)
        material /= max(1, len(event["members"]))
        energy[target] += material * coefficient * event["strength"]
    return {element: round(value, 10) for element, value in energy.items()}


def _role_elements(day_element: str) -> dict[str, str]:
    resource = next(element for element, produced in GENERATES.items() if produced == day_element)
    officer = next(element for element, controlled in CONTROLS.items() if controlled == day_element)
    return {
        "same": day_element,
        "resource": resource,
        "output": GENERATES[day_element],
        "wealth": CONTROLS[day_element],
        "officer": officer,
    }


def calculate_dss(day_element: str, energy: dict[str, float]) -> tuple[float, float]:
    roles = _role_elements(day_element)
    support = energy[roles["same"]] + energy[roles["resource"]]
    pressure = sum(
        energy[roles[role]] * SCORING["pressure_factors"][role]
        for role in ("output", "wealth", "officer")
    )
    ratio = (support + SCORING["daymaster_anchor"]) / (
        SCORING["pressure_floor"] + SCORING["pressure_scale"] * pressure
    )
    score = clamp(100.0 - SCORING["dss_log_penalty"] * abs(math.log(max(0.05, ratio))))
    return ratio, score


def _climate_adjustment(month: str) -> dict[str, float]:
    if month in {"亥", "子", "丑"}:
        return {"木": 0.30, "火": 0.80, "土": 0.15, "金": 0.00, "水": -0.40}
    if month in {"巳", "午", "未"}:
        return {"木": 0.00, "火": -0.40, "土": -0.10, "金": 0.20, "水": 0.80}
    if month in {"申", "酉", "戌"}:
        return {"木": 0.30, "火": 0.40, "土": -0.40, "金": -0.60, "水": 0.80}
    return {"木": -0.20, "火": 0.30, "土": 0.00, "金": 0.20, "水": 0.10}


def _half_step(value: float) -> float:
    doubled = Decimal(str(value * 2.0)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return float(doubled / Decimal("2"))


def calculate_dfp(
    chart: Chart,
    dss: float,
    energy: dict[str, float],
    nodes: list[Node],
    interactions: list[dict[str, Any]],
) -> dict[str, float]:
    day_element = STEMS[chart.day_master]["element"]
    if dss < 0.95:
        role_values = {"resource": 2.20, "same": 1.70, "output": -0.20, "wealth": -1.50, "officer": -2.30}
    elif dss < 1.10:
        role_values = {"resource": 0.40, "same": 0.20, "output": 1.30, "wealth": 1.50, "officer": 1.20}
    else:
        role_values = {"resource": -1.80, "same": -1.50, "output": 1.60, "wealth": 2.00, "officer": 1.80}
    climate = _climate_adjustment(chart.month_branch)
    total = max(0.001, sum(energy.values()))
    result: dict[str, float] = {}
    for element in ELEMENTS:
        role = element_role(day_element, element)
        value = role_values[role] + climate[element]
        share = energy[element] / total
        if share > 0.32:
            value -= min(0.80, (share - 0.32) * 3.5)
        result[element] = value

    # A clash predominantly damages the weaker root.  This is material in the
    # canonical 辛卯 + 乙酉 regression and applies uniformly to every chart.
    node_lookup = {node.id: node for node in nodes}
    totals_lookup = _branch_totals(nodes)
    for event in interactions:
        if event["type"] != "冲":
            continue
        members = [node_lookup.get(member) for member in event["members"]]
        members = [member for member in members if member is not None]
        if len(members) != 2:
            continue
        weaker = min(members, key=lambda node: (totals_lookup.get(node.id, 0.0), node.id))
        result[weaker.element] -= 0.50 * event["strength"]

    return {element: _half_step(clamp(value, -3.0, 3.0)) for element, value in result.items()}


def _event_effect(
    event: dict[str, Any],
    nodes: list[Node],
    dfp: dict[str, float],
) -> float:
    lookup = {node.id: node for node in nodes}
    branch_totals = _branch_totals(nodes)
    members = [lookup[member] for member in event["members"] if member in lookup]
    if not members:
        return 0.0
    kind = event["type"]
    if event.get("result_element") in ELEMENTS and kind in {"天干合", "六合", "半合", "三合", "三会"}:
        result_utility = dfp[event["result_element"]] / 3.0
        consumed = sum(dfp[node.element] / 3.0 for node in members) / len(members)
        return clamp(result_utility - 0.35 * consumed, -1.0, 1.0) * event["strength"]
    if kind in {"冲", "天干冲"} and len(members) == 2:
        if kind == "冲":
            target = min(members, key=lambda node: (branch_totals.get(node.id, 0.0), node.id))
        else:
            target = min(members, key=lambda node: (node.base_weight, node.id))
        return clamp(-dfp[target.element] / 3.0, -1.0, 1.0) * event["strength"]
    if kind in {"刑", "自刑", "害", "破"}:
        utility = sum(dfp[node.element] / 3.0 for node in members) / len(members)
        return clamp(-utility, -1.0, 1.0) * event["strength"]
    if kind == "墓库引动" and event.get("result_element") in ELEMENTS:
        return (dfp[event["result_element"]] / 3.0) * 0.35 * event["strength"]
    return 0.0


def _grouped_effects(
    interactions: list[dict[str, Any]],
    effects: dict[str, float],
    *,
    predicate: Any | None = None,
) -> list[float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in interactions:
        if predicate is not None and not predicate(event):
            continue
        grouped[event["dedupe_group"]].append(effects[event["id"]])
    result: list[float] = []
    for values in grouped.values():
        positives = sorted((value for value in values if value >= 0), reverse=True)
        negatives = sorted((-value for value in values if value < 0), reverse=True)
        positive = positives[0] + 0.25 * sum(positives[1:]) if positives else 0.0
        negative = negatives[0] + 0.25 * sum(negatives[1:]) if negatives else 0.0
        result.append(clamp(positive - negative, -1.0, 1.0))
    return result


def _pillar_alignment(pillar: Pillar, dfp: dict[str, float]) -> float:
    stem_element = STEMS[pillar.stem]["element"]
    stem_utility = dfp[stem_element] / 3.0
    hidden_utility = sum(
        share * (dfp[STEMS[hidden]["element"]] / 3.0)
        for hidden, share in BRANCHES[pillar.branch]["hidden"]
    )
    return clamp(0.45 * stem_utility + 0.55 * hidden_utility, -1.0, 1.0)


def _entropy_score(energy: dict[str, float]) -> float:
    total = sum(energy.values())
    if total <= 0:
        return 0.0
    entropy = -sum((value / total) * math.log(value / total) for value in energy.values() if value > 0)
    return 100.0 * entropy / math.log(len(ELEMENTS))


def _profile_score(dfp: dict[str, float]) -> float:
    strongest_help = max(dfp.values())
    strongest_harm = abs(min(dfp.values()))
    return clamp(50.0 + 3.0 * strongest_help - strongest_harm)


def _vp(
    interactions: list[dict[str, Any]],
    effects: dict[str, float],
    *,
    dynamic_only: bool = False,
) -> float:
    severity = {"冲": 1.00, "天干冲": 0.60, "刑": 0.85, "自刑": 0.70, "害": 0.55, "破": 0.45, "六合": 0.45, "半合": 0.35, "三合": 0.55, "三会": 0.55, "天干合": 0.40, "墓库引动": 0.35}
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in interactions:
        if dynamic_only and not event["dynamic"]:
            continue
        negative = max(0.0, -effects[event["id"]])
        if negative <= 0:
            continue
        prominence = 1.0
        if "day" in event["positions"]:
            prominence = 1.35
        elif "month" in event["positions"]:
            prominence = 1.20
        grouped[event["dedupe_group"]].append(
            negative * severity.get(event["type"], 0.30) * prominence
        )
    total = 0.0
    for values in grouped.values():
        ordered = sorted(values, reverse=True)
        total += ordered[0] + 0.25 * sum(ordered[1:])
    return clamp(total * SCORING["vp_scale"], 0.0, 25.0)


def _activation(
    interactions: list[dict[str, Any]],
    *,
    annual_only: bool,
) -> float:
    weights = {"冲": 30, "天干冲": 18, "刑": 24, "自刑": 18, "害": 14, "破": 10, "六合": 18, "半合": 14, "三合": 24, "三会": 26, "天干合": 16, "墓库引动": 12}
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in interactions:
        if annual_only and not event["annual"]:
            continue
        prominence = 1.20 if "day" in event["positions"] else 1.10 if "month" in event["positions"] else 1.0
        grouped[event["dedupe_group"]].append(weights.get(event["type"], 8) * prominence * event["strength"])
    total = 10.0 if annual_only else 0.0
    for values in grouped.values():
        ordered = sorted(values, reverse=True)
        total += ordered[0] + 0.25 * sum(ordered[1:])
    return clamp(total)


def _source_effect_mean(
    interactions: list[dict[str, Any]],
    effects: dict[str, float],
    source: str,
) -> float:
    values = _grouped_effects(
        interactions,
        effects,
        predicate=lambda event: source in event["sources"],
    )
    return sum(values) / len(values) if values else 0.0


def _climate_score(chart: Chart, energy: dict[str, float]) -> float:
    adjustment = _climate_adjustment(chart.month_branch)
    positive = [element for element, value in adjustment.items() if value > 0.25]
    negative = [element for element, value in adjustment.items() if value < -0.25]
    total = max(0.001, sum(energy.values()))
    good = sum(energy[element] for element in positive) / total
    excess = sum(energy[element] for element in negative) / total
    return clamp(45.0 + 70.0 * good - 45.0 * excess)


def _efm(nodes: list[Node], interactions: list[dict[str, Any]], activation: float) -> dict[str, float | int]:
    fields = {"事业权责": 0.0, "财务资源": 0.0, "关系家庭": 0.0, "健康压力": 0.0, "学习资质": 0.0, "迁移环境": 0.0}
    lookup = {node.id: node for node in nodes}
    for event in interactions:
        if not event["annual"]:
            continue
        base = event["strength"]
        if "day" in event["positions"]:
            fields["关系家庭"] += 1.5 * base
            fields["健康压力"] += 1.0 * base
        if "month" in event["positions"]:
            fields["事业权责"] += 1.3 * base
        if "year" in event["positions"] or "hour" in event["positions"]:
            fields["迁移环境"] += 0.8 * base
        for member in event["members"]:
            node = lookup.get(member)
            if not node:
                continue
            role = node.ten_god
            if role in {"正官", "七杀", "食神", "伤官"}:
                fields["事业权责"] += 0.5 * base
            if role in {"正财", "偏财", "比肩", "劫财"}:
                fields["财务资源"] += 0.5 * base
            if role in {"正印", "偏印"}:
                fields["学习资质"] += 0.6 * base
    maximum = max(fields.values(), default=0.0)
    if maximum <= 0:
        return {key: 0 for key in fields}
    return {key: round1(activation * value / maximum) for key, value in fields.items()}


def _layer_snapshot(chart: Chart, request: Request, layer: str) -> dict[str, Any]:
    nodes, interactions = layer_facts(chart, request, layer)
    energy = calculate_energy(nodes, interactions)
    ratio, dss_score = calculate_dss(STEMS[chart.day_master]["element"], energy)
    dfp = calculate_dfp(chart, ratio, energy, nodes, interactions)
    effects = {event["id"]: _event_effect(event, nodes, dfp) for event in interactions}
    enriched = [{**event, "net_effect": round1(effects[event["id"]])} for event in interactions]
    vp = _vp(interactions, effects)
    snapshot: dict[str, Any] = {
        "layer": layer,
        "season_anchor": chart.month_branch,
        "day_master": chart.day_master,
        "nodes": [node.public() for node in nodes],
        "energy": {element: round1(energy[element]) for element in ELEMENTS},
        "dss": {"ratio": round2(ratio), "band": dss_band(ratio), "score": round1(dss_score), "status": "computed"},
        "dfp": {element: round1(dfp[element]) for element in ELEMENTS},
        "dfp_score": round1(_profile_score(dfp)),
        "interactions": enriched,
        "vp": round1(vp),
        "_raw": {
            "energy": energy,
            "dss": ratio,
            "dss_score": dss_score,
            "dfp": dfp,
            "effects": effects,
            "nodes": nodes,
        },
    }
    return snapshot


def score_single_chart(chart: Chart, request: Request) -> dict[str, Any]:
    snapshots: dict[str, dict[str, Any]] = {}
    r = _layer_snapshot(chart, request, "R")
    snapshots["R"] = r
    rraw = r["_raw"]
    r_effect_values = list(rraw["effects"].values())
    route = clamp(55.0 + 20.0 * (sum(r_effect_values) / len(r_effect_values) if r_effect_values else 0.0))
    stability = clamp(100.0 - float(r["vp"]) * 4.0)
    nbs = clamp(
        0.30 * rraw["dss_score"]
        + 0.20 * _entropy_score(rraw["energy"])
        + 0.20 * _climate_score(chart, rraw["energy"])
        + 0.15 * route
        + 0.15 * stability
        + SCORING["nbs_calibration_offset"]
    )
    if chart.complete:
        r["nbs"] = round1(nbs)

    dls: float | None = None
    if "D" in request.layers:
        d = _layer_snapshot(chart, request, "D")
        snapshots["D"] = d
        draw = d["_raw"]
        alignment = _pillar_alignment(request.luck[chart.id], rraw["dfp"])
        interaction = _source_effect_mean(d["interactions"], draw["effects"], "D")
        dls = clamp(
            SCORING["dls_base"]
            + 0.30 * (draw["dss_score"] - rraw["dss_score"])
            + 22.0 * alignment
            + 16.0 * interaction
        )
        if chart.complete:
            d["dls"] = round1(dls)

    if "Y" in request.layers:
        y = _layer_snapshot(chart, request, "Y")
        snapshots["Y"] = y
        assert request.year is not None and dls is not None
        draw = snapshots["D"]["_raw"]
        yraw = y["_raw"]
        annual_alignment = _pillar_alignment(request.year, draw["dfp"])
        annual_effect = _source_effect_mean(y["interactions"], yraw["effects"], "Y")
        yds = clamp(
            SCORING["yds_base"]
            + 0.30 * (yraw["dss_score"] - draw["dss_score"])
            + 24.0 * annual_alignment
            + 18.0 * annual_effect
        )
        luck_alignment = _pillar_alignment(request.luck[chart.id], rraw["dfp"])
        opposition = 0.0
        if luck_alignment * annual_alignment < 0:
            opposition = min(1.0, abs(luck_alignment - annual_alignment))
        # Direct annual attack on the luck pillar is a stronger three-layer
        # contradiction than two unrelated mixed signals.
        if any(
            event["annual"]
            and "luck" in event["positions"]
            and event["type"] in {"冲", "刑", "害", "破", "天干冲"}
            for event in y["interactions"]
        ):
            opposition = max(opposition, 0.75)
        scs = clamp(
            SCORING["scs_base"]
            + 16.0 * (luck_alignment + annual_alignment) / 2.0
            + 16.0 * annual_effect
            - 20.0 * opposition
        )
        vp = _vp(y["interactions"], yraw["effects"], dynamic_only=False)
        eai = _activation(y["interactions"], annual_only=True)
        components = {
            "nbs": nbs,
            "dls": dls,
            "yds": yds,
            "dss_score": yraw["dss_score"],
            "dfp_score": _profile_score(yraw["dfp"]),
            "scs": scs,
            "vp": vp,
        }
        afs_raw = sum(components[name] * weight for name, weight in SINGLE_WEIGHTS.items()) - vp
        afs = clamp(afs_raw)
        if chart.complete:
            y.update(
                {
                    "yds": round1(yds),
                    "scs": round1(scs),
                    "vp": round1(vp),
                    "eai": {"score": round1(eai), "band": band(eai, ACTIVATION_BANDS), "status": "computed"},
                    "efm": _efm(yraw["nodes"], y["interactions"], eai),
                    "afs": {
                        "raw": round1(afs_raw),
                        "score": round1(afs),
                        "band": band(afs, AFS_BANDS),
                        "formula": "AFS-2.5-code",
                        "status": "computed",
                        "components": {key: round1(value) for key, value in components.items()},
                    },
                }
            )

    for snapshot in snapshots.values():
        snapshot.pop("_raw", None)
    evidence = sorted(
        {
            item["id"]: {
                "id": item["id"],
                "rule_id": item["rule_id"],
                "sources": item["sources"],
                "object": item["values"],
                "interaction": item["type"],
                "result_element": item.get("result_element"),
                "effect": item["net_effect"],
                "dedupe_group": item["dedupe_group"],
            }
            for snapshot in snapshots.values()
            for item in snapshot["interactions"]
        }.values(),
        key=lambda item: item["id"],
    )
    result: dict[str, Any] = {
        "chart_id": chart.id,
        "complete": chart.complete,
        "layers": snapshots,
        "evidence": evidence,
    }
    if not chart.complete:
        result["diagnostics"] = ["时柱未知：只输出机械事实与基础向量，不生成正式综合分。"]
    return result
