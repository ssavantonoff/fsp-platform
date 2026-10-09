"""P6-A structural checks, never production ranking or DB seeding."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.candidate_assessments import CandidateAssessmentProvider
from validate_matching_v2_dataset import (
    Dataset,
    OfflineAssessmentProvider,
    exclusion_reasons,
    load_dataset,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "docs/validation/matching-v2-dataset-v1.json"
DOCUMENT = DATASET.with_suffix(".md")
VALIDATOR = ROOT / "backend/validate_matching_v2_dataset.py"


def test_dataset_artifacts_and_structural_validator():
    assert DATASET.is_file(), "P6-A dataset JSON is required"
    assert DOCUMENT.is_file(), "P6-A methodology is required"
    assert VALIDATOR.is_file(), "P6-A independent validator is required"
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--dataset", str(DATASET)],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "8 Needs; 36 Candidates; 288 structural pairs" in result.stdout
    assert "Ranking/evaluation not executed" in result.stdout


@pytest.mark.parametrize(
    "path,value",
    [
        (("needs", 1, "id"), "N1"),
        (("candidates", 1, "id"), "C01"),
        (("needs", 0, "specialization"), "JAVA"),
        (("candidates", 0, "verified_grade"), "EXPERT"),
        (("candidates", 0, "normalized_assessment_score"), 101),
        (("candidates", 0, "normalized_assessment_score"), True),
        (("candidates", 0, "normalized_assessment_score"), 85.5),
        (("candidates", 0, "assessment_verified_at"), None),
        (("candidates", 0, "assessment_verified_at"), "2026-10-08T12:00:00"),
        (("candidates", 0, "self_declared_skills"), ["Java"]),
        (("candidates", 0, "self_declared_skills"), ["Python", "Python"]),
        (("needs", 0, "nice_to_have_skills"), ["Python"]),
        (("needs", 0, "salary_from"), "90000.001"),
        (("needs", 0, "salary_to"), "80000.00"),
        (("candidates", 0, "years_of_experience"), -1),
        (("candidates", 0, "personal_data_consent"), False),
        (("candidates", 1, "fsp", "state"), "ENTERED_UNVERIFIED"),
        (("candidates", 1, "fsp", "synced_at"), "2026-10-08T00:00:00Z"),
        (("candidates", 1, "fsp", "achievements", 0, "result_level"), "PARTICIPANT"),
        (("candidates", 1, "fsp", "fsp_id"), "MOCK-MISSING"),
        (("candidates", 0, "fsp", "fsp_id"), "MOCK-WINNER"),
        (("candidates", 2, "declared_grade"), "JUNIOR"),
        (("candidates", 14, "self_declared_skills"), ["React", "TypeScript"]),
        (("candidates", 26, "self_declared_skills"), ["Python", "SQL", "PostgreSQL"]),
        (("candidates", 35, "verified_grade"), "SENIOR"),
        (("needs", 2, "catalog_limited"), False),
        (("needs", 2, "position_title"), "Backend / Senior"),
        (("needs", 2, "required_grade"), "MIDDLE"),
        (("version",), True),
        (("synthetic",), 1),
        (("candidates", 0, "fsp", "state"), "ACCEPTED"),
        (("needs", 0, "must_have_skills"), []),
        (("candidates", 0, "fsp", "verified_at"), "2026-10-09T00:00:00Z"),
        (("candidates", 1, "fsp", "verified_at"), None),
        (("candidates", 0, "email"), "real-person@example.com"),
        (("candidates", 0, "ranking_score"), 99),
        (("candidates", 0, "fsp", "fsp_bonus"), 5),
    ],
)
def test_schema_rejects_invalid_or_out_of_scope_input(path, value):
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    target = data
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        Dataset.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("key", ["needs", "candidates"])
def test_exact_record_counts_are_enforced(key):
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    data[key].pop()
    with pytest.raises(ValidationError):
        Dataset.model_validate_json(json.dumps(data))


def test_duplicate_verified_fsp_identity_is_rejected():
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    data["candidates"][0]["fsp"] = data["candidates"][1]["fsp"]
    with pytest.raises(ValidationError, match="globally unique"):
        Dataset.model_validate_json(json.dumps(data))


def test_structural_eligibility_ignores_fsp_declared_grade_and_soft_factors():
    dataset = load_dataset()
    needs = {n.id: n for n in dataset.needs}
    candidates = {c.id: c for c in dataset.candidates}
    assert not exclusion_reasons(needs["N1"], candidates["C03"])
    assert "grade" in exclusion_reasons(needs["N2"], candidates["C03"])
    assert "must_have" in exclusion_reasons(needs["N4"], candidates["C15"])
    assert "must_have" in exclusion_reasons(needs["N7"], candidates["C27"])
    assert "unverified_assessment" in exclusion_reasons(needs["N8"], candidates["C36"])
    assert not exclusion_reasons(needs["N7"], candidates["C32"])
    assert "consent" in exclusion_reasons(needs["N7"], candidates["C34"])
    assert "specialization" in exclusion_reasons(needs["N7"], candidates["C01"])
    for left, right in (("C05", "C06"), ("C17", "C18")):
        for need in dataset.needs:
            assert exclusion_reasons(need, candidates[left]) == exclusion_reasons(
                need, candidates[right]
            )


def test_offline_assessment_provider_preserves_synthetic_canonical_evidence():
    before = DATASET.read_bytes()
    dataset = load_dataset()
    provider: CandidateAssessmentProvider = OfflineAssessmentProvider(dataset)
    values = provider.get_assessments(["C01", "C36", "C01", "missing"])
    assert set(values) == {"C01", "C36"}
    assert values["C01"].normalized_assessment_score == 100
    assert values["C36"].verified_grade is None
    assert values["C36"].normalized_assessment_score is None
    assert values["C36"].assessment_verified_at is None
    assert DATASET.read_bytes() == before


def test_emitted_json_schema_is_explicit_and_forbids_unknown_properties():
    schema = Dataset.model_json_schema()
    assert schema["additionalProperties"] is False
    for model in ("NeedRecord", "CandidateRecord", "FspRecord", "Evidence"):
        assert schema["$defs"][model]["additionalProperties"] is False
    assert schema["properties"]["needs"]["minItems"] == 8
    assert schema["properties"]["candidates"]["maxItems"] == 36
