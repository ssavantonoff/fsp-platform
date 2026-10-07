from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, load_only, selectinload

from app.errors import ApiError
from app.invitation_schemas import (
    CandidateContact,
    CandidateInvitationOut,
    CandidateInvitationPage,
    CandidateSnapshot,
    EmployerContact,
    EmployerInvitationOut,
    EmployerInvitationPage,
    InvitationSend,
    NeedSnapshot,
    StoredNeedSnapshot,
)
from app.models import (
    CandidateProfile,
    EmployerProfile,
    Invitation,
    InvitationStatus,
    NeedStatus,
    Skill,
    User,
    utcnow,
)
from app.schemas import SkillOut
from app.services import employer_needs, matching
from app.services.candidate_assessments import CandidateAssessmentProvider
from app.services.matching_rules import CandidateMatchInput


def _unavailable() -> ApiError:
    return ApiError(
        404, "candidate_not_available", "Кандидат недоступен для приглашения."
    )


def send(
    db: Session,
    user: User,
    need_id: str,
    data: InvitationSend,
    provider: CandidateAssessmentProvider,
) -> Invitation:
    try:
        with db.no_autoflush:
            need = employer_needs.get_need(db, user, need_id, for_update=True)
            if need.status != NeedStatus.ACTIVE:
                raise ApiError(
                    409,
                    "need_state_conflict",
                    "Приглашение доступно для активной потребности.",
                )
            candidate_row = db.execute(
                select(CandidateProfile, func.substr(CandidateProfile.last_name, 1, 1))
                .where(CandidateProfile.id == data.candidate_id)
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
                        Skill.id, raiseload=True
                    ),
                )
                .with_for_update(of=CandidateProfile)
                .execution_options(populate_existing=True)
            ).one_or_none()
            if candidate_row is None:
                raise _unavailable()
            candidate, surname_initial = candidate_row
            company = db.scalar(
                select(EmployerProfile)
                .where(
                    EmployerProfile.id == need.employer_id,
                    EmployerProfile.user_id == user.id,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if company is None:
                raise ApiError(404, "need_not_found", "Потребность не найдена.")
            criteria = matching.load_need_criteria(db, user, need.id)
            candidate_input = CandidateMatchInput(
                candidate_id=candidate.id,
                specialization=candidate.specialization,
                personal_data_consent=candidate.personal_data_consent,
                skill_ids=frozenset(skill.id for skill in candidate.skills),
                years_of_experience=candidate.years_of_experience,
            )
            assessment = provider.get_assessments([candidate.id]).get(candidate.id)
            evaluation = matching.evaluate_candidate(
                criteria, candidate_input, assessment
            )
            if evaluation is None:
                raise _unavailable()
            # Parent row locks protect profile/Need edits and their associations.
            # Share-lock the skill catalog too, so snapshot names cannot change.
            catalog = {
                row.id: SkillOut(id=row.id, name=row.name)
                for row in db.execute(
                    select(Skill.id, Skill.name)
                    .where(
                        Skill.id.in_(
                            criteria.must_have_skill_ids
                            | criteria.nice_to_have_skill_ids
                        )
                    )
                    .order_by(Skill.id)
                    .with_for_update(read=True)
                )
            }
            need_snapshot = StoredNeedSnapshot(
                need_id=need.id,
                position_title=need.position_title,
                specialization=need.specialization,
                required_grade=need.required_grade,
                target_experience_years=need.target_experience_years,
                salary_from=format(need.salary_from, ".2f"),
                salary_to=format(need.salary_to, ".2f"),
                description=need.description,
                additional_requirements=need.additional_requirements,
                must_have_skills=sorted(
                    [catalog[skill_id] for skill_id in criteria.must_have_skill_ids],
                    key=lambda skill: (skill.name, skill.id),
                ),
                nice_to_have_skills=sorted(
                    [catalog[skill_id] for skill_id in criteria.nice_to_have_skill_ids],
                    key=lambda skill: (skill.name, skill.id),
                ),
                company_name=company.company_name,
                contact_person_name=company.contact_person_name,
                website=company.website,
            )
            candidate_snapshot = CandidateSnapshot(
                candidate_id=candidate.id,
                display_name=matching.masked_display_name(
                    candidate.first_name, surname_initial
                ),
                specialization=candidate.specialization,
                verified_grade=evaluation.eligible.verified_grade,
                normalized_assessment_score=evaluation.eligible.normalized_assessment_score,
                assessment_verified_at=evaluation.eligible.assessment_verified_at,
                professional_fit_score=evaluation.fit.score,
                breakdown=matching.match_breakdown(evaluation, criteria),
            )
            invitation = Invitation(
                need_id=need.id,
                employer_id=need.employer_id,
                candidate_id=candidate.id,
                message=data.message,
                need_snapshot=need_snapshot.model_dump(mode="json"),
                candidate_snapshot=candidate_snapshot.model_dump(mode="json"),
                sent_at=utcnow(),
            )
            db.add(invitation)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "invitation_conflict", "Приглашение уже существует."
        ) from exc
    except ApiError:
        db.rollback()
        raise
    return invitation


def _common(invitation: Invitation) -> dict[str, Any]:
    return {
        "id": invitation.id,
        "need_id": invitation.need_id,
        "status": invitation.status,
        "message": invitation.message,
        "need_snapshot": NeedSnapshot.model_validate(invitation.need_snapshot),
        "sent_at": invitation.sent_at,
        "viewed_at": invitation.viewed_at,
        "responded_at": invitation.responded_at,
        "withdrawn_at": invitation.withdrawn_at,
    }


def employer_out(db: Session, invitation: Invitation) -> EmployerInvitationOut:
    fields = _common(invitation)
    fields["candidate_snapshot"] = CandidateSnapshot.model_validate(
        invitation.candidate_snapshot
    )
    if invitation.status == InvitationStatus.ACCEPTED:
        row = db.execute(
            select(CandidateProfile.first_name, CandidateProfile.last_name, User.email)
            .join(User, User.id == CandidateProfile.user_id)
            .where(CandidateProfile.id == invitation.candidate_id)
        ).one()
        fields["candidate_contact"] = CandidateContact(
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
        )
    return EmployerInvitationOut(**fields)


def candidate_out(db: Session, invitation: Invitation) -> CandidateInvitationOut:
    fields = _common(invitation)
    if invitation.status == InvitationStatus.ACCEPTED:
        row = db.execute(
            select(
                EmployerProfile.company_name,
                EmployerProfile.contact_person_name,
                User.email,
                EmployerProfile.website,
            )
            .join(User, User.id == EmployerProfile.user_id)
            .where(EmployerProfile.id == invitation.employer_id)
        ).one()
        fields["employer_contact"] = EmployerContact(
            company_name=row.company_name,
            contact_person_name=row.contact_person_name,
            email=row.email,
            website=row.website,
        )
    return CandidateInvitationOut(**fields)


def _owned(user: User, *, employer: bool) -> Select[tuple[Invitation]]:
    if employer:
        owner_id = select(EmployerProfile.id).where(EmployerProfile.user_id == user.id)
        owned = Invitation.employer_id == owner_id.scalar_subquery()
    else:
        owner_id = select(CandidateProfile.id).where(
            CandidateProfile.user_id == user.id
        )
        owned = Invitation.candidate_id == owner_id.scalar_subquery()
    return select(Invitation).where(owned)


def get(
    db: Session,
    user: User,
    invitation_id: str,
    *,
    employer: bool,
    for_update: bool = False,
) -> Invitation:
    statement = _owned(user, employer=employer).where(Invitation.id == invitation_id)
    if for_update:
        statement = statement.with_for_update(of=Invitation)
    with db.no_autoflush:
        invitation = db.scalar(statement.execution_options(populate_existing=True))
    if invitation is None:
        raise ApiError(404, "invitation_not_found", "Приглашение не найдено.")
    return invitation


def list_employer(
    db: Session,
    user: User,
    need_id: str,
    *,
    limit: int,
    offset: int,
) -> EmployerInvitationPage:
    with db.no_autoflush:
        need = employer_needs.get_need(db, user, need_id)
        statement = _owned(user, employer=True).where(Invitation.need_id == need.id)
        total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        rows = db.scalars(
            statement.order_by(Invitation.sent_at.desc(), Invitation.id)
            .limit(limit)
            .offset(offset)
            .execution_options(populate_existing=True)
        )
        return EmployerInvitationPage(
            items=[employer_out(db, row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )


def list_candidate(
    db: Session,
    user: User,
    *,
    limit: int,
    offset: int,
) -> CandidateInvitationPage:
    with db.no_autoflush:
        statement = _owned(user, employer=False)
        total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        rows = db.scalars(
            statement.order_by(Invitation.sent_at.desc(), Invitation.id)
            .limit(limit)
            .offset(offset)
            .execution_options(populate_existing=True)
        )
        return CandidateInvitationPage(
            items=[candidate_out(db, row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )


def transition(
    db: Session,
    user: User,
    invitation_id: str,
    target: InvitationStatus,
) -> Invitation:
    if target == InvitationStatus.SENT:
        raise ValueError("SENT is not an invitation action")
    try:
        invitation = get(
            db,
            user,
            invitation_id,
            employer=target == InvitationStatus.WITHDRAWN,
            for_update=True,
        )
        if invitation.status == target:
            db.commit()
            return invitation
        if invitation.status not in {InvitationStatus.SENT, InvitationStatus.VIEWED}:
            raise ApiError(
                409,
                "invitation_state_conflict",
                "Недопустимое изменение статуса приглашения.",
            )
        invitation.status = target
        now = utcnow()
        if target == InvitationStatus.VIEWED:
            invitation.viewed_at = now
        elif target == InvitationStatus.WITHDRAWN:
            invitation.withdrawn_at = now
        else:
            invitation.responded_at = now
        invitation.updated_at = now
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "invitation_state_conflict", "Не удалось изменить статус приглашения."
        ) from exc
    except ApiError:
        db.rollback()
        raise
    return invitation
