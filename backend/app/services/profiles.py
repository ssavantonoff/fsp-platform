from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.errors import ApiError
from app.models import CandidateProfile, EmployerProfile, Skill, User, utcnow
from app.schemas import CandidateOut, CandidateWrite, EmployerWrite
from app.services import assessments, fsp


def candidate_profile(db: Session, user: User) -> CandidateProfile:
    profile = (
        db.scalars(
            select(CandidateProfile)
            .where(CandidateProfile.user_id == user.id)
            .options(joinedload(CandidateProfile.skills))
        )
        .unique()
        .one_or_none()
    )
    if profile is None:
        raise ApiError(404, "profile_not_found", "Создайте профиль кандидата.")
    return profile


def employer_profile(db: Session, user: User) -> EmployerProfile:
    profile = db.scalar(
        select(EmployerProfile).where(EmployerProfile.user_id == user.id)
    )
    if profile is None:
        raise ApiError(404, "profile_not_found", "Создайте профиль компании.")
    return profile


def save_candidate(
    db: Session, user: User, data: CandidateWrite, *, create: bool
) -> CandidateOut:
    profile = db.scalar(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if create and profile is not None:
        raise ApiError(409, "profile_exists", "Профиль уже создан.")
    if not create and profile is None:
        raise ApiError(404, "profile_not_found", "Сначала создайте профиль.")
    skills = list(
        db.scalars(
            select(Skill).where(Skill.id.in_(data.skill_ids)).order_by(Skill.name)
        )
    )
    if len(skills) != len(data.skill_ids):
        raise ApiError(422, "unknown_skill", "Выбран неизвестный навык.")
    if profile is None:
        profile = CandidateProfile(user_id=user.id, personal_data_consent=False)
        db.add(profile)
    if not create and data.specialization != profile.specialization:
        if assessments.expire_active(db, profile, utcnow()) is not None:
            raise ApiError(
                409,
                "assessment_in_progress",
                "Завершите активный тест перед сменой специализации.",
            )
        profile.specialization = data.specialization
        assessments.synchronize_verification(db, profile)
    if data.personal_data_consent and not profile.personal_data_consent:
        profile.personal_data_consent_at = utcnow()
    elif not data.personal_data_consent:
        profile.personal_data_consent_at = None
    # FSP evidence deletion can autoflush: align the consent pair before any SQL.
    profile.personal_data_consent = data.personal_data_consent
    if not create and data.fsp_id != profile.fsp_id:
        fsp.clear_verification(db, profile)
    for key, value in data.model_dump(exclude={"skill_ids"}).items():
        setattr(profile, key, value)
    profile.skills = skills
    profile.updated_at = utcnow()
    try:
        # Copy scalars and relationships while the write lock still protects them.
        # The DTO is returned only after commit succeeds, even with expiration on.
        db.flush()
        # Preserve database timestamp representation and relationship ordering
        # while the write lock still protects this version.
        db.refresh(profile)
        result = CandidateOut.model_validate(profile)
        commit_profile(db)
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "profile_conflict", "Профиль уже создан. Обновите страницу."
        ) from exc
    return result


def save_employer(
    db: Session, user: User, data: EmployerWrite, *, create: bool
) -> EmployerProfile:
    profile = db.scalar(
        select(EmployerProfile)
        .where(EmployerProfile.user_id == user.id)
        .with_for_update()
    )
    if create and profile is not None:
        raise ApiError(409, "profile_exists", "Профиль уже создан.")
    if not create and profile is None:
        raise ApiError(404, "profile_not_found", "Сначала создайте профиль.")
    if profile is None:
        profile = EmployerProfile(user_id=user.id)
        db.add(profile)
    for key, value in data.model_dump(mode="json").items():
        setattr(profile, key, value)
    profile.updated_at = utcnow()
    commit_profile(db)
    db.refresh(profile)
    return profile


def commit_profile(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "profile_conflict", "Профиль уже создан. Обновите страницу."
        ) from exc
