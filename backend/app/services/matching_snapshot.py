"""One statement snapshot for Matching inputs, without ORM state or row locks."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import String, cast, func, literal, null, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    CandidateProfile,
    FspAchievement,
    FspResultLevel,
    Grade,
    Skill,
    Specialization,
    candidate_skills,
)
from app.schemas import SkillOut
from app.services.candidate_assessments import CandidateAssessment
from app.services.fsp_rules import FspSignal, score_achievements
from app.services.matching_rules import CandidateMatchInput, NeedCriteria


@dataclass(frozen=True)
class SnapshotProfile:
    candidate: CandidateMatchInput
    first_name: str
    surname_initial: str
    skills: tuple[SkillOut, ...]


@dataclass(frozen=True)
class MatchingSnapshot:
    profiles: tuple[SnapshotProfile, ...]
    assessments: dict[str, CandidateAssessment]
    fsp_signals: dict[str, FspSignal]
    catalog: dict[str, SkillOut]


def load_matching_snapshot(db: Session, criteria: NeedCriteria) -> MatchingSnapshot:
    # Typed NULLs keep UNION portable on PostgreSQL and SQLite. Child streams
    # grow additively; joining skills to achievements would multiply the rows.
    fields: dict[str, ColumnElement[Any]] = {
        "candidate_id": CandidateProfile.id.label("candidate_id"),
        "first_name": CandidateProfile.first_name.label("first_name"),
        "surname_initial": cast(func.substr(CandidateProfile.last_name, 1, 1), String),
        "specialization": cast(CandidateProfile.specialization, String),
        "consent": CandidateProfile.personal_data_consent.label("consent"),
        "experience": CandidateProfile.years_of_experience.label("experience"),
        "grade": cast(CandidateProfile.verified_grade, String),
        "score": CandidateProfile.normalized_assessment_score.label("score"),
        "verified_at": CandidateProfile.assessment_verified_at.label("verified_at"),
        "skill_id": cast(null(), String),
        "skill_name": cast(null(), String),
        "competition_id": cast(null(), String),
        "result_level": cast(null(), String),
    }

    def stream(kind: str, values: dict[str, Any]) -> Select[Any]:
        return select(
            literal(kind).label("kind"),
            *(
                values.get(name, cast(null(), column.type)).label(name)
                for name, column in fields.items()
            ),
        )

    statement = union_all(
        stream("profile", fields),
        stream(
            "skill",
            {
                "candidate_id": candidate_skills.c.candidate_id,
                "skill_id": Skill.id,
                "skill_name": Skill.name,
            },
        ).select_from(candidate_skills.join(Skill)),
        stream(
            "fsp",
            {
                "candidate_id": CandidateProfile.id,
                "competition_id": FspAchievement.competition_id,
                "result_level": cast(FspAchievement.result_level, String),
            },
        )
        .select_from(CandidateProfile)
        .outerjoin(FspAchievement, FspAchievement.candidate_id == CandidateProfile.id)
        .where(CandidateProfile.fsp_verified_at.is_not(None)),
        stream("catalog", {"skill_id": Skill.id, "skill_name": Skill.name}).where(
            Skill.id.in_(criteria.must_have_skill_ids | criteria.nice_to_have_skill_ids)
        ),
    )
    with db.no_autoflush:
        rows = db.execute(statement).all()
    profiles = {}
    skills: dict[str, list[SkillOut]] = {}
    assessments = {}
    evidence: dict[str, list[tuple[str, FspResultLevel]]] = {}
    catalog = {}
    # UNION does not guarantee branch ordering; materialize before assembling.
    for row in rows:
        if row.kind == "profile":
            profiles[row.candidate_id] = row
            assessments[row.candidate_id] = CandidateAssessment(
                row.candidate_id,
                Grade(row.grade) if row.grade is not None else None,
                row.score,
                row.verified_at,
            )
        elif row.kind == "skill":
            skills.setdefault(row.candidate_id, []).append(
                SkillOut(id=row.skill_id, name=row.skill_name)
            )
        elif row.kind == "fsp":
            values = evidence.setdefault(row.candidate_id, [])
            if row.competition_id is not None:
                values.append((row.competition_id, FspResultLevel(row.result_level)))
        elif row.kind == "catalog":
            catalog[row.skill_id] = SkillOut(id=row.skill_id, name=row.skill_name)
    return MatchingSnapshot(
        profiles=tuple(
            SnapshotProfile(
                candidate=CandidateMatchInput(
                    row.candidate_id,
                    Specialization(row.specialization),
                    row.consent,
                    frozenset(skill.id for skill in skills.get(row.candidate_id, [])),
                    row.experience,
                ),
                first_name=row.first_name,
                surname_initial=row.surname_initial,
                skills=tuple(skills.get(row.candidate_id, [])),
            )
            for _, row in sorted(profiles.items())
        ),
        assessments=assessments,
        fsp_signals={
            key: score_achievements(values) for key, values in evidence.items()
        },
        catalog=catalog,
    )
