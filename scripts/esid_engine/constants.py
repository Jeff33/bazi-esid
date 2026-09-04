"""Frozen rule tables for Bazi-ESID 2.5 Code Edition.

Every numeric choice that the prose manuscript left open lives in this file.
Changing any value creates a different ruleset hash and therefore a new engine
version.  The runtime never asks a language model to fill a numeric gap.
"""

from __future__ import annotations

from typing import Final


METHOD_VERSION: Final = "2.5-code"
ENGINE_VERSION: Final = "1.0.0"
SCHEMA_VERSION: Final = "bazi-esid.input/1"
OUTPUT_SCHEMA: Final = "bazi-esid.output/1"

ELEMENTS: Final = ("木", "火", "土", "金", "水")
GENERATES: Final = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS: Final = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

STEMS: Final = {
    "甲": {"element": "木", "polarity": "阳", "index": 0},
    "乙": {"element": "木", "polarity": "阴", "index": 1},
    "丙": {"element": "火", "polarity": "阳", "index": 2},
    "丁": {"element": "火", "polarity": "阴", "index": 3},
    "戊": {"element": "土", "polarity": "阳", "index": 4},
    "己": {"element": "土", "polarity": "阴", "index": 5},
    "庚": {"element": "金", "polarity": "阳", "index": 6},
    "辛": {"element": "金", "polarity": "阴", "index": 7},
    "壬": {"element": "水", "polarity": "阳", "index": 8},
    "癸": {"element": "水", "polarity": "阴", "index": 9},
}

# Hidden-stem shares are frozen numerical releases of 主气/中气/余气.
BRANCHES: Final = {
    "子": {"index": 0, "hidden": (("癸", 1.00),)},
    "丑": {"index": 1, "hidden": (("己", 0.60), ("癸", 0.30), ("辛", 0.10))},
    "寅": {"index": 2, "hidden": (("甲", 0.60), ("丙", 0.30), ("戊", 0.10))},
    "卯": {"index": 3, "hidden": (("乙", 1.00),)},
    "辰": {"index": 4, "hidden": (("戊", 0.60), ("乙", 0.30), ("癸", 0.10))},
    "巳": {"index": 5, "hidden": (("丙", 0.60), ("戊", 0.30), ("庚", 0.10))},
    "午": {"index": 6, "hidden": (("丁", 0.70), ("己", 0.30))},
    "未": {"index": 7, "hidden": (("己", 0.60), ("丁", 0.30), ("乙", 0.10))},
    "申": {"index": 8, "hidden": (("庚", 0.60), ("壬", 0.30), ("戊", 0.10))},
    "酉": {"index": 9, "hidden": (("辛", 1.00),)},
    "戌": {"index": 10, "hidden": (("戊", 0.60), ("辛", 0.30), ("丁", 0.10))},
    "亥": {"index": 11, "hidden": (("壬", 0.70), ("甲", 0.30))},
}

SOURCE_WEIGHTS: Final = {"R": 1.00, "D": 0.70, "Y": 0.45}
STEM_POSITION_WEIGHTS: Final = {
    "year": 0.90,
    "month": 1.10,
    "day": 0.00,  # day master is the reference point, not ordinary support
    "hour": 0.90,
    "luck": 0.95,
    "annual": 0.95,
}
BRANCH_POSITION_WEIGHTS: Final = {
    "year": 1.00,
    "month": 1.60,
    "day": 1.25,
    "hour": 1.00,
    "luck": 1.10,
    "annual": 1.10,
}

# Month-command multipliers.  The original month remains the seasonal anchor
# in R, R+D and R+D+Y; dynamic pillars never replace it.
SEASON_COEFFICIENTS: Final = {
    "寅": {"木": 1.60, "火": 1.25, "土": 0.55, "金": 0.65, "水": 0.90},
    "卯": {"木": 1.60, "火": 1.25, "土": 0.55, "金": 0.65, "水": 0.90},
    "辰": {"木": 1.15, "火": 0.85, "土": 1.35, "金": 0.70, "水": 0.90},
    "巳": {"木": 0.90, "火": 1.60, "土": 1.25, "金": 0.55, "水": 0.65},
    "午": {"木": 0.90, "火": 1.60, "土": 1.25, "金": 0.55, "水": 0.65},
    "未": {"木": 0.90, "火": 1.15, "土": 1.35, "金": 0.80, "水": 0.65},
    "申": {"木": 0.65, "火": 0.55, "土": 0.90, "金": 1.60, "水": 1.25},
    "酉": {"木": 0.65, "火": 0.55, "土": 0.90, "金": 1.60, "水": 1.25},
    "戌": {"木": 0.65, "火": 0.90, "土": 1.35, "金": 1.15, "水": 0.80},
    "亥": {"木": 1.25, "火": 0.65, "土": 0.65, "金": 0.90, "水": 1.60},
    "子": {"木": 1.25, "火": 0.65, "土": 0.65, "金": 0.90, "水": 1.60},
    "丑": {"木": 0.80, "火": 0.65, "土": 1.35, "金": 0.90, "水": 1.15},
}

PILLAR_RELATION_MODIFIER: Final = {
    "same": 1.08,
    "branch_generates_stem": 1.05,
    "stem_generates_branch": 0.95,
    "stem_controls_branch": 0.90,
    "branch_controls_stem": 0.82,
    "neutral": 1.00,
}

