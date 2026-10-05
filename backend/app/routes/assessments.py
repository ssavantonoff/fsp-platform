from fastapi import APIRouter, Depends

from app.assessment_schemas import (
    AnswerWrite,
    AssessmentStart,
    AttemptOut,
    AttemptSummary,
    AvailabilityOut,
)
from app.dependencies import CandidateUser, Db, require_trusted_origin
from app.services import assessments

router = APIRouter(prefix="/candidate/assessments", tags=["assessments"])
mutations = [Depends(require_trusted_origin)]


@router.get("/availability", response_model=AvailabilityOut)
def availability(user: CandidateUser, db: Db) -> object:
    return assessments.availability(db, user)


@router.post("", response_model=AttemptOut, status_code=201, dependencies=mutations)
def start(data: AssessmentStart, user: CandidateUser, db: Db) -> object:
    return assessments.start(db, user, data.target_grade)


@router.get("/current", response_model=AttemptOut)
def current(user: CandidateUser, db: Db) -> object:
    return assessments.get_attempt(db, user)


@router.get("/history", response_model=list[AttemptSummary])
def history(user: CandidateUser, db: Db) -> object:
    return assessments.history(db, user)


@router.get("/{attempt_id}", response_model=AttemptOut)
def get_attempt(attempt_id: str, user: CandidateUser, db: Db) -> object:
    return assessments.get_attempt(db, user, attempt_id)


@router.put(
    "/{attempt_id}/answers/{attempt_question_id}",
    response_model=AttemptOut,
    dependencies=mutations,
)
def answer(
    attempt_id: str,
    attempt_question_id: str,
    data: AnswerWrite,
    user: CandidateUser,
    db: Db,
) -> object:
    return assessments.save_answer(
        db, user, attempt_id, attempt_question_id, data.selected_option_id
    )


@router.post("/{attempt_id}/submit", response_model=AttemptOut, dependencies=mutations)
def submit(attempt_id: str, user: CandidateUser, db: Db) -> object:
    return assessments.submit(db, user, attempt_id)
