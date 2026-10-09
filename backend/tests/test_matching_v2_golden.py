"""P6-B1 artifact integrity only: never import application or ranking modules."""

import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "docs/validation/matching-v2-dataset-v1.json"
GOLDEN = ROOT / "docs/validation/matching-v2-golden-proposed-v1.json"
VALIDATOR = ROOT / "backend/validate_matching_v2_golden.py"
FROZEN_HASH = "ef362631fc3104c50f29bca301b1fc9368b74a3a1ae95d2c0ba1e491ced0add5"


def test_required_review_artifacts_exist():
    assert GOLDEN.is_file(), "P6-B1 proposed JSON is required"
    assert GOLDEN.with_name("matching-v2-golden-methodology.md").is_file()
    assert VALIDATOR.is_file(), "P6-B1 independent validator is required"


@pytest.fixture
def artifacts():
    assert GOLDEN.is_file(), "P6-B1 proposed JSON is required"
    assert VALIDATOR.is_file(), "P6-B1 independent validator is required"
    spec = importlib.util.spec_from_file_location("golden_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_artifacts_cover_exact_frozen_eligible_pairs_read_only(artifacts):
    module, proposed = artifacts
    before = DATASET.read_bytes()
    assert hashlib.sha256(before).hexdigest() == FROZEN_HASH
    dataset = json.loads(before)
    module.validate(proposed, dataset)
    pairs = {(x["need_id"], x["candidate_id"]) for x in proposed["labels"]}
    expected = {
        "N1": {"C01", "C02", "C03", "C04"},
        "N2": {"C05", "C06", "C07", "C08", "C10"},
        "N3": {"C08", "C09", "C10"},
        "N4": {"C13", "C14", "C16", "C17", "C18", "C19", "C21"},
        "N5": {"C16", "C17", "C18", "C20", "C22", "C24"},
        "N6": {"C20", "C22", "C24"},
        "N7": {"C25", "C26", "C28", "C29", "C30", "C32", "C35"},
        "N8": {"C29", "C30", "C35"},
    }
    assert pairs == {(n, c) for n, candidates in expected.items() for c in candidates}
    assert len(proposed["labels"]) == 38
    assert DATASET.read_bytes() == before


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "excluded",
        "unknown_id",
        "grade_bool",
        "grade_float",
        "grade_range",
        "empty_rationale",
        "empty_uncertainty",
        "empty_limitations",
        "missing_factor",
        "false_evidence",
        "proxy_missing",
        "proxy_invented",
        "fsp_score",
        "fsp_bonus",
        "fsp_count",
        "fsp_best",
        "fsp_verified",
        "fsp_missing",
        "control_missing",
        "control_grade",
        "negative_missing",
        "negative_reason",
        "status",
        "dataset_hash",
        "ranking_output",
        "private_field",
        "human_review_claim",
    ],
)
def test_validator_rejects_incomplete_or_contaminated_proposals(artifacts, mutation):
    module, original = artifacts
    module.validate(original, json.loads(DATASET.read_text(encoding="utf-8")))
    data = copy.deepcopy(original)
    label = data["labels"][0]
    if mutation == "missing":
        data["labels"].pop()
    elif mutation == "duplicate":
        data["labels"][-1] = copy.deepcopy(label)
    elif mutation in {"excluded", "unknown_id"}:
        label["candidate_id"] = "C15" if mutation == "excluded" else "C99"
    elif mutation.startswith("grade_"):
        label["relevance_grade"] = {
            "grade_bool": True,
            "grade_float": 2.0,
            "grade_range": 4,
        }[mutation]
    elif mutation in {"empty_rationale", "empty_uncertainty", "empty_limitations"}:
        key = mutation.removeprefix("empty_")
        label[key] = " " if key == "rationale" else []
    elif mutation == "missing_factor":
        del label["factors_considered"]["assessment_evidence"]
    elif mutation == "false_evidence":
        label["factors_considered"]["relevant_experience"]["years"] = 99
    elif mutation == "proxy_missing":
        next(x for x in data["labels"] if x["need_id"] == "N3")["flags"] = []
    elif mutation == "proxy_invented":
        label["flags"] = ["CATALOG_PROXY"]
    elif mutation.startswith("fsp_"):
        if mutation == "fsp_missing":
            data["fsp_expectations"].pop()
        else:
            key, value = {
                "fsp_score": ("expected_achievement_score", 99),
                "fsp_bonus": ("expected_bonus", 5),
                "fsp_count": ("distinct_competition_count", 9),
                "fsp_best": ("best_result_level", "WINNER"),
                "fsp_verified": ("verified", True),
            }[mutation]
            data["fsp_expectations"][0][key] = value
    elif mutation == "control_missing":
        data["controlled_comparisons"].pop()
    elif mutation == "control_grade":
        next(x for x in data["labels"] if x["candidate_id"] == "C06")[
            "relevance_grade"
        ] = 0
    elif mutation == "negative_missing":
        data["negative_cases"].pop()
    elif mutation == "negative_reason":
        data["negative_cases"][0]["required_exclusion"] = "consent"
    elif mutation == "status":
        data["status"] = "FINAL"
    elif mutation == "dataset_hash":
        data["dataset_reference"]["sha256"] = "0" * 64
    elif mutation == "human_review_claim":
        data["human_reviewed"] = True
    else:
        label["ranking_score" if mutation == "ranking_output" else "email"] = 99
    with pytest.raises(ValueError):
        module.validate(data, json.loads(DATASET.read_text(encoding="utf-8")))


