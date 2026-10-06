from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import Db, EmployerUser, require_trusted_origin
from app.need_schemas import MatchesPage, NeedOut, NeedPage, NeedWrite
from app.services import employer_needs, matching
from app.services.candidate_assessments import (
    CandidateAssessmentProvider,
    ProfileAssessmentProvider,
)

router = APIRouter(prefix="/employer/needs", tags=["employer"])
mutations = [Depends(require_trusted_origin)]


def get_assessment_provider(db: Db) -> CandidateAssessmentProvider:
    return ProfileAssessmentProvider(db)


@router.get("", response_model=NeedPage)
def list_needs(
    user: EmployerUser,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NeedPage:
    return employer_needs.list_needs(db, user, limit=limit, offset=offset)


@router.post("", response_model=NeedOut, status_code=201, dependencies=mutations)
def create_need(data: NeedWrite, user: EmployerUser, db: Db) -> NeedOut:
    return employer_needs.need_out(employer_needs.create_need(db, user, data))


@router.get("/{need_id}", response_model=NeedOut)
def get_need(need_id: str, user: EmployerUser, db: Db) -> NeedOut:
    return employer_needs.need_out(employer_needs.get_need(db, user, need_id))


@router.put("/{need_id}", response_model=NeedOut, dependencies=mutations)
def update_need(need_id: str, data: NeedWrite, user: EmployerUser, db: Db) -> NeedOut:
    return employer_needs.need_out(employer_needs.update_need(db, user, need_id, data))


@router.post("/{need_id}/activate", response_model=NeedOut, dependencies=mutations)
def activate_need(need_id: str, user: EmployerUser, db: Db) -> NeedOut:
    return employer_needs.need_out(employer_needs.activate_need(db, user, need_id))


@router.post("/{need_id}/close", response_model=NeedOut, dependencies=mutations)
def close_need(need_id: str, user: EmployerUser, db: Db) -> NeedOut:
    return employer_needs.need_out(employer_needs.close_need(db, user, need_id))


@router.get("/{need_id}/matches", response_model=MatchesPage)
def get_matches(
    need_id: str,
    user: EmployerUser,
    db: Db,
    provider: Annotated[CandidateAssessmentProvider, Depends(get_assessment_provider)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MatchesPage:
    return matching.match_need(db, user, need_id, provider, limit=limit, offset=offset)
