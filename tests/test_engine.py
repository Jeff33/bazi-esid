from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from esid_engine import InputError, RULESET_SHA256, analyze, analyze_batch, verify  # noqa: E402
from esid_engine.canonical import load_json  # noqa: E402
from esid_engine.constants import BRANCHES, STEMS  # noqa: E402
from esid_engine.facts import layer_facts, ten_god  # noqa: E402
from esid_engine.model import Pillar, parse_request  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class EngineTests(unittest.TestCase):
    def test_all_sixty_valid_pillars_and_parity_rejection(self) -> None:
        valid = []
        for stem, stem_data in STEMS.items():
            for branch, branch_data in BRANCHES.items():
                text = stem + branch
                if (stem_data["index"] - branch_data["index"]) % 2 == 0:
                    self.assertEqual(Pillar.parse(text, "p").text, text)
                    valid.append(text)
        self.assertEqual(len(valid), 60)
        with self.assertRaises(InputError):
            Pillar.parse("甲丑", "p")
        with self.assertRaises(InputError):
            Pillar.parse("AB", "p")

    def test_duplicate_and_unknown_json_fields_rejected(self) -> None:
        with self.assertRaises(InputError):
            load_json('{"a":1,"a":2}')
        payload = fixture("golden_single.json")
        payload["manual_score"] = 88
        with self.assertRaises(InputError):
            analyze(payload)

    def test_ten_god_and_hidden_stem_facts(self) -> None:
        self.assertEqual(ten_god("乙", "庚"), "正官")
        self.assertEqual(ten_god("乙", "戊"), "正财")
        request = parse_request(fixture("golden_single.json"))
        nodes, _ = layer_facts(request.charts[0], request, "R")
        hidden = [(node.value, node.ten_god) for node in nodes if node.id.startswith("A_R.hour.branch.hidden")]
        self.assertEqual(hidden, [("戊", "正财"), ("乙", "比肩"), ("癸", "偏印")])

    def test_golden_single_calibration(self) -> None:
        output = analyze(fixture("golden_single.json"))
        layers = output["payload"]["result"]["layers"]
        self.assertEqual(layers["R"]["dss"]["ratio"], 0.83)
        self.assertEqual(layers["D"]["dss"]["ratio"], 0.96)
        self.assertEqual(layers["Y"]["dss"]["ratio"], 0.76)
        self.assertEqual(layers["R"]["dfp"], {"木": 2, "火": 0, "土": -2, "金": -3, "水": 3})
        self.assertEqual(layers["Y"]["dfp"], {"木": 1.5, "火": 0, "土": -2, "金": -3, "水": 3})
        self.assertEqual(layers["R"]["nbs"], 63)
        self.assertEqual(layers["D"]["dls"], 60)
        self.assertEqual(layers["Y"]["yds"], 40.5)
        self.assertEqual(layers["Y"]["dss"]["score"], 56)
        self.assertEqual(layers["Y"]["dfp_score"], 56)
        self.assertEqual(layers["Y"]["scs"], 35)
        self.assertEqual(layers["Y"]["vp"], 21.5)
        self.assertEqual(layers["Y"]["afs"]["score"], 31.5)
        self.assertEqual(layers["Y"]["eai"]["score"], 92)

    def test_golden_interactions_keep_sources(self) -> None:
        output = analyze(fixture("golden_single.json"))
        interactions = output["payload"]["result"]["layers"]["Y"]["interactions"]
        signatures = {(item["type"], tuple(item["values"])) for item in interactions}
        self.assertIn(("冲", ("卯", "酉")), signatures)
        self.assertIn(("六合", ("辰", "酉")), signatures)
        self.assertIn(("半合", ("巳", "酉")), signatures)
        self.assertTrue(any(item["annual"] and "Y" in item["sources"] for item in interactions))

    def test_full_rebuild_and_month_anchor(self) -> None:
        request = parse_request(fixture("golden_single.json"))
        nodes, _ = layer_facts(request.charts[0], request, "Y")
        self.assertEqual({node.source for node in nodes}, {"R", "D", "Y"})
        output = analyze(fixture("golden_single.json"))
        layer = output["payload"]["result"]["layers"]["Y"]
        self.assertEqual(layer["season_anchor"], "申")
        self.assertEqual(len(layer["nodes"]), len(nodes))

    def test_layer_totals_are_not_imputed(self) -> None:
        payload = fixture("golden_single.json")
        payload["timing"] = {"luck": {}, "year": None}
        r_only = analyze(payload)["payload"]["result"]["layers"]
        self.assertEqual(set(r_only), {"R"})
        self.assertNotIn("afs", r_only["R"])
        payload["timing"] = {"luck": {"A": "辛卯"}, "year": None}
        d_only = analyze(payload)["payload"]["result"]["layers"]
        self.assertEqual(set(d_only), {"R", "D"})
        self.assertNotIn("afs", d_only["D"])

    def test_unknown_hour_disables_formal_total(self) -> None:
        payload = fixture("golden_single.json")
        payload["charts"][0]["pillars"]["hour"] = None
        output = analyze(payload)["payload"]["result"]
        self.assertFalse(output["complete"])
        self.assertNotIn("nbs", output["layers"]["R"])
        self.assertNotIn("afs", output["layers"]["Y"])

    def test_determinism_hash_and_tamper_detection(self) -> None:
        payload = fixture("golden_single.json")
        first = analyze(payload)
        second = analyze(copy.deepcopy(payload))
        self.assertEqual(first, second)
        self.assertTrue(verify(first))
        self.assertEqual(first["payload"]["reproducibility"]["ruleset_sha256"], RULESET_SHA256)
        tampered = copy.deepcopy(first)
        tampered["payload"]["result"]["layers"]["Y"]["afs"]["score"] = 99
        self.assertFalse(verify(tampered))

    def test_cli_bytes_ignore_hash_seed_timezone_and_locale(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "run_esid.py"),
            "analyze",
            "--compact",
            "--input",
            str(FIXTURES / "golden_single.json"),
        ]
        outputs = []
        for seed, timezone, locale in (("1", "UTC", "C"), ("997", "Asia/Shanghai", "C.UTF-8")):
            env = dict(os.environ, PYTHONHASHSEED=seed, TZ=timezone, LC_ALL=locale)
            outputs.append(subprocess.check_output(command, env=env))
        self.assertEqual(outputs[0], outputs[1])

    def test_only_one_code_path(self) -> None:
        policy = analyze(fixture("golden_single.json"))["payload"]["policy"]
        self.assertEqual(policy["execution_path"], "code_only")
        self.assertFalse(policy["interval_scores"])
        self.assertFalse(policy["llm_override"])

    def test_compatibility_regression_and_bcs_boundary(self) -> None:
        output = analyze(fixture("compat_pair.json"))["payload"]["result"]
        layer = output["layers"]["R"]
        self.assertTrue(output["formal_scoring"])
        self.assertEqual(layer["cfs"]["score"], 51.8)
        self.assertIn("bcs", layer)
        self.assertNotIn("bcs", layer["cfs"]["components"])
        self.assertGreater(len(layer["interactions"]), 0)

    def test_compatibility_is_symmetric(self) -> None:
        original = fixture("compat_pair.json")
        swapped = copy.deepcopy(original)
        a, b = swapped["charts"]
        swapped["charts"] = [{**b, "id": "A"}, {**a, "id": "B"}]
        first = analyze(original)["payload"]["result"]["layers"]["R"]["cfs"]["score"]
        second = analyze(swapped)["payload"]["result"]["layers"]["R"]["cfs"]["score"]
        self.assertEqual(first, second)

    def test_compatibility_without_sex_is_fact_only(self) -> None:
        payload = fixture("compat_pair.json")
        payload["charts"][1]["sex"] = "unspecified"
        result = analyze(payload)["payload"]["result"]
        self.assertFalse(result["formal_scoring"])
        self.assertNotIn("cfs", result["layers"]["R"])

    def test_dynamic_compatibility_separates_volatility(self) -> None:
        payload = fixture("compat_pair.json")
        payload["timing"] = {"luck": {"A": "辛卯", "B": "乙卯"}, "year": "乙酉"}
        result = analyze(payload)["payload"]["result"]["layers"]
        self.assertIn("dcs", result["D"])
        self.assertIn("ycs", result["Y"])
        self.assertIn("r_afs", result["Y"])
        self.assertIn("rai", result["Y"])
        self.assertNotIn("rvp", result["R"]["cfs"]["components"])
        self.assertIn("rvp_dynamic", result["Y"])
        self.assertNotIn("rvp_dynamic", result["R"])

    def test_incomplete_compatibility_luck_layer_rejected(self) -> None:
        payload = fixture("compat_pair.json")
        payload["timing"] = {"luck": {"A": "辛卯"}, "year": None}
        with self.assertRaises(InputError):
            analyze(payload)

    def test_score_boundaries_over_deterministic_chart_set(self) -> None:
        pillars = ["甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉"]
        for index in range(0, 6):
            payload = fixture("golden_single.json")
            payload["record_id"] = f"bounds-{index}"
            payload["charts"][0]["pillars"] = {
                "year": pillars[index],
                "month": pillars[index + 1],
                "day": pillars[index + 2],
                "hour": pillars[index + 3],
            }
            payload["timing"] = {"luck": {"A": pillars[index + 4]}, "year": pillars[index + 1]}
            layers = analyze(payload)["payload"]["result"]["layers"]
            for layer in layers.values():
                self.assertTrue(0 <= layer["dss"]["score"] <= 100)
                self.assertTrue(0 <= layer["vp"] <= 25)
                self.assertTrue(all(-3 <= value <= 3 for value in layer["dfp"].values()))
            self.assertTrue(0 <= layers["Y"]["afs"]["score"] <= 100)
            self.assertTrue(0 <= layers["Y"]["eai"]["score"] <= 100)

    def test_batch_ranking_is_input_order_invariant(self) -> None:
        first = fixture("golden_single.json")
        second = copy.deepcopy(first)
        first["record_id"] = "A"
        second["record_id"] = "B"
        second["timing"]["year"] = "丙戌"
        batch = {"schema": "bazi-esid.batch-input/1", "batch_id": "rank", "ranking_metric": "afs", "records": [second, first]}
        reversed_batch = copy.deepcopy(batch)
        reversed_batch["records"].reverse()
        one = analyze_batch(batch)
        two = analyze_batch(reversed_batch)
        self.assertEqual(one, two)
        ranking = one["payload"]["ranking"]
        self.assertEqual({item["record_id"] for item in ranking}, {"A", "B"})
        self.assertGreaterEqual(ranking[0]["score"], ranking[1]["score"])


if __name__ == "__main__":
    unittest.main()
