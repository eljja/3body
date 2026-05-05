from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .transition_model import feature_names_for_report, feature_vector_for_report
from .types import AnalysisReport, ChartType


@dataclass(frozen=True, slots=True)
class TransitionBoundaryEstimate:
    previous: ChartType
    current: ChartType
    coordinate: str
    before_mean: float
    after_mean: float
    crossing_mean: float
    crossing_std: float
    delta_mean: float
    support: int

    @property
    def direction(self) -> str:
        if self.delta_mean > 0.0:
            return "increasing"
        if self.delta_mean < 0.0:
            return "decreasing"
        return "flat"


def estimate_transition_boundaries(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
    coordinate: str = "hierarchy_perturbation_strength",
) -> tuple[TransitionBoundaryEstimate, ...]:
    grouped: dict[tuple[ChartType, ChartType], list[tuple[float, float]]] = {}
    for reports in reports_by_name.values():
        if len(reports) < 2:
            continue
        for before_report, after_report in zip(reports, reports[1:], strict=False):
            if before_report.primary_chart == after_report.primary_chart:
                continue
            before_names = feature_names_for_report(before_report)
            after_names = feature_names_for_report(after_report)
            if before_names != after_names or coordinate not in before_names:
                continue
            index = before_names.index(coordinate)
            before_value = float(feature_vector_for_report(before_report)[index])
            after_value = float(feature_vector_for_report(after_report)[index])
            if not np.isfinite(before_value) or not np.isfinite(after_value):
                continue
            grouped.setdefault((before_report.primary_chart, after_report.primary_chart), []).append(
                (before_value, after_value)
            )

    estimates: list[TransitionBoundaryEstimate] = []
    for (previous, current), pairs in grouped.items():
        matrix = np.asarray(pairs, dtype=float)
        before = matrix[:, 0]
        after = matrix[:, 1]
        crossing = 0.5 * (before + after)
        delta = after - before
        estimates.append(
            TransitionBoundaryEstimate(
                previous=previous,
                current=current,
                coordinate=coordinate,
                before_mean=float(np.mean(before)),
                after_mean=float(np.mean(after)),
                crossing_mean=float(np.mean(crossing)),
                crossing_std=float(np.std(crossing)),
                delta_mean=float(np.mean(delta)),
                support=int(matrix.shape[0]),
            )
        )
    return tuple(sorted(estimates, key=lambda item: (str(item.previous), str(item.current))))


def transition_boundary_rows(
    estimates: tuple[TransitionBoundaryEstimate, ...] | list[TransitionBoundaryEstimate],
) -> list[dict[str, float | int | str]]:
    return [
        {
            "from": str(estimate.previous),
            "to": str(estimate.current),
            "coordinate": estimate.coordinate,
            "before_mean": estimate.before_mean,
            "after_mean": estimate.after_mean,
            "crossing_mean": estimate.crossing_mean,
            "crossing_std": estimate.crossing_std,
            "delta_mean": estimate.delta_mean,
            "direction": estimate.direction,
            "support": estimate.support,
        }
        for estimate in estimates
    ]
