import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessment_bank_config import (
    EXPANDED_BLUEPRINT,
    LEGACY_BACKEND_BLUEPRINT,
    SourceBlueprint,
)
from app.assessment_validation import (
    AssessmentValidationFinding,
    validate_source_bank,
    validate_source_banks,
)
from app.models import (
    AssessmentOption,
    AssessmentQuestion,
    Difficulty,
    Grade,
    Specialization,
)


class SeedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    version: int = Field(ge=1, strict=True)
    supersedes: str | None = None
    grade: Grade
    competency: str
    difficulty: Difficulty
    prompt: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)


@dataclass(frozen=True)
class BankSource:
    specialization: Specialization
    filename: str
    blueprint: SourceBlueprint = EXPANDED_BLUEPRINT
    reviewed_sha256: str | None = None
    review_reference: str | None = None

    @property
    def published(self) -> bool:
        return bool(
            self.reviewed_sha256
            and len(self.reviewed_sha256) == 64
            and all(c in "0123456789abcdef" for c in self.reviewed_sha256)
            and self.review_reference
            and self.review_reference.strip()
        )


# Publication is explicit. Merely adding a JSON file never enables a bank.
# The only approved source at A0 is the unchanged, previously published P5 bank.
BANK_SOURCES = (
    BankSource(
        Specialization.BACKEND,
        "backend_questions.json",
        LEGACY_BACKEND_BLUEPRINT,
        "76cda12d6358f14da84cce0ac584035ab189ae7a2f43e18d1e3cfed41276023c",
        "docs/assessment-bank-diversity.md#p5-b-disposition",
    ),
    BankSource(Specialization.FRONTEND, "frontend_questions.json"),
    BankSource(Specialization.DATA_ML, "data_ml_questions.json"),
)


def bank_sources() -> dict[Specialization, BankSource]:
    sources: dict[Specialization, BankSource] = {}
    for source in BANK_SOURCES:
        if (
            not isinstance(source.specialization, Specialization)
            or source.specialization in sources
            or (
                source.blueprint != EXPANDED_BLUEPRINT
                and not (
                    source.specialization == Specialization.BACKEND
                    and source.blueprint == LEGACY_BACKEND_BLUEPRINT
                )
            )
        ):
            raise ValueError("Invalid assessment bank registry") from None
        sources[source.specialization] = source
    return sources


def _structure_error(findings: list[AssessmentValidationFinding]) -> ValueError:
    details = "; ".join(
        f"{finding.category}"
        + (f" [{finding.code}]" if finding.code is not None else "")
        + f": {finding.context}"
        for finding in findings
    )
    return ValueError(f"Invalid assessment source structure: {details}")


def _load_source(source: BankSource) -> tuple[list[SeedQuestion], str]:
    try:
        raw = (Path(__file__).parent / "content" / source.filename).read_bytes()
        content = json.loads(raw)
        if not isinstance(content, list):
            raise ValueError("Invalid assessment source format") from None
        questions = [SeedQuestion.model_validate(item) for item in content]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError):
        raise ValueError("Invalid assessment source format") from None
    findings = validate_source_bank(
        questions, specialization=source.specialization, blueprint=source.blueprint
    )
    if findings:
        raise _structure_error(findings)
    return questions, sha256(raw).hexdigest()


def load_bank(
    specialization: Specialization = Specialization.BACKEND,
) -> list[SeedQuestion]:
    """Read a registered source for preflight; this does not publish it."""
    if not isinstance(specialization, Specialization):
        raise ValueError("Unsupported assessment specialization") from None
    source = bank_sources().get(specialization)
    if source is None:
        raise ValueError("Unregistered assessment bank") from None
    return _load_source(source)[0]


def load_banks() -> dict[Specialization, list[SeedQuestion]]:
    """Load all reviewed sources before any seed mutation."""
    banks = {}
    blueprints = {}
    for specialization, source in bank_sources().items():
        if not source.published:
            continue
        questions, digest = _load_source(source)
        if digest != source.reviewed_sha256:
            raise ValueError(
                "Assessment source differs from reviewed content"
            ) from None
        banks[specialization] = questions
        blueprints[specialization] = source.blueprint
    findings = validate_source_banks(banks, blueprints=blueprints)
    if findings:
        raise _structure_error(findings)
    return banks


def _same_question(
    question: AssessmentQuestion, item: SeedQuestion, specialization: Specialization
) -> bool:
    return (
        question.specialization == specialization
        and question.grade == item.grade
        and question.competency == item.competency
        and question.difficulty == item.difficulty
        and question.prompt == item.prompt
        and question.version == item.version
        and len(question.options) == 4
        and {(o.text, o.is_correct) for o in question.options}
        == {(text, index == 0) for index, text in enumerate(item.options)}
    )


def bank_is_published(db: Session, specialization: Specialization) -> bool:
    """New starts require a complete persisted copy of the reviewed source."""
    try:
        source = bank_sources().get(specialization)
        if source is None or not source.published:
            return False
        expected = load_banks().get(specialization)
        if expected is None:
            return False
    except ValueError:
        return False
    questions = {
        q.code: q
        for q in db.scalars(
            select(AssessmentQuestion).where(
                AssessmentQuestion.specialization == specialization,
                AssessmentQuestion.is_active.is_(True),
            )
        )
    }
    return len(questions) == len(expected) and all(
        item.code in questions
        and _same_question(questions[item.code], item, specialization)
        for item in expected
    )


def seed_questions(db: Session) -> None:
    banks = load_banks()
    existing = {q.code: q for q in db.scalars(select(AssessmentQuestion))}
    # Preflight every immutable row and lineage before changing the session.
    for specialization, questions in banks.items():
        for item in questions:
            question = existing.get(item.code)
            if question and not _same_question(question, item, specialization):
                raise ValueError(
                    f"Immutable question changed: {item.code}; use a new version/code"
                )
            predecessor = existing.get(item.supersedes) if item.supersedes else None
            if predecessor and predecessor.specialization != specialization:
                raise ValueError("Assessment predecessor belongs to another bank")
    for specialization, questions in banks.items():
        for item in questions:
            _seed_question(db, existing, specialization, item)


def _seed_question(
    db: Session,
    existing: dict[str, AssessmentQuestion],
    specialization: Specialization,
    item: SeedQuestion,
) -> None:
    # An explicit replacement only deactivates the predecessor; history is kept.
    if item.supersedes and item.supersedes in existing:
        existing[item.supersedes].is_active = False
    question = existing.get(item.code)
    if question:
        # Deliberate deactivation is preserved on repeated seed runs.
        return
    question = AssessmentQuestion(
        code=item.code,
        version=item.version,
        specialization=specialization,
        grade=item.grade,
        competency=item.competency,
        difficulty=item.difficulty,
        prompt=item.prompt,
        options=[
            AssessmentOption(text=text, is_correct=index == 0)
            for index, text in enumerate(item.options)
        ],
    )
    db.add(question)
