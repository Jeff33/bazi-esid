"""Public analysis, batch and verification API."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .canonical import InputError, RULESET_SHA256, normalize_json, sha256_json
from .compatibility import score_compatibility
from .constants import ENGINE_VERSION, METHOD_VERSION, OUTPUT_SCHEMA
from .model import parse_request
from .scoring import score_single_chart


def implementation_sha256() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.glob("*.py"), key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _envelope(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_json(payload)
    return {
        "payload": normalized,
        "integrity": {
            "canonicalization": "esid-json-v1",
            "payload_sha256": sha256_json(normalized),
        },
    }


def analyze(payload: Any) -> dict[str, Any]:
    request = parse_request(payload)
    input_sha = sha256_json(request.normalized_input)
    if request.mode == "single":
        result = score_single_chart(request.charts[0], request)
    else:
        result = score_compatibility(request)
    output = {
        "schema": OUTPUT_SCHEMA,
        "record_id": request.record_id,
        "reproducibility": {
            "method_version": METHOD_VERSION,
            "engine_version": ENGINE_VERSION,
            "ruleset_id": f"bazi-esid-{METHOD_VERSION}-canonical",
            "ruleset_sha256": RULESET_SHA256,
            "implementation_sha256": implementation_sha256(),
            "input_sha256": input_sha,
            "run_id": sha256_json({"ruleset": RULESET_SHA256, "input": input_sha})[:24],
        },
        "mode": {
            "requested": request.mode,
            "effective": request.effective_mode,
            "layers": request.layers,
            "complete": all(chart.complete for chart in request.charts),
        },
        "input_ledger": request.normalized_input,
        "result": result,
        "policy": {
            "numeric_authority": "code",
            "execution_path": "code_only",
            "interval_scores": False,
            "llm_override": False,
        },
    }
    return _envelope(output)


def _extract_metric(envelope: dict[str, Any], metric: str) -> float | None:
    result = envelope["payload"]["result"]
    try:
        if metric == "afs":
            return float(result["layers"]["Y"]["afs"]["score"])
        if metric == "nbs":
            return float(result["layers"]["R"]["nbs"])
        if metric == "cfs":
            return float(result["layers"]["R"]["cfs"]["score"])
        if metric == "r_afs":
            return float(result["layers"]["Y"]["r_afs"]["score"])
    except (KeyError, TypeError, ValueError):
        return None
    raise InputError("ranking_metric must be afs, nbs, cfs, or r_afs")


def analyze_batch(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InputError("batch input must be an object")
    allowed = {"schema", "batch_id", "ranking_metric", "records"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise InputError(f"unknown batch field(s): {', '.join(unknown)}")
    if payload.get("schema") != "bazi-esid.batch-input/1":
        raise InputError("batch schema must equal 'bazi-esid.batch-input/1'")
    batch_id = payload.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id.strip():
        raise InputError("batch_id must be a non-empty string")
    metric = payload.get("ranking_metric")
    if metric not in {"afs", "nbs", "cfs", "r_afs"}:
        raise InputError("ranking_metric must be afs, nbs, cfs, or r_afs")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise InputError("records must be a non-empty array")
    ids = [record.get("record_id") if isinstance(record, dict) else None for record in records]
    if any(not isinstance(item, str) or not item for item in ids):
        raise InputError("every batch record needs a non-empty record_id")
    if len(set(ids)) != len(ids):
        raise InputError("batch record_id values must be unique")

    analyses = [analyze(record) for record in sorted(records, key=lambda item: item["record_id"])]
    ranked: list[dict[str, Any]] = []
    unranked: list[dict[str, str]] = []
    comparability: tuple[Any, ...] | None = None
    for envelope in analyses:
        meta = envelope["payload"]
        score = _extract_metric(envelope, metric)
        key = (
            meta["reproducibility"]["ruleset_sha256"],
            meta["mode"]["effective"],
            meta["mode"]["complete"],
            metric,
        )
        if score is None:
            unranked.append({"record_id": meta["record_id"], "reason": f"metric {metric} is unavailable"})
            continue
        if comparability is None:
            comparability = key
        if key != comparability:
            unranked.append({"record_id": meta["record_id"], "reason": "not in the first comparable cohort"})
            continue
        ranked.append({"record_id": meta["record_id"], "score": score})
    ranked.sort(key=lambda item: (-item["score"], item["record_id"]))
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    batch_payload = {
        "schema": "bazi-esid.batch-output/1",
        "batch_id": batch_id.strip(),
        "ranking_metric": metric,
        "reproducibility": {
            "method_version": METHOD_VERSION,
            "engine_version": ENGINE_VERSION,
            "ruleset_sha256": RULESET_SHA256,
            "implementation_sha256": implementation_sha256(),
        },
        "ranking": ranked,
        "unranked": sorted(unranked, key=lambda item: item["record_id"]),
        "records": analyses,
    }
    return _envelope(batch_payload)


def verify(envelope: Any) -> bool:
    if not isinstance(envelope, dict) or set(envelope) != {"payload", "integrity"}:
        return False
    integrity = envelope.get("integrity")
    if not isinstance(integrity, dict):
        return False
    return (
        integrity.get("canonicalization") == "esid-json-v1"
        and integrity.get("payload_sha256") == sha256_json(envelope["payload"])
    )
