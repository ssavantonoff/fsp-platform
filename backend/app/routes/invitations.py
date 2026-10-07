from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import CandidateUser, Db, EmployerUser, require_trusted_origin
from app.invitation_schemas import (
    CandidateInvitationOut,
    CandidateInvitationPage,
    EmployerInvitationOut,
    EmployerInvitationPage,
    InvitationSend,
)
from app.models import InvitationStatus
from app.routes.employer_needs import get_assessment_provider
from app.services import invitations
from app.services.candidate_assessments import CandidateAssessmentProvider

router = APIRouter(tags=["invitations"])
mutations = [Depends(require_trusted_origin)]


@router.post(
    "/employer/needs/{need_id}/invitations",
    response_model=EmployerInvitationOut,
    response_model_exclude_unset=True,
    status_code=201,
    dependencies=mutations,
)
def send_invitation(
    need_id: str,
    data: InvitationSend,
    user: EmployerUser,
    db: Db,
    provider: Annotated[CandidateAssessmentProvider, Depends(get_assessment_provider)],
) -> EmployerInvitationOut:
    return invitations.employer_out(
        db, invitations.send(db, user, need_id, data, provider)
    )


@router.get(
    "/employer/needs/{need_id}/invitations",
    response_model=EmployerInvitationPage,
    response_model_exclude_unset=True,
)
def list_employer_invitations(
    need_id: str,
    user: EmployerUser,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EmployerInvitationPage:
    return invitations.list_employer(db, user, need_id, limit=limit, offset=offset)


@router.get(
    "/employer/invitations/{invitation_id}",
    response_model=EmployerInvitationOut,
    response_model_exclude_unset=True,
)
def get_employer_invitation(
    invitation_id: str, user: EmployerUser, db: Db
) -> EmployerInvitationOut:
    return invitations.employer_out(
        db, invitations.get(db, user, invitation_id, employer=True)
    )


@router.post(
    "/employer/invitations/{invitation_id}/withdraw",
    response_model=EmployerInvitationOut,
    response_model_exclude_unset=True,
    dependencies=mutations,
)
def withdraw(invitation_id: str, user: EmployerUser, db: Db) -> EmployerInvitationOut:
    return invitations.employer_out(
        db, invitations.transition(db, user, invitation_id, InvitationStatus.WITHDRAWN)
    )


@router.get(
    "/candidate/invitations",
    response_model=CandidateInvitationPage,
    response_model_exclude_unset=True,
)
def list_candidate_invitations(
    user: CandidateUser,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CandidateInvitationPage:
    return invitations.list_candidate(db, user, limit=limit, offset=offset)


@router.get(
    "/candidate/invitations/{invitation_id}",
    response_model=CandidateInvitationOut,
    response_model_exclude_unset=True,
)
def get_candidate_invitation(
    invitation_id: str, user: CandidateUser, db: Db
) -> CandidateInvitationOut:
    return invitations.candidate_out(
        db, invitations.get(db, user, invitation_id, employer=False)
    )


@router.post(
    "/candidate/invitations/{invitation_id}/view",
    response_model=CandidateInvitationOut,
    response_model_exclude_unset=True,
    dependencies=mutations,
)
def view(invitation_id: str, user: CandidateUser, db: Db) -> CandidateInvitationOut:
    return invitations.candidate_out(
        db, invitations.transition(db, user, invitation_id, InvitationStatus.VIEWED)
    )


@router.post(
    "/candidate/invitations/{invitation_id}/accept",
    response_model=CandidateInvitationOut,
    response_model_exclude_unset=True,
    dependencies=mutations,
)
def accept(invitation_id: str, user: CandidateUser, db: Db) -> CandidateInvitationOut:
    return invitations.candidate_out(
        db, invitations.transition(db, user, invitation_id, InvitationStatus.ACCEPTED)
    )


@router.post(
    "/candidate/invitations/{invitation_id}/decline",
    response_model=CandidateInvitationOut,
    response_model_exclude_unset=True,
    dependencies=mutations,
)
def decline(invitation_id: str, user: CandidateUser, db: Db) -> CandidateInvitationOut:
    return invitations.candidate_out(
        db, invitations.transition(db, user, invitation_id, InvitationStatus.DECLINED)
    )
