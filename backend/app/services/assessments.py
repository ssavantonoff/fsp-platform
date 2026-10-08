import random
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.assessment_schemas import (
    AttemptOut,
    AttemptSummary,
    AvailabilityOut,
    GradeAvailability,
    OptionOut,
    QuestionOut,
)
from app.errors import ApiError
from app.models import (
    AssessmentAttempt,
    AssessmentAttemptQuestion,
    AssessmentQuestion,
    AssessmentStatus,
    CandidateProfile,
    CompletionReason,
    Difficulty,
    Grade,
    Specialization,
    User,
    utcnow,
)
from app.schemas import CandidateOut

COMPETENCIES: dict[Specialization, tuple[str, ...]] = {
    Specialization.BACKEND: (
        "PROGRAMMING",
        "HTTP_API",
        "DATABASES",
        "ARCHITECTURE",
        "TESTING_SECURITY_DEBUGGING",
    ),
    Specialization.FRONTEND: (
        "JAVASCRIPT_TYPESCRIPT",
        "REACT_UI",
        "BROWSER_WEB",
        "STATE_DATA",
        "TESTING_PERFORMANCE_ACCESSIBILITY",
    ),
    Specialization.DATA_ML: (
        "PYTHON_DATA",
        "STATISTICS_ML",
        "DATA_PROCESSING_SQL",
        "MODELING_EVALUATION",
        "MLOPS_PRODUCTION",
    ),
}
GRADE_ORDER = {grade: index for index, grade in enumerate(Grade)}
BLUEPRINT = {Difficulty.BASIC: 1, Difficulty.APPLIED: 2, Difficulty.ADVANCED: 1}


