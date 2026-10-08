from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import CandidateUser, Db, require_trusted_origin
from app.fsp_schemas import FspAction, FspStatus
from app.services import fsp
from app.services.fsp_registry import FspRegistryProvider, MockFspRegistryProvider

router = APIRouter(prefix="/candidate/fsp", tags=["fsp prototype"])
mutations = [Depends(require_trusted_origin)]


def get_registry_provider() -> FspRegistryProvider:
    return MockFspRegistryProvider()


Registry = Annotated[FspRegistryProvider, Depends(get_registry_provider)]
EMPTY_ACTION = FspAction()


@router.get("", response_model=FspStatus)
def read_status(user: CandidateUser, db: Db) -> FspStatus:
    return fsp.status(db, user)


@router.post("/verify", response_model=FspStatus, dependencies=mutations)
def verify(
    user: CandidateUser, db: Db, provider: Registry, data: FspAction = EMPTY_ACTION
) -> FspStatus:
    return fsp.sync(db, user, provider)


@router.post("/refresh", response_model=FspStatus, dependencies=mutations)
def refresh(
    user: CandidateUser, db: Db, provider: Registry, data: FspAction = EMPTY_ACTION
) -> FspStatus:
    return fsp.sync(db, user, provider, refresh=True)


@router.delete("/verification", response_model=FspStatus, dependencies=mutations)
def unlink(user: CandidateUser, db: Db, data: FspAction = EMPTY_ACTION) -> FspStatus:
    return fsp.unlink(db, user)
