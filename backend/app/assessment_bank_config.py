from dataclasses import dataclass

from app.models import Difficulty, Specialization

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


@dataclass(frozen=True)
class SourceBlueprint:
    basic: int
    applied: int
    advanced: int

    @property
    def mix(self) -> dict[Difficulty, int]:
        return {
            Difficulty.BASIC: self.basic,
            Difficulty.APPLIED: self.applied,
            Difficulty.ADVANCED: self.advanced,
        }


# P8-A0 preserves the already published P5 source until P8-A1 is reviewed.
LEGACY_BACKEND_BLUEPRINT = SourceBlueprint(2, 4, 2)
EXPANDED_BLUEPRINT = SourceBlueprint(2, 6, 2)
