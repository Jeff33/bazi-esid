"""Deterministic compatibility layer built on the same chart fact engine."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Any

from .canonical import clamp, round1
from .constants import (
    ACTIVATION_BANDS,
    AFS_BANDS,
    CFS_WEIGHTS,
    CONTROLS,
    ELEMENTS,
    GENERATES,
    RAFS_WEIGHTS,
    STEMS,
)
from .facts import Node, detect_interactions
from .model import Chart, Request
from .scoring import (
    _activation,
    _climate_adjustment,
    _event_effect,
    _layer_snapshot,
    _profile_score,
    band,
    score_single_chart,
)


def _bottleneck(first: float, second: float) -> float:
    return 0.75 * min(first, second) + 0.25 * max(first, second)


def _shares(energy: dict[str, float]) -> dict[str, float]:
    total = max(0.001, sum(energy.values()))
    return {element: energy[element] / total for element in ELEMENTS}


def _partner_element(chart: Chart) -> str | None:
    day = STEMS[chart.day_master]["element"]
    if chart.sex == "male":
        return CONTROLS[day]
    if chart.sex == "female":
        return next(element for element, controlled in CONTROLS.items() if controlled == day)
    return None


def _palace_stability(snapshot: dict[str, Any]) -> float:
    events = [event for event in snapshot["interactions"] if "day" in event["positions"]]
    if not events:
        return 72.0
    negative = sum(max(0.0, -float(event["net_effect"])) * event["strength"] for event in events)
    positive = sum(max(0.0, float(event["net_effect"])) * event["strength"] for event in events)
    return clamp(72.0 + 16.0 * positive - 22.0 * negative)


def _partner_star_score(chart: Chart, snapshot: dict[str, Any]) -> float | None:
    element = _partner_element(chart)
    if element is None:
        return None
    raw = snapshot["_raw"]
    share = _shares(raw["energy"])[element]
    visible = any(
        node.kind == "stem" and node.element == element and node.base_weight > 0
        for node in raw["nodes"]
    )
    rooted = any(node.kind == "hidden" and node.element == element for node in raw["nodes"])
    return clamp(38.0 + 150.0 * min(0.28, share) + (9.0 if visible else 0.0) + (5.0 if rooted else 0.0))


def _ims(chart: Chart, snapshot: dict[str, Any]) -> float | None:
    if not chart.complete:
        return None
    partner_star = _partner_star_score(chart, snapshot)
    if partner_star is None:
        return None
    nbs = float(snapshot.get("nbs", 50.0))
    capacity = clamp(0.65 * float(snapshot["dss"]["score"]) + 0.35 * nbs)
    palace = _palace_stability(snapshot)
    route = clamp(45.0 + 0.50 * _profile_score(snapshot["_raw"]["dfp"]))
    energy_share = _shares(snapshot["_raw"]["energy"])
    day = STEMS[chart.day_master]["element"]
    output = GENERATES[day]
    companion = day
    boundary = clamp(70.0 - 55.0 * max(0.0, energy_share[output] + energy_share[companion] - 0.48))
    return clamp(0.25 * capacity + 0.25 * palace + 0.20 * partner_star + 0.20 * route + 0.10 * boundary)


def _directional_fit(receiver: dict[str, Any], provider: dict[str, Any]) -> float:
    receiver_dfp = receiver["_raw"]["dfp"]
    provider_dfp = provider["_raw"]["dfp"]
    provider_shares = _shares(provider["_raw"]["energy"])
    utility = 0.0
    for element in ELEMENTS:
        receiver_utility = receiver_dfp[element] / 3.0
        provider_cost = max(0.0, -provider_dfp[element] / 3.0)
        sustainability = 1.0 - 0.35 * provider_cost
        utility += provider_shares[element] * receiver_utility * sustainability
    return clamp(50.0 + 50.0 * utility)


def _pair_flow(first: dict[str, Any], second: dict[str, Any]) -> float:
    a = _shares(first["_raw"]["energy"])
    b = _shares(second["_raw"]["energy"])
    generation = 0.0
    control = 0.0
    for element in ELEMENTS:
        generation += a[element] * b[GENERATES[element]] + b[element] * a[GENERATES[element]]
        control += a[element] * b[CONTROLS[element]] + b[element] * a[CONTROLS[element]]
    return clamp(50.0 + 150.0 * generation - 115.0 * control)


def _cross_events(
    first_nodes: list[Node],
    second_nodes: list[Node],
) -> tuple[list[Node], list[dict[str, Any]]]:
    # The annual pillar is one shared clock, not two relationship actors.  Use
    # one synthetic Y node set so swapping A/B cannot change a group candidate.
    annual: list[Node] = []
    for node in first_nodes:
        if node.source != "Y":
            continue
        prefix = f"{node.chart_id}_Y"
        shared_id = node.id.replace(prefix, "Y", 1)
        shared_parent = node.parent.replace(prefix, "Y", 1) if node.parent else None
        annual.append(replace(node, id=shared_id, chart_id="Y", parent=shared_parent))
    nodes = sorted(
        [node for node in first_nodes + second_nodes if node.source != "Y"] + annual,
        key=lambda node: node.id,
    )
    lookup = {node.id: node for node in nodes}
    branch_values: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        if node.kind == "branch" and node.chart_id in {"A", "B"}:
            branch_values[node.chart_id].add(node.value)
    events = []
    for event in detect_interactions(nodes):
        charts = {lookup[member].chart_id for member in event["members"] if member in lookup}
        if len(charts) < 2:
            continue
        if event["type"] in {"半合", "三合", "三会"} or (
            event["type"] == "刑" and len(set(event["values"])) >= 3
        ):
            required = set(event["values"])
            if any(required <= values for values in branch_values.values()):
                continue
        events.append(event)
    return nodes, events


def _cross_effects(
    nodes: list[Node],
    events: list[dict[str, Any]],
    first: dict[str, Any],
    second: dict[str, Any],
) -> dict[str, float]:
    average_dfp = {
        element: (first["_raw"]["dfp"][element] + second["_raw"]["dfp"][element]) / 2.0
        for element in ELEMENTS
    }
    return {event["id"]: _event_effect(event, nodes, average_dfp) for event in events}


def _net_effect(events: list[dict[str, Any]], effects: dict[str, float], predicate: Any = None) -> float:
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in events:
        if predicate is not None and not predicate(event):
            continue
        grouped[event["dedupe_group"]].append(effects[event["id"]])
    values: list[float] = []
    for group in grouped.values():
        ordered = sorted(group, key=abs, reverse=True)
        values.append(clamp(ordered[0] + 0.25 * sum(ordered[1:]), -1.0, 1.0))
    return sum(values) / len(values) if values else 0.0


def _relationship_rvp(
    events: list[dict[str, Any]],
    effects: dict[str, float],
    *,
    dynamic_only: bool = False,
) -> float:
    """Relationship volatility includes motion even when a clash removes a taboo.

    This is separate from auspiciousness: beneficial movement can still require
    negotiation.  Same-episode evidence uses strongest + 25% of the remainder.
    """

    motion = {"冲": 0.90, "刑": 0.80, "自刑": 0.60, "害": 0.55, "破": 0.45, "天干冲": 0.25}
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in events:
        if dynamic_only and not event["dynamic"]:
            continue
        prominence = 1.30 if "day" in event["positions"] else 1.15 if "month" in event["positions"] else 1.0
        structural_motion = motion.get(event["type"], 0.0)
        adverse = max(0.0, -effects[event["id"]]) * 0.70
        if structural_motion or adverse:
            grouped[event["dedupe_group"]].append((structural_motion + adverse) * prominence * event["strength"])
    total = 0.0
    for values in grouped.values():
        ordered = sorted(values, reverse=True)
        total += ordered[0] + 0.25 * sum(ordered[1:])
    return clamp(total * 1.50, 0.0, 25.0)


def _climate_fit(receiver: Chart, provider: dict[str, Any]) -> float:
    need = _climate_adjustment(receiver.month_branch)
    shares = _shares(provider["_raw"]["energy"])
    value = sum(shares[element] * need[element] for element in ELEMENTS)
    return clamp(50.0 + 55.0 * value)


def _pair_metrics(
    first_chart: Chart,
    second_chart: Chart,
    first: dict[str, Any],
    second: dict[str, Any],
) -> dict[str, Any]:
    nodes, events = _cross_events(first["_raw"]["nodes"], second["_raw"]["nodes"])
    effects = _cross_effects(nodes, events, first, second)
    net = _net_effect(events, effects)
    rfs = _bottleneck(_directional_fit(first, second), _directional_fit(second, first))
    palace_events = [event for event in events if "day" in event["positions"]]
    palace_net = _net_effect(palace_events, effects)
    star_a = _partner_star_score(first_chart, second)
    star_b = _partner_star_score(second_chart, first)
    star_match = _bottleneck(star_a, star_b) if star_a is not None and star_b is not None else None
    mps = None
    if star_match is not None:
        palace_pair = clamp(55.0 + 45.0 * palace_net)
        role = clamp(50.0 + 35.0 * net)
        protect = clamp(55.0 + 30.0 * max(0.0, net) - 25.0 * max(0.0, -net))
        mps = clamp(0.35 * palace_pair + 0.30 * star_match + 0.20 * role + 0.15 * protect)
    flow = _pair_flow(first, second)
    crs = clamp(0.55 * flow + 0.45 * (50.0 + 50.0 * net))
    chs = _bottleneck(_climate_fit(first_chart, second), _climate_fit(second_chart, first))
    combine_types = {"天干合", "六合", "半合", "三合", "三会"}
    hoi_net = _net_effect(events, effects, predicate=lambda event: event["type"] in combine_types)
    hoi = clamp(50.0 + 50.0 * hoi_net)
    rvp = _relationship_rvp(events, effects)
    bcs = clamp(0.25 * (50.0 + 50.0 * net) + 0.20 * flow + 0.20 * rfs + 0.20 * (100.0 - rvp * 4.0) + 0.15 * chs)
    return {
        "nodes": nodes,
        "events": events,
        "effects": effects,
        "net": net,
        "rfs": rfs,
        "mps": mps,
        "crs": crs,
        "chs_fit": chs,
        "hoi_quality": hoi,
        "rvp": rvp,
        "bcs": bcs,
    }


def _ims_penalty(first: float, second: float) -> float:
    low = min(first, second)
    gap = abs(first - second)
    if low < 30 or gap >= 40:
        return 10.0
    if low < 45 or gap >= 30:
        return 6.0
    if low < 55 or gap >= 20:
        return 3.0
    return 0.0


def _public_pair(metrics: dict[str, Any], layer: str) -> dict[str, Any]:
    result = {
        "layer": layer,
        "bcs": round1(metrics["bcs"]),
        "rfs": round1(metrics["rfs"]),
        "mps": round1(metrics["mps"]) if metrics["mps"] is not None else None,
        "crs": round1(metrics["crs"]),
        "chs_fit": round1(metrics["chs_fit"]),
        "hoi_quality": round1(metrics["hoi_quality"]),
        "ssf_support": 50,
        "rvp": round1(metrics["rvp"]),
        "interactions": [
            {**event, "net_effect": round1(metrics["effects"][event["id"]])}
            for event in metrics["events"]
        ],
    }
    return result


def score_compatibility(request: Request) -> dict[str, Any]:
    first_chart, second_chart = request.charts
    public_individual = {
        chart.id: score_single_chart(chart, request)
        for chart in request.charts
    }
    internal: dict[str, dict[str, dict[str, Any]]] = {}
    pairs: dict[str, dict[str, Any]] = {}
    for layer in request.layers:
        internal[layer] = {
            first_chart.id: _layer_snapshot(first_chart, request, layer),
            second_chart.id: _layer_snapshot(second_chart, request, layer),
        }
        pairs[layer] = _pair_metrics(
            first_chart,
            second_chart,
            internal[layer][first_chart.id],
            internal[layer][second_chart.id],
        )

    for chart in request.charts:
        nbs = public_individual[chart.id]["layers"]["R"].get("nbs")
        if nbs is not None:
            internal["R"][chart.id]["nbs"] = nbs

    ims_a = _ims(first_chart, internal["R"][first_chart.id])
    ims_b = _ims(second_chart, internal["R"][second_chart.id])
    formal = ims_a is not None and ims_b is not None
    static = pairs["R"]
    output_layers = {layer: _public_pair(metrics, layer) for layer, metrics in pairs.items()}
    result: dict[str, Any] = {
        "individual": public_individual,
        "layers": output_layers,
        "formal_scoring": formal,
    }
    if not formal:
        result["diagnostics"] = ["正式合婚分需要双方完整四柱及 male/female 性别；当前只输出机械双盘事实。"]
        return result

    assert ims_a is not None and ims_b is not None and static["mps"] is not None
    penalty = _ims_penalty(ims_a, ims_b)
    ims = clamp((ims_a + ims_b) / 2.0 - penalty)
    components = {
        "ims": ims,
        "rfs": static["rfs"],
        "mps": static["mps"],
        "crs": static["crs"],
        "chs_fit": static["chs_fit"],
        "hoi_quality": static["hoi_quality"],
        "ssf_support": 50.0,
    }
    cfs_raw = sum(components[key] * weight for key, weight in CFS_WEIGHTS.items()) - static["rvp"]
    cfs = clamp(cfs_raw)
    output_layers["R"].update(
        {
            "ims_a": round1(ims_a),
            "ims_b": round1(ims_b),
            "ims_penalty": round1(penalty),
            "ims": round1(ims),
            "cfs": {
                "raw": round1(cfs_raw),
                "score": round1(cfs),
                "band": band(cfs, AFS_BANDS),
                "formula": "CFS-2.5-code",
                "status": "computed",
                "components": {key: round1(value) for key, value in components.items()},
                "bcs_note": "BCS is diagnostic and has zero weight in the published CFS formula.",
            },
        }
    )

    dcs: float | None = None
    if "D" in request.layers:
        dynamic = pairs["D"]
        dls_a = float(public_individual["A"]["layers"]["D"]["dls"])
        dls_b = float(public_individual["B"]["layers"]["D"]["dls"])
        sync = clamp(100.0 - abs(dls_a - dls_b))
        assert dynamic["mps"] is not None
        dcs = clamp(
            0.20 * sync
            + 0.25 * dynamic["rfs"]
            + 0.20 * dynamic["mps"]
            + 0.25 * dynamic["crs"]
            + 0.10 * dynamic["chs_fit"]
        )
        output_layers["D"]["dcs"] = round1(dcs)
        output_layers["D"]["sync"] = round1(sync)

    if "Y" in request.layers:
        assert dcs is not None
        annual = pairs["Y"]
        assert annual["mps"] is not None
        annual_net = _net_effect(
            annual["events"], annual["effects"], predicate=lambda event: event["annual"]
        )
        yval = clamp(50.0 + 50.0 * annual_net)
        ycs = clamp(
            0.20 * yval
            + 0.25 * annual["rfs"]
            + 0.25 * annual["mps"]
            + 0.20 * annual["crs"]
            + 0.10 * annual["chs_fit"]
        )
        scs_a = float(public_individual["A"]["layers"]["Y"]["scs"])
        scs_b = float(public_individual["B"]["layers"]["Y"]["scs"])
        r_scs = clamp(0.40 * _bottleneck(scs_a, scs_b) + 0.60 * (50.0 + 50.0 * annual_net))
        rvp_dynamic = _relationship_rvp(annual["events"], annual["effects"], dynamic_only=True)
        rafs_components = {
            "cfs": cfs,
            "dcs": dcs,
            "ycs": ycs,
            "crs": annual["crs"],
            "r_scs": r_scs,
        }
        rafs_raw = sum(rafs_components[key] * weight for key, weight in RAFS_WEIGHTS.items()) - rvp_dynamic
        rafs = clamp(rafs_raw)
        rai = _activation(annual["events"], annual_only=True)
        output_layers["Y"].update(
            {
                "ycs": round1(ycs),
                "yval": round1(yval),
                "r_scs": round1(r_scs),
                "rvp_dynamic": round1(rvp_dynamic),
                "r_afs": {
                    "raw": round1(rafs_raw),
                    "score": round1(rafs),
                    "band": band(rafs, AFS_BANDS),
                    "formula": "R-AFS-2.5-code",
                    "status": "computed",
                    "components": {key: round1(value) for key, value in rafs_components.items()},
                },
                "rai": {"score": round1(rai), "band": band(rai, ACTIVATION_BANDS), "status": "computed"},
            }
        )
    return result
