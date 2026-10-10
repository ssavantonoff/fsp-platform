from collections.abc import Iterable
from contextlib import nullcontext
from dataclasses import dataclass
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import (
    EmployerNeed,
    EmployerNeedSkill,
    FspResultLevel,
    NeedSkillKind,
    NeedStatus,
    User,
)
from app.need_schemas import (
    EmployerCandidatePreview,
    FactorBreakdown,
    GradeBreakdown,
    MatchBreakdown,
    MatchesPage,
    NiceToHaveBreakdown,
)
from app.schemas import SkillOut
from app.services.candidate_assessments import (
    CandidateAssessment,
    CandidateAssessmentProvider,
    ProfileAssessmentProvider,
)
from app.services.fsp_rules import UNVERIFIED, FspSignal
from app.services.matching_rules import (
    CandidateMatchInput,
    FactorContribution,
    NeedCriteria,
    RankedCandidate,
    ScoringInput,
    eligible_candidate,
    score_professional_fit,
)
from app.services.matching_snapshot import SnapshotProfile, load_matching_snapshot
from app.services.profiles import employer_profile


@dataclass(frozen=True)
class EvaluatedCandidate(RankedCandidate):
    fsp: FspSignal

    @property
    def ranking_score(self) -> float:
        return 0.95 * self.fit.score + self.fsp.fsp_bonus


def rank_evaluations(values: Iterable[EvaluatedCandidate]) -> list[EvaluatedCandidate]:
    return sorted(
        values,
        key=lambda item: (
            -item.ranking_score,
            -item.fit.score,
            -item.eligible.normalized_assessment_score,
            item.eligible.candidate.candidate_id,
        ),
    )


class RankingFields(TypedDict):
    ranking_score: float
    fsp_verified: bool
    fsp_achievement_score: float
    fsp_bonus: float
    competition_count: int
    best_result_level: FspResultLevel | None


def ranking_fields(item: EvaluatedCandidate) -> RankingFields:
    signal = item.fsp
    return {
        "ranking_score": item.ranking_score,
        "fsp_verified": signal.fsp_verified,
        "fsp_achievement_score": signal.fsp_achievement_score,
        "fsp_bonus": signal.fsp_bonus,
        "competition_count": signal.competition_count,
        "best_result_level": signal.best_result_level,
    }


def load_need_criteria(db: Session, user: User, need_id: str) -> NeedCriteria:
    with db.no_autoflush:
        profile = employer_profile(db, user)
        rows = db.execute(
            select(
                EmployerNeed.id,
                EmployerNeed.employer_id,
                EmployerNeed.status,
                EmployerNeed.specialization,
                EmployerNeed.required_grade,
                EmployerNeed.target_experience_years,
                EmployerNeedSkill.skill_id,
                EmployerNeedSkill.kind,
            )
            .outerjoin(EmployerNeedSkill, EmployerNeedSkill.need_id == EmployerNeed.id)
            .where(EmployerNeed.id == need_id, EmployerNeed.employer_id == profile.id)
        ).all()
    if not rows:
        raise ApiError(404, "need_not_found", "Потребность не найдена.")
    first = rows[0]
    if first.status != NeedStatus.ACTIVE:
        raise ApiError(
            409, "need_state_conflict", "Подбор доступен для активной потребности."
        )
    return NeedCriteria(
        need_id=first.id,
        employer_id=first.employer_id,
        specialization=first.specialization,
        required_grade=first.required_grade,
        target_experience_years=first.target_experience_years,
        must_have_skill_ids=frozenset(
            row.skill_id for row in rows if row.kind == NeedSkillKind.MUST_HAVE
        ),
        nice_to_have_skill_ids=frozenset(
            row.skill_id for row in rows if row.kind == NeedSkillKind.NICE_TO_HAVE
        ),
    )