def test_fsp_literal_business_expectations_and_controlled_comparisons(artifacts):
    _, data = artifacts
    expected = {
        "NONE": (False, 0, None, 0, 0),
        "ENTERED_UNVERIFIED": (False, 0, None, 0, 0),
        "VERIFIED_EMPTY": (True, 0, None, 0, 0),
        "PARTICIPANT": (True, 1, "PARTICIPANT", 10, 0.5),
        "FINALIST": (True, 1, "FINALIST", 45, 2.25),
        "PRIZE_WINNER": (True, 1, "PRIZE_WINNER", 66, 3.3),
        "WINNER": (True, 1, "WINNER", 80, 4),
        "MULTIPLE_COMPETITIONS": (True, 3, "WINNER", 100, 5),
        "TEAM_ACHIEVEMENT": (True, 1, "WINNER", 80, 4),
    }
    assert {x["scenario"] for x in data["fsp_expectations"]} == set(expected)
    for x in data["fsp_expectations"]:
        assert (
            tuple(
                x[k]
                for k in (
                    "verified",
                    "distinct_competition_count",
                    "best_result_level",
                    "expected_achievement_score",
                    "expected_bonus",
                )
            )
            == expected[x["scenario"]]
        )
    assert {tuple(x["candidate_ids"]) for x in data["controlled_comparisons"]} == {
        ("C05", "C06"),
        ("C17", "C18"),
    }


@pytest.mark.parametrize(
    "state,evidence,score,bonus,count,best",
    [
        ("VERIFIED", [("one", "PARTICIPANT")], 10, "0.5", 1, "PARTICIPANT"),
        ("VERIFIED", [("one", "FINALIST")], 45, "2.25", 1, "FINALIST"),
        ("VERIFIED", [("one", "PRIZE_WINNER")], 66, "3.3", 1, "PRIZE_WINNER"),
        ("VERIFIED", [("one", "WINNER")], 80, "4", 1, "WINNER"),
        ("VERIFIED", [], 0, "0", 0, None),
        ("ENTERED_UNVERIFIED", [("one", "WINNER")], 0, "0", 0, None),
        ("VERIFIED", [("one", "FINALIST"), ("one", "WINNER")], 80, "4", 1, "WINNER"),
        (
            "VERIFIED",
            [(str(i), "PARTICIPANT") for i in range(4)],
            30,
            "1.5",
            4,
            "PARTICIPANT",
        ),
    ],
)
def test_independent_fsp_formula_deduplicates_caps_and_requires_verification(
    artifacts,
    state,
    evidence,
    score,
    bonus,
    count,
    best,
):
    from decimal import Decimal

    module, _ = artifacts
    candidate = {
        "fsp": {
            "state": state,
            "achievements": [
                {"competition_id": cid, "result_level": level}
                for cid, level in evidence
            ],
        }
    }
    actual = module.fsp_expectation(candidate)
    assert actual["expected_achievement_score"] == Decimal(score)
    assert actual["expected_bonus"] == Decimal(bonus)
    assert actual["distinct_competition_count"] == count
    assert actual["best_result_level"] == best


def test_cli_deterministic_and_refuses_changed_dataset_bytes(artifacts, tmp_path):
    before = DATASET.read_bytes()
    command = [sys.executable, str(VALIDATOR)]
    runs = [subprocess.run(command, capture_output=True, timeout=30) for _ in range(2)]
    assert all(x.returncode == 0 for x in runs), runs[0].stderr
    assert runs[0].stdout == runs[1].stdout
    changed = tmp_path / "changed.json"
    changed.write_bytes(before + b" ")
    failed = subprocess.run(
        command + ["--dataset", str(changed)],
        capture_output=True,
        timeout=30,
    )
    assert failed.returncode != 0
    assert b"Frozen dataset SHA256 mismatch" in failed.stderr
    assert DATASET.read_bytes() == before


def test_validator_has_no_application_network_or_process_imports(artifacts):
    allowed = {"argparse", "hashlib", "json", "decimal", "pathlib", "typing"}
    for node in ast.walk(ast.parse(VALIDATOR.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert all(x.name.split(".")[0] in allowed for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module.split(".")[0] in allowed
