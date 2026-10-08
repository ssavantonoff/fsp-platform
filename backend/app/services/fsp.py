from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.fsp_schemas import FspAchievementOut, FspStatus
from app.models import CandidateProfile, FspAchievement, FspResultLevel, User, utcnow
from app.services.fsp_registry import FspRegistryProvider, RegistryUnavailable
from app.services.fsp_rules import FspSignal, score_achievements


def _profile(db: Session, user: User, *, lock: bool = False) -> CandidateProfile:
    statement = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    if lock:
        statement = statement.with_for_update(of=CandidateProfile)
    profile = db.scalar(statement.execution_options(populate_existing=True))
    if profile is None:
        raise ApiError(404, "profile_not_found", "Создайте профиль кандидата.")
    return profile


def clear_verification(db: Session, profile: CandidateProfile) -> None:
    # Callers own the same CandidateProfile row lock, including normal profile edits.
    db.execute(delete(FspAchievement).where(FspAchievement.candidate_id == profile.id))
    profile.fsp_verified_id = None
    profile.fsp_verified_at = None
    profile.fsp_synced_at = None


def status(db: Session, user: User) -> FspStatus:
    # Identity, timestamps and child evidence share one SQL snapshot; GET is read-only.
    with db.no_autoflush:
        rows = db.execute(
            select(
                CandidateProfile.id,
                CandidateProfile.fsp_id,
                CandidateProfile.fsp_verified_id,
                CandidateProfile.fsp_verified_at,
                CandidateProfile.fsp_synced_at,
                FspAchievement,
            )
            .outerjoin(
                FspAchievement, FspAchievement.candidate_id == CandidateProfile.id
            )
            .where(CandidateProfile.user_id == user.id)
            .order_by(FspAchievement.competition_id, FspAchievement.external_id)
            .execution_options(populate_existing=True)
        ).all()
    if not rows:
        raise ApiError(404, "profile_not_found", "Создайте профиль кандидата.")
    first = rows[0]
    verified = first.fsp_verified_at is not None
    achievements = (
        [row.FspAchievement for row in rows if row.FspAchievement is not None]
        if verified
        else []
    )
    signal = (
        score_achievements((a.competition_id, a.result_level) for a in achievements)
        if verified
        else FspSignal()
    )
    return FspStatus(
        fsp_id=first.fsp_id,
        fsp_verified=verified,
        fsp_verified_at=first.fsp_verified_at,
        fsp_synced_at=first.fsp_synced_at,
        fsp_achievement_score=signal.fsp_achievement_score,
        fsp_bonus=signal.fsp_bonus,
        competition_count=signal.competition_count,
        best_result_level=signal.best_result_level,
        achievements=[FspAchievementOut.model_validate(a) for a in achievements],
    )


def sync(
    db: Session, user: User, provider: FspRegistryProvider, *, refresh: bool = False
) -> FspStatus:
    try:
        with db.no_autoflush:
            profile = _profile(db, user, lock=True)
            if refresh and profile.fsp_verified_at is None:
                raise ApiError(409, "fsp_not_verified", "Сначала подтвердите FSP ID.")
            record = provider.lookup(profile.fsp_id) if profile.fsp_id else None
            if record is None:
                raise ApiError(
                    404, "fsp_not_available", "FSP ID недоступен в mock-реестре."
                )
            # Validate provider uniqueness before replacing any stored evidence.
            if len({a.external_id for a in record.achievements}) != len(
                record.achievements
            ):
                raise RegistryUnavailable("Duplicate provider achievement IDs")
            verified_at = profile.fsp_verified_at
            clear_verification(db, profile)
            now = utcnow()
            profile.fsp_verified_id = profile.fsp_id
            profile.fsp_verified_at = verified_at or now
            profile.fsp_synced_at = now
            db.add_all(
                [
                    FspAchievement(candidate_id=profile.id, **item.model_dump())
                    for item in record.achievements
                ]
            )
            profile.updated_at = now
        # Flush first, build coherent response while still holding the parent lock.
        db.flush()
        result = status(db, user)
        db.commit()
        return result
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409,
            "fsp_verification_conflict",
            "Проверка FSP ID недоступна. Обновите страницу.",
        ) from exc
    except RegistryUnavailable as exc:
        db.rollback()
        raise ApiError(
            503, "fsp_provider_unavailable", "Mock-реестр ФСП временно недоступен."
        ) from exc
    except ApiError:
        db.rollback()
        raise


def unlink(db: Session, user: User) -> FspStatus:
    try:
        profile = _profile(db, user, lock=True)
        clear_verification(db, profile)
        profile.updated_at = utcnow()
        db.flush()
        result = status(db, user)
        db.commit()
        return result
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "fsp_verification_conflict", "Не удалось снять проверку FSP ID."
        ) from exc
    except ApiError:
        db.rollback()
        raise


def load_signals(db: Session, candidate_ids: Sequence[str]) -> dict[str, FspSignal]:
    # Keep private registry identity entirely outside Matching's public DTOs.
    signals: dict[str, FspSignal] = {}
    for offset in range(0, len(candidate_ids), 500):
        with db.no_autoflush:
            rows = db.execute(
                select(
                    CandidateProfile.id,
                    FspAchievement.competition_id,
                    FspAchievement.result_level,
                )
                .outerjoin(
                    FspAchievement, FspAchievement.candidate_id == CandidateProfile.id
                )
                .where(
                    CandidateProfile.id.in_(candidate_ids[offset : offset + 500]),
                    CandidateProfile.fsp_verified_at.is_not(None),
                )
                .order_by(CandidateProfile.id)
            ).all()
        evidence: dict[str, list[tuple[str, FspResultLevel]]] = {}
        for row in rows:
            evidence.setdefault(row.id, [])
            if row.competition_id is not None:
                evidence[row.id].append((row.competition_id, row.result_level))
        for candidate_id, items in evidence.items():
            signals[candidate_id] = score_achievements(items)
    return signals
