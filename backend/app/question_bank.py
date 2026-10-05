import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AssessmentOption,
    AssessmentQuestion,
    Difficulty,
    Grade,
    Specialization,
)
from app.services.assessments import COMPETENCIES


class SeedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    version: int = Field(ge=1)
    supersedes: str | None = None
    grade: Grade
    competency: str
    difficulty: Difficulty
    prompt: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)


def load_bank() -> list[SeedQuestion]:
    content = json.loads(
        (Path(__file__).parent / "content/backend_questions.json").read_text()
    )
    questions = [SeedQuestion.model_validate(item) for item in content]
    if len({q.code for q in questions}) != len(questions):
        raise ValueError("Duplicate question codes")
    for question in questions:
        if question.competency not in COMPETENCIES[Specialization.BACKEND]:
            raise ValueError("Question bank competencies mismatch")
        if len(set(question.options)) != 4 or any(
            not text.strip() for text in question.options
        ):
            raise ValueError(f"Invalid options: {question.code}")
    return questions


def seed_questions(db: Session) -> None:
    existing = {q.code: q for q in db.scalars(select(AssessmentQuestion))}
    for item in load_bank():
        # An explicit replacement only deactivates the predecessor; history is kept.
        if item.supersedes and item.supersedes in existing:
            existing[item.supersedes].is_active = False
        question = existing.get(item.code)
        if question:
            same = (
                question.specialization == Specialization.BACKEND
                and question.grade == item.grade
                and question.competency == item.competency
                and question.difficulty == item.difficulty
                and question.prompt == item.prompt
                and question.version == item.version
                and {(o.text, o.is_correct) for o in question.options}
                == {(text, index == 0) for index, text in enumerate(item.options)}
            )
            if not same:
                raise ValueError(
                    f"Immutable question changed: {item.code}; use a new version/code"
                )
            # Deliberate deactivation is preserved on repeated seed runs.
            continue
        question = AssessmentQuestion(
            code=item.code,
            version=item.version,
            specialization=Specialization.BACKEND,
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