def match_need(
    db: Session,
    user: User,
    need_id: str,
    provider: CandidateAssessmentProvider,
    *,
    limit: int,
    offset: int,
) -> MatchesPage:
    with db.no_autoflush:
        criteria = load_need_criteria(db, user, need_id)
        snapshot = load_matching_snapshot(db, criteria)
        context = (
            provider.matching_snapshot(snapshot.assessments)
            if isinstance(provider, ProfileAssessmentProvider)
            else nullcontext()
        )
        with context:
            assessments = provider.get_assessments(
                [profile.candidate.candidate_id for profile in snapshot.profiles]
            )
        ranked = []
        profiles = {}
        for profile in snapshot.profiles:
            candidate = profile.candidate
            candidate_id = candidate.candidate_id
            evaluation = evaluate_candidate(
                criteria,
                candidate,
                assessments.get(candidate_id),
                fsp=snapshot.fsp_signals.get(candidate_id, FspSignal()),
            )
            if evaluation is None:
                continue
            ranked.append(evaluation)
            profiles[candidate_id] = (profile, profile.surname_initial)
        ordered = rank_evaluations(ranked)
        return MatchesPage(
            items=[
                _preview(
                    item,
                    *profiles[item.eligible.candidate.candidate_id],
                    criteria,
                    snapshot.catalog,
                )
                for item in ordered[offset : offset + limit]
            ],
            total=len(ordered),
            limit=limit,
            offset=offset,
        )


def evaluate_candidate(
    criteria: NeedCriteria,
    candidate: CandidateMatchInput,
    assessment: CandidateAssessment | None,
    *,
    fsp: FspSignal = UNVERIFIED,
) -> EvaluatedCandidate | None:
    eligible = eligible_candidate(criteria, candidate, assessment)
    if eligible is None:
        return None
    fit = score_professional_fit(
        ScoringInput(
            normalized_assessment_score=eligible.normalized_assessment_score,
            grade_fit=eligible.grade_fit,
            matched_nice_to_have=len(
                candidate.skill_ids & criteria.nice_to_have_skill_ids
            ),
            total_nice_to_have=len(criteria.nice_to_have_skill_ids),
            years_of_experience=candidate.years_of_experience,
            target_experience_years=criteria.target_experience_years,
        )
    )
    return EvaluatedCandidate(eligible=eligible, fit=fit, fsp=fsp)


def masked_display_name(first_name: str, surname_initial: str) -> str:
    return f"{first_name} {surname_initial}."


def match_breakdown(item: RankedCandidate, criteria: NeedCriteria) -> MatchBreakdown:
    fit = item.fit
    matched_nice = item.eligible.candidate.skill_ids & criteria.nice_to_have_skill_ids
    return MatchBreakdown(
        assessment=_factor(fit.assessment),
        grade=GradeBreakdown(
            score=fit.grade.score,
            max=fit.grade.max,
            active=fit.grade.active,
            exact_match=item.eligible.verified_grade == criteria.required_grade,
        ),
        nice_to_have=NiceToHaveBreakdown(
            score=fit.nice_to_have.score,
            max=fit.nice_to_have.max,
            active=fit.nice_to_have.active,
            matched=len(matched_nice),
            total=len(criteria.nice_to_have_skill_ids),
        ),
        experience=_factor(fit.experience),
    )


def _skills(ids: Iterable[str], catalog: dict[str, SkillOut]) -> list[SkillOut]:
    return sorted(
        (catalog[skill_id] for skill_id in ids),
        key=lambda skill: (skill.name, skill.id),
    )


def _factor(factor: FactorContribution) -> FactorBreakdown:
    return FactorBreakdown(score=factor.score, max=factor.max, active=factor.active)


def _preview(
    item: EvaluatedCandidate,
    profile: SnapshotProfile,
    surname_initial: str,
    criteria: NeedCriteria,
    catalog: dict[str, SkillOut],
) -> EmployerCandidatePreview:
    eligible = item.eligible
    candidate = eligible.candidate
    fit = item.fit
    matched_nice = candidate.skill_ids & criteria.nice_to_have_skill_ids
    return EmployerCandidatePreview(
        **ranking_fields(item),
        candidate_id=candidate.candidate_id,
        display_name=masked_display_name(profile.first_name, surname_initial),
        specialization=candidate.specialization,
        verified_grade=eligible.verified_grade,
        skills=sorted(
            (SkillOut(id=skill.id, name=skill.name) for skill in profile.skills),
            key=lambda skill: (skill.name, skill.id),
        ),
        years_of_experience=candidate.years_of_experience,
        normalized_assessment_score=eligible.normalized_assessment_score,
        assessment_verified_at=eligible.assessment_verified_at,
        professional_fit_score=fit.score,
        breakdown=match_breakdown(item, criteria),
        matched_must_have_skills=_skills(
            criteria.must_have_skill_ids & candidate.skill_ids, catalog
        ),
        matched_nice_to_have_skills=_skills(matched_nice, catalog),
        missing_nice_to_have_skills=_skills(
            criteria.nice_to_have_skill_ids - candidate.skill_ids, catalog
        ),
    )
