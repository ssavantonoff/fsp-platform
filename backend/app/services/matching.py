from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, load_only, selectinload

from app.errors import ApiError
from app.models import (
    CandidateProfile,
    EmployerNeed,
    EmployerNeedSkill,
    NeedSkillKind,
    NeedStatus,
    Skill,
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
)
from app.services.matching_rules import (
    CandidateMatchInput,
    FactorContribution,
    NeedCriteria,
    RankedCandidate,
    ScoringInput,
    eligible_candidate,
    rank_candidates,
    score_professional_fit,
)
from app.services.profiles import employer_profile


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
        pool = db.execute(
            select(CandidateProfile, func.substr(CandidateProfile.last_name, 1, 1))
            .options(
                load_only(
                    CandidateProfile.id,
                    CandidateProfile.first_name,
                    CandidateProfile.specialization,
                    CandidateProfile.personal_data_consent,
                    CandidateProfile.years_of_experience,
                    raiseload=True,
                ),
                selectinload(CandidateProfile.skills).load_only(
                    Skill.id, Skill.name, raiseload=True
                ),
            )
            .order_by(CandidateProfile.id)
        ).all()
        assessments = provider.get_assessments([profile.id for profile, _ in pool])
        catalog = {
            row.id: SkillOut(id=row.id, name=row.name)
            for row in db.execute(
                select(Skill.id, Skill.name).where(
                    Skill.id.in_(
                        criteria.must_have_skill_ids | criteria.nice_to_have_skill_ids
                    )
                )
            )
        }
        ranked = []
        profiles = {}
        for profile, surname_initial in pool:
            candidate = CandidateMatchInput(
                candidate_id=profile.id,
                specialization=profile.specialization,
                personal_data_consent=profile.personal_data_consent,
                skill_ids=frozenset(skill.id for skill in profile.skills),
                years_of_experience=profile.years_of_experience,
            )
            evaluation = evaluate_candidate(
                criteria, candidate, assessments.get(profile.id)
            )
            if evaluation is None:
                continue
            ranked.append(evaluation)
            profiles[profile.id] = (profile, surname_initial)
        ordered = rank_candidates(ranked)
        return MatchesPage(
            items=[
                _preview(
                    item,
                    *profiles[item.eligible.candidate.candidate_id],
                    criteria,
                    catalog,
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
) -> RankedCandidate | None:
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
    return RankedCandidate(eligible=eligible, fit=fit)


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
    item: RankedCandidate,
    profile: CandidateProfile,
    surname_initial: str,
    criteria: NeedCriteria,
    catalog: dict[str, SkillOut],
) -> EmployerCandidatePreview:
    eligible = item.eligible
    candidate = eligible.candidate
    fit = item.fit
    matched_nice = candidate.skill_ids & criteria.nice_to_have_skill_ids
    return EmployerCandidatePreview(
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
