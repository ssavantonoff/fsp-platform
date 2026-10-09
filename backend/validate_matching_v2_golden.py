"""P6-B1 read-only integrity checks. No application imports or ranking metrics."""

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "docs/validation/matching-v2-dataset-v1.json"
GOLDEN = ROOT / "docs/validation/matching-v2-golden-proposed-v1.json"
FROZEN_HASH = "ef362631fc3104c50f29bca301b1fc9368b74a3a1ae95d2c0ba1e491ced0add5"
STARTING_SHA = "a7590b79227f31abc9dba3e639d567cc0553138d"
GRADE_COMPATIBILITY = {
    "JUNIOR": {"JUNIOR", "MIDDLE"},
    "MIDDLE": {"MIDDLE", "SENIOR"},
    "SENIOR": {"SENIOR"},
}
EXPECTED_COUNTS = {
    "N1": 4,
    "N2": 5,
    "N3": 3,
    "N4": 7,
    "N5": 6,
    "N6": 3,
    "N7": 7,
    "N8": 3,
}
PROXIES = {"N3", "N5", "N7", "N8"}
SCENARIOS = {
    "NONE": "C05",
    "ENTERED_UNVERIFIED": "C03",
    "VERIFIED_EMPTY": "C36",
    "PARTICIPANT": "C06",
    "FINALIST": "C10",
    "PRIZE_WINNER": "C18",
    "WINNER": "C22",
    "MULTIPLE_COMPETITIONS": "C02",
    "TEAM_ACHIEVEMENT": "C15",
}
QUALITY = {
    "PARTICIPANT": Decimal("0"),
    "FINALIST": Decimal("0.50"),
    "PRIZE_WINNER": Decimal("0.80"),
    "WINNER": Decimal("1.00"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def record(value: Any, keys: set[str], context: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{context}: object required")
    require(set(value) == keys, f"{context}: missing or unknown fields")
    return dict(value)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def texts(value: Any, context: str) -> None:
    require(isinstance(value, list) and bool(value), f"{context}: list required")
    require(all(nonempty(x) for x in value), f"{context}: nonempty text required")


def reasons(need: dict[str, Any], candidate: dict[str, Any]) -> set[str]:
    """Independent approved hard filters, without soft factors or declared grade."""
    result = set()
    if candidate["personal_data_consent"] is not True:
        result.add("consent")
    if candidate["specialization"] != need["specialization"]:
        result.add("specialization")
    if any(
        candidate[x] is None
        for x in (
            "verified_grade",
            "normalized_assessment_score",
            "assessment_verified_at",
        )
    ):
        result.add("unverified_assessment")
    if candidate["verified_grade"] not in GRADE_COMPATIBILITY[need["required_grade"]]:
        result.add("grade")
    if not set(need["must_have_skills"]) <= set(candidate["self_declared_skills"]):
        result.add("must_have")
    return result


def fsp_expectation(candidate: dict[str, Any]) -> dict[str, Any]:
    """Approved business formula on frozen evidence, never production scoring."""
    fsp = candidate["fsp"]
    verified = fsp["state"] == "VERIFIED"
    evidence = fsp["achievements"] if verified else []
    count = len({x["competition_id"] for x in evidence})
    best = max(
        (x["result_level"] for x in evidence), key=QUALITY.__getitem__, default=None
    )
    # Multiply before division: the approved /3*30 component is exactly 10 per
    # competition, avoiding a recurring-decimal intermediate and display rounding.
    quality = QUALITY[best] if best is not None else Decimal(0)
    score = Decimal(min(count, 3)) * 30 / 3 + quality * 70
    return {
        "verified": verified,
        "distinct_competition_count": count,
        "best_result_level": best,
        "expected_achievement_score": score,
        "expected_bonus": score / 100 * 5,
    }


def check_factors(value: Any, need: dict[str, Any], candidate: dict[str, Any]) -> None:
    factors = record(
        value,
        {
            "specialization",
            "verified_grade",
            "must_have",
            "nice_to_have",
            "assessment_evidence",
            "relevant_experience",
        },
        "factors",
    )
    for key in ("specialization", "verified_grade", "must_have", "nice_to_have"):
        require(nonempty(factors[key]), f"factors.{key}: text required")
    assessment = record(
        factors["assessment_evidence"],
        {"normalized_score", "verified_at", "provenance"},
        "assessment_evidence",
    )
    require(type(assessment["normalized_score"]) is int, "Assessment score type")
    require(
        assessment
        == {
            "normalized_score": candidate["normalized_assessment_score"],
            "verified_at": candidate["assessment_verified_at"],
            "provenance": "SYNTHETIC_CANONICAL_FIXTURE",
        },
        "Assessment evidence differs from frozen candidate",
    )
    experience = record(
        factors["relevant_experience"],
        {"years", "soft_target_years", "provenance"},
        "experience",
    )
    for key in ("years", "soft_target_years"):
        require(
            experience[key] is None or type(experience[key]) in (int, float),
            "Experience must be numeric or unknown, never boolean",
        )
    require(
        experience
        == {
            "years": candidate["years_of_experience"],
            "soft_target_years": need["target_experience_years"],
            "provenance": "SELF_DECLARED_GENERAL_TENURE; ROLE_RELEVANCE_UNCONFIRMED",
        },
        "Experience evidence differs from frozen inputs",
    )


def validate(proposed: Any, dataset: dict[str, Any]) -> None:
    """Validate the closed artifact contract; qualitative prose needs human review."""
    data = record(
        proposed,
        {
            "name",
            "version",
            "status",
            "human_reviewed",
            "dataset_reference",
            "provenance",
            "labels",
            "fsp_expectations",
            "controlled_comparisons",
            "negative_cases",
        },
        "proposal",
    )
    require(data["name"] == "matching-v2-golden-proposed-v1", "Proposal name")
    require(type(data["version"]) is int and data["version"] == 1, "Version")
    require(
        data["status"] == "PROPOSED" and data["human_reviewed"] is False,
        "Only unreviewed PROPOSED labels are permitted",
    )
    require(
        data["dataset_reference"]
        == {
            "name": "matching-v2-validation-v1",
            "path": "docs/validation/matching-v2-dataset-v1.json",
            "sha256": FROZEN_HASH,
            "freeze_commit": STARTING_SHA,
        },
        "Frozen dataset reference mismatch",
    )
    provenance = record(
        data["provenance"],
        {
            "author_type",
            "requirements",
            "production_ranking_observed",
            "production_scoring_used",
            "ranking_metrics_computed",
        },
        "provenance",
    )
    require(
        provenance["author_type"] == "AI_PROPOSED"
        and nonempty(provenance["requirements"]),
        "AI provenance required",
    )
    require(
        all(
            provenance[k] is False
            for k in (
                "production_ranking_observed",
                "production_scoring_used",
                "ranking_metrics_computed",
            )
        ),
        "Independence declarations must be false",
    )
    require(dataset["name"] == "matching-v2-validation-v1", "Dataset namespace")
    needs = {x["id"]: x for x in dataset["needs"]}
    candidates = {x["id"]: x for x in dataset["candidates"]}
    require(
        len(dataset["needs"]) == 8 and set(needs) == set(EXPECTED_COUNTS),
        "Exact Need IDs required",
    )
    require(
        len(dataset["candidates"]) == 36
        and set(candidates) == {f"C{i:02}" for i in range(1, 37)},
        "Exact Candidate IDs required",
    )
    eligible = {
        (n, c)
        for n in needs
        for c in candidates
        if not reasons(needs[n], candidates[c])
    }
    counts = {n: sum(pair[0] == n for pair in eligible) for n in needs}
    require(
        counts == EXPECTED_COUNTS and len(eligible) == 38,
        "Structural reference mismatch: STOP",
    )
    require(
        isinstance(data["labels"], list) and len(data["labels"]) == 38,
        "Exactly 38 labels required",
    )
    labels = {}
    for item in data["labels"]:
        label = record(
            item,
            {
                "need_id",
                "candidate_id",
                "relevance_grade",
                "rationale",
                "factors_considered",
                "limitations",
                "uncertainty",
                "flags",
            },
            "label",
        )
        require(
            isinstance(label["need_id"], str)
            and isinstance(label["candidate_id"], str),
            "Pair IDs must be strings",
        )
        pair = (label["need_id"], label["candidate_id"])
        require(pair in eligible, f"Not an eligible frozen pair: {pair}")
        require(pair not in labels, f"Duplicate pair: {pair}")
        grade = label["relevance_grade"]
        require(type(grade) is int and 0 <= grade <= 3, "Grade must be integer 0..3")
        require(nonempty(label["rationale"]), "Complete rationale required")
        texts(label["limitations"], "limitations")
        texts(label["uncertainty"], "uncertainty")
        expected_flags = ["CATALOG_PROXY"] if pair[0] in PROXIES else []
        require(label["flags"] == expected_flags, "Catalog proxy marker mismatch")
        if pair[0] in PROXIES:
            require(
                needs[pair[0]]["limitation"] in label["limitations"],
                "Explicit frozen catalog limitation required",
            )
        check_factors(label["factors_considered"], needs[pair[0]], candidates[pair[1]])
        labels[pair] = label
    require(set(labels) == eligible, "Missing eligible pairs")
    require(
        isinstance(data["fsp_expectations"], list)
        and len(data["fsp_expectations"]) == 9,
        "Nine FSP scenarios required",
    )
    seen = set()
    for item in data["fsp_expectations"]:
        case = record(
            item,
            {
                "scenario",
                "candidate_id",
                "verified",
                "distinct_competition_count",
                "best_result_level",
                "expected_achievement_score",
                "expected_bonus",
                "rationale",
            },
            "FSP case",
        )
        scenario = case["scenario"]
        require(
            isinstance(scenario, str) and scenario in SCENARIOS, "Unknown FSP scenario"
        )
        require(scenario not in seen, "Duplicate FSP scenario")
        seen.add(scenario)
        require(case["candidate_id"] == SCENARIOS[scenario], "FSP fixture mismatch")
        require(type(case["verified"]) is bool, "FSP verified must be boolean")
        require(type(case["distinct_competition_count"]) is int, "FSP count type")
        require(nonempty(case["rationale"]), "FSP rationale required")
        expected = fsp_expectation(candidates[case["candidate_id"]])
        for key, value in expected.items():
            if isinstance(value, Decimal):
                require(type(case[key]) in (int, float), "FSP score type")
                require(Decimal(str(case[key])) == value, f"Incorrect FSP {key}")
            else:
                require(case[key] == value, f"Incorrect FSP {key}")
    require(seen == set(SCENARIOS), "Missing FSP scenario")
    check_controls(data["controlled_comparisons"], needs, candidates, labels)
    check_negatives(data["negative_cases"], needs, candidates)


def check_controls(
    value: Any,
    needs: dict[str, Any],
    candidates: dict[str, Any],
    labels: dict[tuple[str, str], Any],
) -> None:
    require(isinstance(value, list) and len(value) == 2, "Two controlled pairs")
    expected = {("C05", "C06"): ["N2"], ("C17", "C18"): ["N4", "N5"]}
    seen = set()
    professional = (
        "specialization",
        "verified_grade",
        "normalized_assessment_score",
        "assessment_verified_at",
        "self_declared_skills",
        "years_of_experience",
    )
    for item in value:
        case = record(
            item,
            {
                "candidate_ids",
                "need_ids",
                "professional_inputs_equal",
                "expected_professional_fit_relation",
                "expected_relevance_relation",
                "expected_bonuses",
                "rationale",
            },
            "controlled comparison",
        )
        require(
            isinstance(case["candidate_ids"], list)
            and all(isinstance(x, str) for x in case["candidate_ids"]),
            "Control IDs",
        )
        pair = tuple(case["candidate_ids"])
        require(pair in expected and pair not in seen, "Unknown/duplicate control")
        seen.add(pair)
        left, right = (candidates[x] for x in pair)
        require(
            all(left[k] == right[k] for k in professional),
            "Controlled professional inputs differ",
        )
        require(
            case["professional_inputs_equal"] is True
            and case["expected_professional_fit_relation"] == "EQUAL_NOT_COMPUTED"
            and case["expected_relevance_relation"] == "EQUAL",
            "Control relation mismatch",
        )
        require(case["need_ids"] == expected[pair], "Control Need coverage")
        require(nonempty(case["rationale"]), "Control rationale required")
        bonuses = case["expected_bonuses"]
        require(
            isinstance(bonuses, list)
            and len(bonuses) == 2
            and all(type(x) in (int, float) for x in bonuses),
            "Control bonus types",
        )
        require(
            [Decimal(str(x)) for x in bonuses]
            == [fsp_expectation(c)["expected_bonus"] for c in (left, right)],
            "Control FSP contribution mismatch",
        )
        for nid in case["need_ids"]:
            require(
                not reasons(needs[nid], left) and not reasons(needs[nid], right),
                "Controlled pair must be eligible",
            )
            require(
                labels[nid, pair[0]]["relevance_grade"]
                == labels[nid, pair[1]]["relevance_grade"],
                "Controlled label drift",
            )
    require(seen == set(expected), "Missing controlled comparison")


def check_negatives(
    value: Any, needs: dict[str, Any], candidates: dict[str, Any]
) -> None:
    expected = {
        "C15": (["N4", "N5", "N6"], "must_have"),
        "C27": (["N7", "N8"], "must_have"),
        "C36": (["N7", "N8"], "unverified_assessment"),
    }
    require(isinstance(value, list) and len(value) == 3, "Three negative cases")
    seen = set()
    for item in value:
        case = record(
            item,
            {
                "candidate_id",
                "need_ids",
                "required_exclusion",
                "expected_eligible",
                "rationale",
            },
            "negative case",
        )
        cid = case["candidate_id"]
        require(
            isinstance(cid, str) and cid in expected and cid not in seen,
            "Unknown/duplicate negative case",
        )
        seen.add(cid)
        nids, reason = expected[cid]
        require(
            case["need_ids"] == nids
            and case["required_exclusion"] == reason
            and case["expected_eligible"] is False,
            "Negative case mismatch",
        )
        require(nonempty(case["rationale"]), "Negative rationale required")
        require(
            all(reason in reasons(needs[nid], candidates[cid]) for nid in nids),
            "Expected hard exclusion not present",
        )
    require(seen == set(expected), "Missing negative case")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    args = parser.parse_args()
    frozen = args.dataset.read_bytes()
    require(
        hashlib.sha256(frozen).hexdigest() == FROZEN_HASH,
        "Frozen dataset SHA256 mismatch: STOP",
    )
    golden = args.golden.read_bytes()
    validate(json.loads(golden), json.loads(frozen))
    print("PASS: 288 structural pairs; 38 eligible labels; 250 excluded")
    print("PASS: nine FSP scenarios; two controlled comparisons; three negative cases")
    print(f"Frozen dataset SHA256: {FROZEN_HASH}")
    print(f"Proposed JSON SHA256: {hashlib.sha256(golden).hexdigest()}")
    print("PROPOSED; human review pending. Production ranking/metrics not executed.")


if __name__ == "__main__":
    main()
