"""P4 achievement signal, independent of Assessment and Professional Fit."""

from collections.abc import Iterable
from dataclasses import dataclass

from app.models import FspResultLevel

QUALITY = {
    FspResultLevel.PARTICIPANT: 0.0,
    FspResultLevel.FINALIST: 0.50,
    FspResultLevel.PRIZE_WINNER: 0.80,
    FspResultLevel.WINNER: 1.00,
}


@dataclass(frozen=True)
class FspSignal:
    fsp_verified: bool = False
    fsp_achievement_score: float = 0.0
    competition_count: int = 0
    best_result_level: FspResultLevel | None = None

    @property
    def fsp_bonus(self) -> float:
        return self.fsp_achievement_score / 100 * 5 if self.fsp_verified else 0.0


UNVERIFIED = FspSignal()


def score_achievements(values: Iterable[tuple[str, FspResultLevel]]) -> FspSignal:
    achievements = tuple(values)
    count = len({competition for competition, _ in achievements})
    best = max(
        (level for _, level in achievements), key=QUALITY.__getitem__, default=None
    )
    score = min(count, 3) / 3 * 30 + (QUALITY[best] * 70 if best else 0)
    return FspSignal(True, min(100.0, max(0.0, score)), count, best)
