from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import Db
from app.models import Skill
from app.schemas import SkillOut

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def skills(db: Db) -> object:
    return list(db.scalars(select(Skill).order_by(Skill.name)))
