#!/usr/bin/env python3
"""Command-line interface for the single canonical ESID engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from esid_engine import (
    ENGINE_VERSION,
    METHOD_VERSION,
    RULESET_SHA256,
    InputError,
    analyze,
    analyze_batch,
    verify,
)
from esid_engine.canonical import canonical_json, load_json


def _read(path: str | None) -> Any:
    if path:
        return load_json(Path(path))
    return load_json(sys.stdin.read())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bazi-ESID 2.5 Code Edition")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "batch", "verify"):
        command = sub.add_parser(name)
        command.add_argument("--input", help="JSON file; defaults to stdin")
        command.add_argument("--compact", action="store_true", help="emit canonical compact JSON")
    sub.add_parser("version")
    sub.add_parser("self-test")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "version":
            print(canonical_json({"method_version": METHOD_VERSION, "engine_version": ENGINE_VERSION, "ruleset_sha256": RULESET_SHA256}, pretty=True))
            return 0
        if args.command == "self-test":
            sample = {
                "schema": "bazi-esid.input/1",
                "record_id": "self-test",
                "mode": "single",
                "charts": [{"id": "A", "sex": "male", "pillars": {"year": "庚午", "month": "甲申", "day": "乙巳", "hour": "庚辰"}}],
                "timing": {"luck": {"A": "辛卯"}, "year": "乙酉"},
            }
            first = analyze(sample)
            second = analyze(sample)
            if first != second or not verify(first):
                raise RuntimeError("determinism or integrity self-test failed")
            layers = first["payload"]["result"]["layers"]
            expected = (
                layers["R"]["dss"]["ratio"],
                layers["D"]["dss"]["ratio"],
                layers["Y"]["dss"]["ratio"],
                layers["Y"]["afs"]["score"],
                layers["Y"]["eai"]["score"],
            )
            if expected != (0.83, 0.96, 0.76, 31.5, 92):
                raise RuntimeError(f"golden regression drifted: {expected}")
            print(canonical_json({"ok": True, "ruleset_sha256": RULESET_SHA256}, pretty=True))
            return 0
        payload = _read(args.input)
        if args.command == "analyze":
            output = analyze(payload)
        elif args.command == "batch":
            output = analyze_batch(payload)
        else:
            output = {"valid": verify(payload)}
        print(canonical_json(output, pretty=not args.compact))
        return 0 if args.command != "verify" or output["valid"] else 1
    except (InputError, OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
