"""Deterministic Four-Pillars fact extraction and interaction detection."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable

from .canonical import evidence_id, round1
from .constants import (
    BRANCHES,
    BRANCH_BREAKS,
    BRANCH_CLASHES,
    BRANCH_COMBINES,
    BRANCH_HARMS,
    BRANCH_POSITION_WEIGHTS,
    CONTROLS,
    GENERATES,
    PAIR_PUNISHMENTS,
    PILLAR_RELATION_MODIFIER,
    SEASON_COEFFICIENTS,
    SELF_PUNISHMENTS,
    SOURCE_WEIGHTS,
    STEMS,
    STEM_CLASHES,
    STEM_COMBINES,
    STEM_POSITION_WEIGHTS,
    STORAGE_BRANCH,
    TEN_GOD_NAMES,
    THREE_HARMONIES,
    THREE_MEETINGS,
    THREE_PUNISHMENTS,
)
from .model import Chart, Pillar, Request


@dataclass(frozen=True)
class Node:
    id: str
    chart_id: str
    source: str
    position: str
    kind: str
    value: str
    element: str
    polarity: str
    base_weight: float
    ten_god: str
    parent: str | None = None

    def public(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "chart": self.chart_id,
            "source": self.source,
            "position": self.position,
            "kind": self.kind,
            "value": self.value,
            "element": self.element,
            "polarity": self.polarity,
            "base_weight": round1(self.base_weight),
            "ten_god": self.ten_god,
        }
        if self.parent:
            result["parent"] = self.parent
        return result


def element_role(day_element: str, other_element: str) -> str:
    if other_element == day_element:
        return "same"
    if GENERATES[day_element] == other_element:
        return "output"
    if CONTROLS[day_element] == other_element:
        return "wealth"
    if CONTROLS[other_element] == day_element:
        return "officer"
    if GENERATES[other_element] == day_element:
        return "resource"
    raise AssertionError(f"unreachable element relation: {day_element}/{other_element}")


def ten_god(day_master: str, other_stem: str) -> str:
    day = STEMS[day_master]
    other = STEMS[other_stem]
    relation = element_role(day["element"], other["element"])
    same_polarity = day["polarity"] == other["polarity"]
    return TEN_GOD_NAMES[(relation, same_polarity)]


def _pillar_relation(pillar: Pillar) -> str:
    stem_element = STEMS[pillar.stem]["element"]
    branch_main_stem = BRANCHES[pillar.branch]["hidden"][0][0]
    branch_element = STEMS[branch_main_stem]["element"]
    if stem_element == branch_element:
        return "same"
    if GENERATES[branch_element] == stem_element:
        return "branch_generates_stem"
    if GENERATES[stem_element] == branch_element:
        return "stem_generates_branch"
    if CONTROLS[stem_element] == branch_element:
        return "stem_controls_branch"
    if CONTROLS[branch_element] == stem_element:
        return "branch_controls_stem"
    return "neutral"


def _pillar_nodes(
    chart: Chart,
    pillar: Pillar,
    source: str,
    position: str,
) -> list[Node]:
    prefix = f"{chart.id}_{source}.{position}"
    source_weight = SOURCE_WEIGHTS[source]
    season = SEASON_COEFFICIENTS[chart.month_branch]
    relation_modifier = PILLAR_RELATION_MODIFIER[_pillar_relation(pillar)]
    stem_element = STEMS[pillar.stem]["element"]
    stem_weight = (
        source_weight
        * STEM_POSITION_WEIGHTS[position]
        * season[stem_element]
        * relation_modifier
    )
    result = [
        Node(
            id=f"{prefix}.stem",
            chart_id=chart.id,
            source=source,
            position=position,
            kind="stem",
            value=pillar.stem,
            element=stem_element,
            polarity=STEMS[pillar.stem]["polarity"],
            base_weight=stem_weight,
            ten_god=ten_god(chart.day_master, pillar.stem),
        )
    ]
    branch_id = f"{prefix}.branch"
    main_stem = BRANCHES[pillar.branch]["hidden"][0][0]
    result.append(
        Node(
            id=branch_id,
            chart_id=chart.id,
            source=source,
            position=position,
            kind="branch",
            value=pillar.branch,
            element=STEMS[main_stem]["element"],
            polarity=STEMS[main_stem]["polarity"],
            base_weight=0.0,
            ten_god=ten_god(chart.day_master, main_stem),
        )
    )
    for index, (hidden_stem, share) in enumerate(BRANCHES[pillar.branch]["hidden"]):
        element = STEMS[hidden_stem]["element"]
        weight = (
            source_weight
            * BRANCH_POSITION_WEIGHTS[position]
            * share
            * season[element]
        )
        result.append(
            Node(
                id=f"{branch_id}.hidden.{index}",
                chart_id=chart.id,
                source=source,
                position=position,
                kind="hidden",
                value=hidden_stem,
                element=element,
                polarity=STEMS[hidden_stem]["polarity"],
                base_weight=weight,
                ten_god=ten_god(chart.day_master, hidden_stem),
                parent=branch_id,
            )
        )
    return result


def build_nodes(chart: Chart, request: Request, layer: str) -> list[Node]:
    nodes: list[Node] = []
    for position in ("year", "month", "day", "hour"):
        pillar = chart.pillars[position]
        if pillar is not None:
            nodes.extend(_pillar_nodes(chart, pillar, "R", position))
    if layer in {"D", "Y"}:
        nodes.extend(_pillar_nodes(chart, request.luck[chart.id], "D", "luck"))
    if layer == "Y":
        assert request.year is not None
        nodes.extend(_pillar_nodes(chart, request.year, "Y", "annual"))
    return sorted(nodes, key=lambda node: node.id)


def _interaction(
    rule_id: str,
    kind: str,
    members: Iterable[Node],
    result_element: str | None = None,
    strength: float = 1.0,
) -> dict[str, Any]:
    selected = sorted(members, key=lambda node: node.id)
    body = {
        "rule_id": rule_id,
        "type": kind,
        "members": [node.id for node in selected],
        "values": [node.value for node in selected],
        "result_element": result_element,
    }
    positions = sorted({node.position for node in selected})
    sources = sorted({node.source for node in selected})
    return {
        "id": evidence_id("ev", body),
        **body,
        "sources": sources,
        "positions": positions,
        "strength": strength,
        "dynamic": any(source in {"D", "Y"} for source in sources),
        "annual": "Y" in sources,
        "dedupe_group": evidence_id(
            "episode",
            {"kind": kind, "values": sorted(body["values"]), "positions": positions},
        ),
    }


def _first_by_value(nodes: list[Node]) -> dict[str, Node]:
    result: dict[str, Node] = {}
    source_order = {"Y": 0, "D": 1, "R": 2}
    position_order = {"annual": 0, "luck": 1, "day": 2, "month": 3, "year": 4, "hour": 5}
    for node in sorted(
        nodes,
        key=lambda item: (
            source_order[item.source],
            position_order[item.position],
            item.id,
        ),
    ):
        result.setdefault(node.value, node)
    return result


def detect_interactions(nodes: list[Node]) -> list[dict[str, Any]]:
    stems = [node for node in nodes if node.kind == "stem"]
    branches = [node for node in nodes if node.kind == "branch"]
    events: list[dict[str, Any]] = []

    for left, right in combinations(stems, 2):
        pair = frozenset((left.value, right.value))
        if len(pair) < 2:
            continue
        if pair in STEM_COMBINES:
            events.append(
                _interaction("INT-STEM-COMBINE", "天干合", (left, right), STEM_COMBINES[pair], 0.70)
            )
        if pair in STEM_CLASHES:
            events.append(_interaction("INT-STEM-CLASH", "天干冲", (left, right), strength=0.55))

    for left, right in combinations(branches, 2):
        pair = frozenset((left.value, right.value))
        if len(pair) < 2:
            continue
        if pair in BRANCH_COMBINES:
            events.append(
                _interaction("INT-BRANCH-SIX-COMBINE", "六合", (left, right), BRANCH_COMBINES[pair], 0.75)
            )
        if pair in BRANCH_CLASHES:
            events.append(_interaction("INT-BRANCH-CLASH", "冲", (left, right), strength=0.90))
        if pair in BRANCH_HARMS:
            events.append(_interaction("INT-BRANCH-HARM", "害", (left, right), strength=0.55))
        if pair in BRANCH_BREAKS:
            events.append(_interaction("INT-BRANCH-BREAK", "破", (left, right), strength=0.45))
        if pair in PAIR_PUNISHMENTS:
            events.append(_interaction("INT-BRANCH-PAIR-PUNISH", "刑", (left, right), strength=0.70))

    by_value = _first_by_value(branches)
    present = set(by_value)
    for group, element in THREE_HARMONIES.items():
        if group <= present:
            events.append(
                _interaction(
                    "INT-BRANCH-THREE-HARMONY",
                    "三合",
                    (by_value[value] for value in sorted(group)),
                    element,
                    1.00,
                )
            )
        else:
            available = sorted(group & present)
            if len(available) == 2:
                events.append(
                    _interaction(
                        "INT-BRANCH-HALF-HARMONY",
                        "半合",
                        (by_value[value] for value in available),
                        element,
                        0.55,
                    )
                )
    for group, element in THREE_MEETINGS.items():
        if group <= present:
            events.append(
                _interaction(
                    "INT-BRANCH-THREE-MEETING",
                    "三会",
                    (by_value[value] for value in sorted(group)),
                    element,
                    1.00,
                )
            )
    for group, label in THREE_PUNISHMENTS.items():
        if group <= present:
            event = _interaction(
                "INT-BRANCH-THREE-PUNISH",
                "刑",
                (by_value[value] for value in sorted(group)),
                strength=0.85,
            )
            event["label"] = label
            events.append(event)

    for value in sorted(SELF_PUNISHMENTS & present):
        matching = [node for node in branches if node.value == value]
        for left, right in combinations(matching, 2):
            events.append(_interaction("INT-BRANCH-SELF-PUNISH", "自刑", (left, right), strength=0.65))

    # A storage branch is considered activated only when another recorded
    # interaction touches it.  This records movement, never "automatic release".
    existing = list(events)
    storage_nodes = {node.id: node for node in branches if node.value in STORAGE_BRANCH}
    for node_id, node in storage_nodes.items():
        touching = [event for event in existing if node_id in event["members"]]
        if touching:
            event = _interaction(
                "INT-STORAGE-ACTIVATION",
                "墓库引动",
                (node,),
                STORAGE_BRANCH[node.value],
                min(1.0, max(item["strength"] for item in touching)),
            )
            event["trigger_ids"] = sorted(item["id"] for item in touching)
            events.append(event)

    unique = {event["id"]: event for event in events}
    return sorted(unique.values(), key=lambda event: event["id"])


def layer_facts(chart: Chart, request: Request, layer: str) -> tuple[list[Node], list[dict[str, Any]]]:
    nodes = build_nodes(chart, request, layer)
    return nodes, detect_interactions(nodes)
