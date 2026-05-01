from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..types import TrajectoryResult
from .charts import ChartClassifier
from .types import AnalysisReport, ChartTransition, ChartType


@dataclass(slots=True)
class AnalysisAtlas:
    """Follow a trajectory through interpretive charts and record transitions."""

    classifier: ChartClassifier = field(default_factory=ChartClassifier)

    def analyze_state(self, system: object, state: np.ndarray) -> AnalysisReport:
        return self.classifier.classify(system, state)

    def analyze_trajectory(
        self,
        system: object,
        trajectory: TrajectoryResult,
        stride: int = 1,
    ) -> tuple[AnalysisReport, ...]:
        if stride < 1:
            raise ValueError("stride must be >= 1.")
        reports = []
        for state in trajectory.y[::stride]:
            reports.append(self.analyze_state(system, state))
        return tuple(reports)

    def transitions(
        self,
        system: object,
        trajectory: TrajectoryResult,
        stride: int = 1,
        minimum_confidence: float = 0.15,
    ) -> tuple[ChartTransition, ...]:
        reports = self.analyze_trajectory(system, trajectory, stride=stride)
        if not reports:
            return ()

        transitions: list[ChartTransition] = []
        previous = reports[0].primary_chart
        for report_index, report in enumerate(reports[1:], start=1):
            current = report.primary_chart
            if current == previous or report.confidence < minimum_confidence:
                continue
            trajectory_index = report_index * stride
            time = float(trajectory.t[min(trajectory_index, len(trajectory.t) - 1)])
            transitions.append(
                ChartTransition(
                    index=trajectory_index,
                    time=time,
                    previous=previous,
                    current=current,
                    reason=report.scores[0].reason,
                )
            )
            previous = current
        return tuple(transitions)

    @staticmethod
    def chart_distribution(reports: tuple[AnalysisReport, ...]) -> dict[ChartType, float]:
        if not reports:
            return {}
        counts: dict[ChartType, int] = {}
        for report in reports:
            counts[report.primary_chart] = counts.get(report.primary_chart, 0) + 1
        total = float(len(reports))
        return {chart: count / total for chart, count in counts.items()}