STEM_COMBINES: Final = {
    frozenset(("甲", "己")): "土",
    frozenset(("乙", "庚")): "金",
    frozenset(("丙", "辛")): "水",
    frozenset(("丁", "壬")): "木",
    frozenset(("戊", "癸")): "火",
}
STEM_CLASHES: Final = {
    frozenset(("甲", "庚")),
    frozenset(("乙", "辛")),
    frozenset(("丙", "壬")),
    frozenset(("丁", "癸")),
}
BRANCH_COMBINES: Final = {
    frozenset(("子", "丑")): "土",
    frozenset(("寅", "亥")): "木",
    frozenset(("卯", "戌")): "火",
    frozenset(("辰", "酉")): "金",
    frozenset(("巳", "申")): "水",
    frozenset(("午", "未")): "土",
}
BRANCH_CLASHES: Final = {
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
}
BRANCH_HARMS: Final = {
    frozenset(("子", "未")),
    frozenset(("丑", "午")),
    frozenset(("寅", "巳")),
    frozenset(("卯", "辰")),
    frozenset(("申", "亥")),
    frozenset(("酉", "戌")),
}
BRANCH_BREAKS: Final = {
    frozenset(("子", "酉")),
    frozenset(("卯", "午")),
    frozenset(("辰", "丑")),
    frozenset(("未", "戌")),
    frozenset(("寅", "亥")),
    frozenset(("巳", "申")),
}
THREE_HARMONIES: Final = {
    frozenset(("申", "子", "辰")): "水",
    frozenset(("亥", "卯", "未")): "木",
    frozenset(("寅", "午", "戌")): "火",
    frozenset(("巳", "酉", "丑")): "金",
}
THREE_MEETINGS: Final = {
    frozenset(("寅", "卯", "辰")): "木",
    frozenset(("巳", "午", "未")): "火",
    frozenset(("申", "酉", "戌")): "金",
    frozenset(("亥", "子", "丑")): "水",
}
THREE_PUNISHMENTS: Final = {
    frozenset(("寅", "巳", "申")): "恃势之刑",
    frozenset(("丑", "未", "戌")): "无恩之刑",
}
PAIR_PUNISHMENTS: Final = {frozenset(("子", "卯")): "无礼之刑"}
SELF_PUNISHMENTS: Final = {"辰", "午", "酉", "亥"}
STORAGE_BRANCH: Final = {"辰": "水", "戌": "火", "丑": "金", "未": "木"}

TEN_GOD_NAMES: Final = {
    ("same", True): "比肩",
    ("same", False): "劫财",
    ("output", True): "食神",
    ("output", False): "伤官",
    ("wealth", True): "偏财",
    ("wealth", False): "正财",
    ("officer", True): "七杀",
    ("officer", False): "正官",
    ("resource", True): "偏印",
    ("resource", False): "正印",
}

# Deterministic scoring policy.  These values define the sole code path.
SCORING: Final = {
    "daymaster_anchor": 1.30,
    "pressure_floor": 0.60,
    "pressure_scale": 0.60,
    "pressure_factors": {"output": 0.55, "wealth": 0.70, "officer": 0.85},
    "dynamic_support_root_multiplier": 2.00,
    "annual_attack_on_luck_root": 0.35,
    "dss_log_penalty": 163.6,
    "nbs_calibration_offset": 1.0,
    "dls_base": 56.9,
    "yds_base": 58.8,
    "scs_base": 58.0,
    "vp_scale": 7.30,
    "interaction_energy": {
        "六合": 0.20,
        "半合": 0.16,
        "三合": 0.45,
        "三会": 0.50,
        "天干合": 0.18,
    },
    "disruption_energy": {"冲": 0.16, "刑": 0.10, "害": 0.06, "破": 0.04, "天干冲": 0.08},
    "round_digits": 1,
}

SINGLE_WEIGHTS: Final = {
    "nbs": 0.20,
    "dls": 0.20,
    "yds": 0.20,
    "dss_score": 0.15,
    "dfp_score": 0.15,
    "scs": 0.10,
}
CFS_WEIGHTS: Final = {
    "ims": 0.20,
    "rfs": 0.20,
    "mps": 0.20,
    "crs": 0.15,
    "chs_fit": 0.10,
    "hoi_quality": 0.10,
    "ssf_support": 0.05,
}
RAFS_WEIGHTS: Final = {
    "cfs": 0.30,
    "dcs": 0.20,
    "ycs": 0.20,
    "crs": 0.15,
    "r_scs": 0.15,
}

AFS_BANDS: Final = (
    (30, "大忌/高风险阶段"),
    (45, "阻滞明显"),
    (55, "中平偏险"),
    (70, "中上"),
    (85, "顺势"),
    (101, "大顺/高度顺势"),
)
ACTIVATION_BANDS: Final = (
    (30, "平淡"),
    (50, "小变化"),
    (70, "明显变化"),
    (85, "大变化"),
    (101, "强烈变局"),
)

# Human-readable descriptor is included in the ruleset hash.  Tables above are
# added by ruleset_payload() in canonical.py so no silent constant is omitted.
RULESET_NOTES: Final = {
    "identity": "Bazi-ESID 2.5 Code Edition canonical ruleset",
    "execution_path": "code_only",
    "interval_scores": False,
    "llm_numeric_override": False,
    "calendar_boundary": "four pillars are authoritative input; casting is upstream",
    "missing_layer_policy": "omit dependent totals; never impute neutral 50",
    "ssf_policy": "standalone shensha disabled; neutral support=50",
    "bcs_policy": "diagnostic only because published CFS formula omits BCS",
    "rvp_policy": "CFS subtracts static RVP; R-AFS subtracts dynamic incremental RVP only",
}
