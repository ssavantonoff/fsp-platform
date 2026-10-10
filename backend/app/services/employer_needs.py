from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.errors import ApiError
from app.models import (
    EmployerNeed,
    EmployerNeedSkill,
    NeedSkillKind,
    NeedStatus,
    Skill,
    User,
    utcnow,
)
from app.need_schemas import NeedOut, NeedPage, NeedWrite
from app.schemas import SkillOut
from app.services.profiles import employer_profile

SKILL_FIELDS = {"must_have_skill_ids", "nice_to_have_skill_ids"}


def _skills(db: Session, data: NeedWrite) -> dict[str, Skill]:
    ids = data.must_have_skill_ids + data.nice_to_have_skill_ids
    skills = {
        skill.id: skill for skill in db.scalars(select(Skill).where(Skill.id.in_(ids)))
    }
    if len(skills) != len(ids):
        raise ApiError(422, "unknown_skill", "Выбран неизвестный навык.")
    return skills


def _commit(db: Session, need: EmployerNeed) -> NeedOut:
    try:
        db.flush()
        db.refresh(need)
        result = need_out(need)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "need_conflict", "Не удалось сохранить потребность."
        ) from exc
    return result


def create_need(db: Session, user: User, data: NeedWrite) -> NeedOut:
    profile = employer_profile(db, user)
    skills = _skills(db, data)
    need = EmployerNeed(employer_id=profile.id, **data.model_dump(exclude=SKILL_FIELDS))
    need.skill_requirements = [
        EmployerNeedSkill(skill=skills[skill_id], kind=kind)
        for ids, kind in (
            (data.must_have_skill_ids, NeedSkillKind.MUST_HAVE),
            (data.nice_to_have_skill_ids, NeedSkillKind.NICE_TO_HAVE),
        )
        for skill_id in ids
    ]
    db.add(need)
    return _commit(db, need)


def get_need(
    db: Session, user: User, need_id: str, *, for_update: bool = False
) -> EmployerNeed:
    profile = employer_profile(db, user)
    statement = select(EmployerNeed).where(
        EmployerNeed.id == need_id, EmployerNeed.employer_id == profile.id
    )
    if for_update:
        # selectin relationship loading runs after the owner-scoped parent lock.
        statement = statement.with_for_update().execution_options(
            populate_existing=True
        )
    else:
        # Keep the mutation lock/selectin path unchanged; GET reads one snapshot.
        statement = statement.options(
            joinedload(EmployerNeed.skill_requirements).joinedload(
                EmployerNeedSkill.skill
            )
        )
    need = db.scalars(statement).unique().one_or_none()
    if need is None:
        raise ApiError(404, "need_not_found", "Потребность не найдена.")
    return need


def update_need(db: Session, user: User, need_id: str, data: NeedWrite) -> NeedOut:
    need = get_need(db, user, need_id, for_update=True)
    if need.status == NeedStatus.CLOSED:
        raise ApiError(
            409, "need_state_conflict", "Закрытую потребность нельзя изменить."
        )
    skills = _skills(db, data)
    existing = {link.skill_id: link for link in need.skill_requirements}
    desired = {
        skill_id: kind
        for ids, kind in (
            (data.must_have_skill_ids, NeedSkillKind.MUST_HAVE),
            (data.nice_to_have_skill_ids, NeedSkillKind.NICE_TO_HAVE),
        )
        for skill_id in ids
    }
    for key, value in data.model_dump(exclude=SKILL_FIELDS).items():
        setattr(need, key, value)
    reconciled = []
    for skill_id, kind in desired.items():
        link = existing.get(skill_id)
        if link is None:
            link = EmployerNeedSkill(skill=skills[skill_id], kind=kind)
        else:
            link.kind = kind
        reconciled.append(link)
    need.skill_requirements = reconciled
    need.updated_at = utcnow()
    return _commit(db, need)


def _transition(
    db: Session, user: User, need_id: str, source: NeedStatus, target: NeedStatus
) -> NeedOut:
    need = get_need(db, user, need_id, for_update=True)
    if need.status != source:
        raise ApiError(
            409, "need_state_conflict", "Недопустимое изменение статуса потребности."
        )
    need.status = target
    need.updated_at = utcnow()
    return _commit(db, need)


def activate_need(db: Session, user: User, need_id: str) -> NeedOut:
    return _transition(db, user, need_id, NeedStatus.DRAFT, NeedStatus.ACTIVE)


def close_need(db: Session, user: User, need_id: str) -> NeedOut:
    return _transition(db, user, need_id, NeedStatus.ACTIVE, NeedStatus.CLOSED)


def list_needs(db: Session, user: User, *, limit: int, offset: int) -> NeedPage:
    profile = employer_profile(db, user)
    owned = EmployerNeed.employer_id == profile.id
    total = db.scalar(select(func.count()).select_from(EmployerNeed).where(owned)) or 0
    needs = db.scalars(
        select(EmployerNeed)
        .where(owned)
        .order_by(EmployerNeed.created_at.desc(), EmployerNeed.id.asc())
        .limit(limit)
        .offset(offset)
        .options(
            joinedload(EmployerNeed.skill_requirements).joinedload(
                EmployerNeedSkill.skill
            )
        )
    ).unique()
    return NeedPage(
        items=[need_out(need) for need in needs],
        total=total,
        limit=limit,
        offset=offset,
    )


def need_out(need: EmployerNeed) -> NeedOut:
    scalars = {
        key: getattr(need, key)
        for key in NeedOut.model_fields
        if key not in {"must_have_skills", "nice_to_have_skills"}
    }
    links = sorted(
        need.skill_requirements, key=lambda link: (link.skill.name, link.skill_id)
    )
    return NeedOut(
        **scalars,
        must_have_skills=[
            SkillOut.model_validate(link.skill)
            for link in links
            if link.kind == NeedSkillKind.MUST_HAVE
        ],
        nice_to_have_skills=[
            SkillOut.model_validate(link.skill)
            for link in links
            if link.kind == NeedSkillKind.NICE_TO_HAVE
        ],
    )