class RandomSource(Protocol):
    def sample(
        self, population: list[AssessmentQuestion], k: int
    ) -> list[AssessmentQuestion]: ...
    def shuffle(self, x: list[str]) -> None: ...


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def lock_profile(db: Session, user: User) -> CandidateProfile:
    # Every mutation acquires this lock first, including specialization edits.
    profile = db.scalar(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if profile is None:
        raise ApiError(404, "profile_not_found", "Сначала создайте профиль кандидата.")
    return profile


def active_attempt(db: Session, profile: CandidateProfile) -> AssessmentAttempt | None:
    return db.scalar(
        select(AssessmentAttempt)
        .where(
            AssessmentAttempt.candidate_id == profile.id,
            AssessmentAttempt.status == AssessmentStatus.IN_PROGRESS,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def synchronize_verification(db: Session, profile: CandidateProfile) -> None:
    successful = list(
        db.scalars(
            select(AssessmentAttempt).where(
                AssessmentAttempt.candidate_id == profile.id,
                AssessmentAttempt.specialization == profile.specialization,
                AssessmentAttempt.status == AssessmentStatus.PASSED,
            )
        )
    )
    best = (
        max(
            successful,
            key=lambda a: (
                GRADE_ORDER[a.target_grade],
                aware(a.finished_at or a.expires_at),
            ),
            default=None,
        )
        if successful
        else None
    )
    profile.verified_grade = best.target_grade if best else None
    profile.normalized_assessment_score = (
        best.normalized_assessment_score if best else None
    )
    profile.assessment_verified_at = best.finished_at if best else None


def finalize(
    db: Session,
    profile: CandidateProfile,
    attempt: AssessmentAttempt,
    now: datetime,
    reason: CompletionReason,
) -> None:
    if attempt.status != AssessmentStatus.IN_PROGRESS:
        return
    counts = dict.fromkeys(COMPETENCIES[attempt.specialization], 0)
    for item in attempt.questions:
        if any(
            option.id == item.selected_option_id and option.is_correct
            for option in item.question.options
        ):
            counts[item.question.competency] += 1
    attempt.competency_scores = {key: value * 25 for key, value in counts.items()}
    attempt.normalized_assessment_score = sum(counts.values()) * 5
    passed = (
        attempt.normalized_assessment_score >= 70
        and min(attempt.competency_scores.values()) >= 50
    )
    attempt.status = AssessmentStatus.PASSED if passed else AssessmentStatus.FAILED
    attempt.completion_reason = reason
    # Timeout is completed at the deadline, even when discovered days later.
    attempt.finished_at = (
        aware(attempt.expires_at) if reason == CompletionReason.TIMEOUT else now
    )
    db.flush()
    if passed:
        synchronize_verification(db, profile)
    db.commit()


def expire_active(
    db: Session, profile: CandidateProfile, now: datetime
) -> AssessmentAttempt | None:
    active = active_attempt(db, profile)
    if active and aware(active.expires_at) <= now:
        finalize(db, profile, active, now, CompletionReason.TIMEOUT)
        # finalize commits; reacquire the lock before another mutation/check.
        db.refresh(profile, with_for_update=True)
        return active_attempt(db, profile)
    return active


def bank(
    db: Session, specialization: Specialization, grade: Grade
) -> list[AssessmentQuestion]:
    return list(
        db.scalars(
            select(AssessmentQuestion)
            .where(
                AssessmentQuestion.specialization == specialization,
                AssessmentQuestion.grade == grade,
                AssessmentQuestion.is_active.is_(True),
            )
            .order_by(AssessmentQuestion.code)
        )
    )


def bank_available(
    questions: list[AssessmentQuestion], specialization: Specialization
) -> bool:
    if any(
        len(q.options) != 4 or sum(o.is_correct for o in q.options) != 1
        for q in questions
    ):
        return False
    for competency in COMPETENCIES[specialization]:
        for difficulty, required in BLUEPRINT.items():
            if (
                sum(
                    q.competency == competency
                    and q.difficulty == difficulty
                    and len(q.options) == 4
                    and sum(o.is_correct for o in q.options) == 1
                    for q in questions
                )
                < required
            ):
                return False
    return True


def question_family(code: str) -> str:
    """The published bank uses one stable slot with a -vN suffix per lineage."""
    family, separator, version = code.rpartition("-v")
    return family if separator and version.isdecimal() else code


def historical_exposure(
    db: Session, profile: CandidateProfile, grade: Grade
) -> Counter[str]:
    counts: Counter[str] = Counter()
    rows = db.execute(
        select(AssessmentQuestion.code, func.count(AssessmentAttemptQuestion.id))
        .join(
            AssessmentAttemptQuestion,
            AssessmentAttemptQuestion.question_id == AssessmentQuestion.id,
        )
        .join(
            AssessmentAttempt,
            AssessmentAttempt.id == AssessmentAttemptQuestion.attempt_id,
        )
        .where(
            AssessmentAttempt.candidate_id == profile.id,
            AssessmentAttempt.specialization == profile.specialization,
            AssessmentAttempt.target_grade == grade,
        )
        .group_by(AssessmentQuestion.code)
    )
    # Membership counts even when unanswered or completed by timeout. Versions of
    # a published slot share exposure; neither history nor question rows are edited.
    for code, count in rows:
        counts[question_family(code)] += count
    return counts


def least_exposed_questions(
    questions: list[AssessmentQuestion],
    count: int,
    exposure: Counter[str],
    source: RandomSource,
) -> list[AssessmentQuestion]:
    levels: dict[int, list[AssessmentQuestion]] = {}
    for question in questions:
        levels.setdefault(exposure[question_family(question.code)], []).append(question)
    selected: list[AssessmentQuestion] = []
    for level in sorted(levels):
        pool = levels[level]
        selected.extend(source.sample(pool, min(count - len(selected), len(pool))))
        if len(selected) == count:
            break
    return selected


def next_available(attempt: AssessmentAttempt) -> datetime | None:
    if attempt.finished_at is None:
        return None
    return aware(attempt.finished_at) + timedelta(
        days=90 if attempt.status == AssessmentStatus.PASSED else 7
    )


def grade_availability(
    db: Session,
    profile: CandidateProfile,
    grade: Grade,
    active: AssessmentAttempt | None,
    user: User,
    now: datetime,
) -> GradeAvailability:
    reason = None
    available_at = None
    if not user.email_verified:
        reason = "EMAIL_NOT_VERIFIED"
    elif not profile.personal_data_consent:
        reason = "CONSENT_REQUIRED"
    elif active:
        reason = "IN_PROGRESS"
    elif (
        profile.verified_grade
        and GRADE_ORDER[grade] < GRADE_ORDER[profile.verified_grade]
    ):
        reason = "LOWER_THAN_VERIFIED"
    elif not bank_available(
        bank(db, profile.specialization, grade), profile.specialization
    ):
        reason = "UNAVAILABLE"
    else:
        latest = db.scalar(
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.candidate_id == profile.id,
                AssessmentAttempt.specialization == profile.specialization,
                AssessmentAttempt.target_grade == grade,
                AssessmentAttempt.status != AssessmentStatus.IN_PROGRESS,
            )
            .order_by(AssessmentAttempt.finished_at.desc())
            .limit(1)
        )
        if latest:
            deadline = next_available(latest)
            if deadline and deadline > now:
                reason, available_at = "COOLDOWN", deadline
    return GradeAvailability(
        grade=grade, available=reason is None, reason=reason, available_at=available_at
    )


def availability(db: Session, user: User) -> AvailabilityOut:
    profile = lock_profile(db, user)
    now = utcnow()
    active = expire_active(db, profile, now)
    return AvailabilityOut(
        specialization=profile.specialization,
        grades=[
            grade_availability(db, profile, grade, active, user, now) for grade in Grade
        ],
        active_attempt_id=active.id if active else None,
        server_now=now,
        verification=CandidateOut.model_validate(profile),
    )


def start(
    db: Session, user: User, grade: Grade, rng: RandomSource | None = None
) -> AttemptOut:
    profile = lock_profile(db, user)
    now = utcnow()
    active = expire_active(db, profile, now)
    allowed = grade_availability(db, profile, grade, active, user, now)
    errors = {
        "EMAIL_NOT_VERIFIED": (
            403,
            "email_not_verified",
            "Подтвердите email перед началом теста.",
        ),
        "CONSENT_REQUIRED": (
            403,
            "consent_required",
            "Дайте согласие на обработку персональных данных.",
        ),
        "IN_PROGRESS": (
            409,
            "assessment_in_progress",
            "У вас уже есть активная попытка.",
        ),
        "LOWER_THAN_VERIFIED": (
            409,
            "assessment_grade_not_allowed",
            "Уровень ниже уже подтверждённого недоступен.",
        ),
        "UNAVAILABLE": (
            409,
            "assessment_unavailable",
            "Для этой специализации пока нет банка вопросов.",
        ),
        "COOLDOWN": (409, "assessment_cooldown", "Повторная попытка пока недоступна."),
    }
    if allowed.reason:
        raise ApiError(*errors[allowed.reason])
    source = rng or random.SystemRandom()
    questions = bank(db, profile.specialization, grade)
    exposure = historical_exposure(db, profile, grade)
    selected = []
    for competency in COMPETENCIES[profile.specialization]:
        for difficulty, count in BLUEPRINT.items():
            selected.extend(
                least_exposed_questions(
                    [
                        q
                        for q in questions
                        if q.competency == competency and q.difficulty == difficulty
                    ],
                    count,
                    exposure,
                    source,
                )
            )
    question_ids = [q.id for q in selected]
    source.shuffle(question_ids)
    by_id = {q.id: q for q in selected}
    attempt = AssessmentAttempt(
        candidate_id=profile.id,
        specialization=profile.specialization,
        target_grade=grade,
        started_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    db.add(attempt)
    db.flush()
    for position, question_id in enumerate(question_ids, 1):
        options = [o.id for o in by_id[question_id].options]
        source.shuffle(options)
        db.add(
            AssessmentAttemptQuestion(
                attempt_id=attempt.id,
                question_id=question_id,
                position=position,
                option_order=options,
            )
        )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "assessment_in_progress", "У вас уже есть активная попытка."
        ) from exc
    db.refresh(attempt)
    return output(attempt, profile, now)


def own_attempt(
    db: Session, profile: CandidateProfile, attempt_id: str
) -> AssessmentAttempt:
    attempt = db.scalar(
        select(AssessmentAttempt)
        .where(
            AssessmentAttempt.id == attempt_id,
            AssessmentAttempt.candidate_id == profile.id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if attempt is None:
        raise ApiError(404, "assessment_not_found", "Попытка не найдена.")
    return attempt


def get_attempt(db: Session, user: User, attempt_id: str | None = None) -> AttemptOut:
    profile = lock_profile(db, user)
    now = utcnow()
    active = expire_active(db, profile, now)
    if attempt_id is None:
        if active is None:
            raise ApiError(404, "assessment_not_found", "Активной попытки нет.")
        attempt = active
    else:
        attempt = own_attempt(db, profile, attempt_id)
    return output(attempt, profile, now)


def save_answer(
    db: Session, user: User, attempt_id: str, question_id: str, option_id: str
) -> AttemptOut:
    profile = lock_profile(db, user)
    now = utcnow()
    # Check ownership before finalizing to avoid effects from a foreign identifier.
    attempt = own_attempt(db, profile, attempt_id)
    expire_active(db, profile, now)
    if attempt.status != AssessmentStatus.IN_PROGRESS:
        raise ApiError(409, "assessment_finished", "Тест уже завершён.")
    item = next((q for q in attempt.questions if q.id == question_id), None)
    if item is None:
        raise ApiError(422, "question_not_in_attempt", "Вопрос не принадлежит попытке.")
    if option_id not in item.option_order:
        raise ApiError(422, "option_not_in_question", "Вариант не принадлежит вопросу.")
    item.selected_option_id = option_id
    item.answered_at = now
    db.commit()
    return output(attempt, profile, now)


def submit(db: Session, user: User, attempt_id: str) -> AttemptOut:
    profile = lock_profile(db, user)
    attempt = own_attempt(db, profile, attempt_id)
    now = utcnow()
    if attempt.status == AssessmentStatus.IN_PROGRESS:
        reason = (
            CompletionReason.TIMEOUT
            if aware(attempt.expires_at) <= now
            else CompletionReason.SUBMITTED
        )
        finalize(db, profile, attempt, now, reason)
    return output(attempt, profile, now)


def summary(attempt: AssessmentAttempt) -> AttemptSummary:
    return AttemptSummary.model_validate(
        {
            **{
                key: getattr(attempt, key)
                for key in AttemptSummary.model_fields
                if key != "available_at"
            },
            "available_at": next_available(attempt),
        }
    )


def output(
    attempt: AssessmentAttempt, profile: CandidateProfile, now: datetime
) -> AttemptOut:
    questions = []
    # Finished responses reveal only aggregate results, never a question review.
    if attempt.status == AssessmentStatus.IN_PROGRESS:
        for item in attempt.questions:
            options = {o.id: o for o in item.question.options}
            questions.append(
                QuestionOut(
                    attempt_question_id=item.id,
                    question_id=item.question_id,
                    position=item.position,
                    competency=item.question.competency,
                    difficulty=item.question.difficulty,
                    prompt=item.question.prompt,
                    options=[
                        OptionOut(id=key, text=options[key].text)
                        for key in item.option_order
                    ],
                    selected_option_id=item.selected_option_id,
                )
            )
    return AttemptOut(
        **summary(attempt).model_dump(),
        server_now=now,
        questions=questions,
        verification=CandidateOut.model_validate(profile),
    )


def history(db: Session, user: User) -> list[AttemptSummary]:
    profile = lock_profile(db, user)
    expire_active(db, profile, utcnow())
    attempts = db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.candidate_id == profile.id)
        .order_by(AssessmentAttempt.started_at.desc())
    )
    return [summary(attempt) for attempt in attempts]
