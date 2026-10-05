from fastapi import APIRouter, Depends

from app.dependencies import CandidateUser, Db, EmployerUser, require_trusted_origin
from app.schemas import CandidateOut, CandidateWrite, EmployerOut, EmployerWrite
from app.services import profiles

candidate = APIRouter(prefix="/candidate", tags=["candidate"])
employer = APIRouter(prefix="/employer", tags=["employer"])
mutations = [Depends(require_trusted_origin)]


@candidate.get("/profile", response_model=CandidateOut)
def get_candidate(user: CandidateUser, db: Db) -> object:
    return profiles.candidate_profile(db, user)


@candidate.post(
    "/profile", response_model=CandidateOut, status_code=201, dependencies=mutations
)
def create_candidate(data: CandidateWrite, user: CandidateUser, db: Db) -> object:
    return profiles.save_candidate(db, user, data, create=True)


@candidate.put("/profile", response_model=CandidateOut, dependencies=mutations)
def update_candidate(data: CandidateWrite, user: CandidateUser, db: Db) -> object:
    return profiles.save_candidate(db, user, data, create=False)


@employer.get("/profile", response_model=EmployerOut)
def get_employer(user: EmployerUser, db: Db) -> object:
    return profiles.employer_profile(db, user)


@employer.post(
    "/profile", response_model=EmployerOut, status_code=201, dependencies=mutations
)
def create_employer(data: EmployerWrite, user: EmployerUser, db: Db) -> object:
    return profiles.save_employer(db, user, data, create=True)


@employer.put("/profile", response_model=EmployerOut, dependencies=mutations)
def update_employer(data: EmployerWrite, user: EmployerUser, db: Db) -> object:
    return profiles.save_employer(db, user, data, create=False)
