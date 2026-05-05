from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from ..analysis import AnalysisAtlas, detect_hysteresis_loops, estimate_transition_boundaries
from ..solvers import AdaptiveIntegrator
from .orbit_library import OrbitLibrary


@dataclass(frozen=True, slots=True)
class BoundaryResolutionRow:
    samples: int
    stride: int
    transition_count: int
    low_crossing: float | None
    high_crossing: float | None
    hysteresis_width: float | None

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "samples": self.samples,
            "stride": self.stride,
            "transition_count": self.transition_count,
            "low_crossing": self.low_crossing,
            "high_crossing": self.high_crossing,
            "hysteresis_width": self.hysteresis_width,
        }


@dataclass(frozen=True, slots=True)
class BoundaryResolutionResult:
    rows: tuple[BoundaryResolutionRow, ...]

    def as_dict(self) -> dict[str, object]:
        low = [row.low_crossing for row in self.rows if row.low_crossing is not None]
        high = [row.high_crossing for row in self.rows if row.high_crossing is not None]
        return {
            "rows": [row.as_dict() for row in self.rows],
            "case_count": len(self.rows),
            "low_crossing_cv": _cv_or_none(low),
            "high_crossing_cv": _cv_or_none(high),
        }


@dataclass(slots=True)
class BoundaryResolutionStudy:
    integrator: AdaptiveIntegrator = field(default_factory=lambda: AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11))
    atlas: AnalysisAtlas = field(default_factory=AnalysisAtlas)
    library: OrbitLibrary = field(default_factory=OrbitLibrary)

    def run(
        self,
        sample_values: tuple[int, ...] = (300, 600),
        stride_values: tuple[int, ...] = (10, 20),
        duration: float = 8.0,
    ) -> BoundaryResolutionResult:
        rows = []
        for samples, stride in product(sample_values, stride_values):
            scenario = self.library.general_hierarchical_flyby(duration=duration, samples=samples)
            trajectory = self.integrator.integrate(
                scenario.system,
                scenario.t_span,
                scenario.initial_state,
                t_eval=scenario.t_eval,
            )
            reports = self.atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
            transitions = self.atlas.transitions(scenario.system, trajectory, stride=stride)
            boundaries = estimate_transition_boundaries(
                {"flyby": reports},
                coordinate="hierarchy_perturbation_strength",
            )
            loops = detect_hysteresis_loops(boundaries)
            if loops:
                loop = loops[0]
                rows.append(
                    BoundaryResolutionRow(
                        samples=samples,
                        stride=stride,
                        transition_count=len(transitions),
                        low_crossing=loop.low_crossing,
                        high_crossing=loop.high_crossing,
                        hysteresis_width=loop.width,
                    )
                )
            else:
                rows.append(
                    BoundaryResolutionRow(
                        samples=samples,
                        stride=stride,
                        transition_count=len(transitions),
                        low_crossing=None,
                        high_crossing=None,
                        hysteresis_width=None,
                    )
                )
        return BoundaryResolutionResult(rows=tuple(rows))


def _cv_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    mean = float(np.mean(values))
    if abs(mean) < 1.0e-12:
        return None
    return float(np.std(values) / abs(mean))
