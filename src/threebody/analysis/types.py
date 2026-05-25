from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ChartType(StrEnum):
    """Interpretive charts used by the analysis atlas."""

    TWO_BODY_HIERARCHY = "two_body_hierarchy"
    DEMOCRATIC_THREE_BODY = "democratic_three_body"
    CLOSE_ENCOUNTER = "close_encounter"
    ESCAPE_TRANSPORT = "escape_transport"
    RESTRICTED_LAGRANGE = "restricted_lagrange"
    RESTRICTED_GATEWAY = "restricted_gateway"
    PERIODIC_ORBIT_NEIGHBORHOOD = "periodic_orbit_neighborhood"
    CHAOTIC_TRANSPORT = "chaotic_transport"


@dataclass(frozen=True, slots=True)
class ChartScore:
    chart: ChartType
    score: float
    reason: str
    diagnostics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChartTransition:
    index: int
    time: float
    previous: ChartType
    current: ChartType
    reason: str


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    primary_chart: ChartType
    scores: tuple[ChartScore, ...]
    features: Any
    reduced_state: Any | None = None

    @property
    def confidence(self) -> float:
        if not self.scores:
            return 0.0
        return float(self.scores[0].score)
