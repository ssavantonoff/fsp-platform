from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from app.models import Difficulty, Grade, Specialization
from app.services.assessments import COMPETENCIES

if TYPE_CHECKING:
    from app.question_bank import SeedQuestion


class AssessmentValidationCategory(StrEnum):
    INVALID_TOTAL = "INVALID_TOTAL"
    INVALID_GRADE_COUNT = "INVALID_GRADE_COUNT"
    INVALID_BUCKET_COUNT = "INVALID_BUCKET_COUNT"
    BLANK_CODE = "BLANK_CODE"
    DUPLICATE_CODE = "DUPLICATE_CODE"
    BLANK_PROMPT = "BLANK_PROMPT"
    INVALID_OPTIONS = "INVALID_OPTIONS"
    DUPLICATE_OPTION = "DUPLICATE_OPTION"
    INVALID_GRADE = "INVALID_GRADE"
    INVALID_DIFFICULTY = "INVALID_DIFFICULTY"
    INVALID_COMPETENCY = "INVALID_COMPETENCY"
    INVALID_VERSION = "INVALID_VERSION"
    INVALID_SUPERSEDES = "INVALID_SUPERSEDES"
    SUPERSEDES_CYCLE = "SUPERSEDES_CYCLE"


@dataclass(frozen=True)
class AssessmentValidationFinding:
    category: AssessmentValidationCategory
    code: str | None
    context: str


def validate_source_bank(
    questions: Sequence[SeedQuestion],
) -> list[AssessmentValidationFinding]:
    """Validate parsed Backend source structure without reading or changing state."""
    category = AssessmentValidationCategory
    competencies = COMPETENCIES[Specialization.BACKEND]
    grades = tuple(Grade)
    difficulties = tuple(Difficulty)
    expected_mix = {
        Difficulty.BASIC: 1,
        Difficulty.APPLIED: 3,
        Difficulty.ADVANCED: 1,
    }
    grade_counts: Counter[Grade] = Counter()
    bucket_counts: Counter[tuple[Grade, str, Difficulty]] = Counter()
    code_counts = Counter(q.code for q in questions)
    seen_codes: set[str] = set()
    record_findings = []

    for question in questions:
        code = question.code if question.code.strip() else None
        if code is None:
            record_findings.append(
                AssessmentValidationFinding(category.BLANK_CODE, None, "Code is blank.")
            )
        if question.code in seen_codes:
            record_findings.append(
                AssessmentValidationFinding(
                    category.DUPLICATE_CODE, code, "Source code is duplicated."
                )
            )
        seen_codes.add(question.code)
        if not question.prompt.strip():
            record_findings.append(
                AssessmentValidationFinding(
                    category.BLANK_PROMPT, code, "Prompt is blank."
                )
            )
        if len(question.options) != 4 or any(
            not option.strip() for option in question.options
        ):
            record_findings.append(
                AssessmentValidationFinding(
                    category.INVALID_OPTIONS, code, "Expected four nonblank options."
                )
            )
        compared_options = [" ".join(option.split()) for option in question.options]
        if len(set(compared_options)) != len(compared_options):
            record_findings.append(
                AssessmentValidationFinding(
                    category.DUPLICATE_OPTION,
                    code,
                    "Options are not distinct after whitespace comparison.",
                )
            )

        # Model-constructed defensive inputs may contain unhashable invalid metadata.
        valid_grade = isinstance(question.grade, str) and question.grade in grades
        valid_difficulty = (
            isinstance(question.difficulty, str) and question.difficulty in difficulties
        )
        valid_competency = (
            isinstance(question.competency, str) and question.competency in competencies
        )
        valid_version = type(question.version) is int and question.version >= 1
        for valid, failure, context in (
            (
                valid_grade,
                category.INVALID_GRADE,
                "Grade is not a supported enum value.",
            ),
            (
                valid_difficulty,
                category.INVALID_DIFFICULTY,
                "Difficulty is not a supported enum value.",
            ),
            (
                valid_competency,
                category.INVALID_COMPETENCY,
                "Competency is not a Backend competency.",
            ),
            (
                valid_version,
                category.INVALID_VERSION,
                "Version must be an integer >=1.",
            ),
        ):
            if not valid:
                record_findings.append(
                    AssessmentValidationFinding(failure, code, context)
                )
        if valid_grade:
            grade_counts[question.grade] += 1
        if valid_grade and valid_difficulty and valid_competency and valid_version:
            bucket_counts[question.grade, question.competency, question.difficulty] += 1

    findings = []
    if len(questions) != 75:
        findings.append(
            AssessmentValidationFinding(
                category.INVALID_TOTAL,
                None,
                f"Expected 75 source records; found {len(questions)}.",
            )
        )
    for grade in grades:
        if grade_counts[grade] != 25:
            findings.append(
                AssessmentValidationFinding(
                    category.INVALID_GRADE_COUNT,
                    None,
                    f"{grade}: expected 25 source records; "
                    f"found {grade_counts[grade]}.",
                )
            )
    for grade in grades:
        for competency in competencies:
            for difficulty in difficulties:
                expected = expected_mix[difficulty]
                actual = bucket_counts[grade, competency, difficulty]
                if actual != expected:
                    findings.append(
                        AssessmentValidationFinding(
                            category.INVALID_BUCKET_COUNT,
                            None,
                            f"{grade}/{competency}/{difficulty}: expected "
                            f"{expected} source record(s); found {actual}.",
                        )
                    )
    findings.extend(record_findings)
    findings.extend(_supersedes_findings(questions, code_counts))
    return findings


def _supersedes_findings(
    questions: Sequence[SeedQuestion], code_counts: Counter[str]
) -> list[AssessmentValidationFinding]:
    category = AssessmentValidationCategory
    # Duplicate/blank source identities cannot form unambiguous graph nodes.
    unique = {
        q.code: q for q in questions if q.code.strip() and code_counts[q.code] == 1
    }
    findings = []
    edges: dict[str, str] = {}
    owners: dict[str, str] = {}
    for code, question in unique.items():
        predecessor = question.supersedes
        if predecessor is None:
            continue
        if not predecessor.strip() or predecessor == code:
            findings.append(
                AssessmentValidationFinding(
                    category.INVALID_SUPERSEDES,
                    code,
                    "Predecessor must be nonblank and different from the source code.",
                )
            )
            continue
        if predecessor in owners:
            findings.append(
                AssessmentValidationFinding(
                    category.INVALID_SUPERSEDES,
                    code,
                    f"Predecessor {predecessor} is already claimed "
                    f"by {owners[predecessor]}.",
                )
            )
        else:
            owners[predecessor] = code
        edges[code] = predecessor

    visited: set[str] = set()
    for start in unique:
        path: list[str] = []
        positions: dict[str, int] = {}
        node = start
        # Missing historical predecessors and nodes without edges end the traversal.
        while node in edges and node not in visited:
            if node in positions:
                cycle = path[positions[node] :]
                findings.append(
                    AssessmentValidationFinding(
                        category.SUPERSEDES_CYCLE,
                        node,
                        f"Cycle among source codes: {', '.join(cycle)}.",
                    )
                )
                break
            positions[node] = len(path)
            path.append(node)
            node = edges[node]
        visited.update(path)
    return findings
