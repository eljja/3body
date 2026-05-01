from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .types import ChartTransition, ChartType


@dataclass(slots=True)
class TransitionGraph:
    """Empirical transition graph between analysis charts."""

    counts: dict[tuple[ChartType, ChartType], int] = field(default_factory=dict)

    def add(self, transitions: tuple[ChartTransition, ...] | list[ChartTransition]) -> None:
        for transition in transitions:
            key = (transition.previous, transition.current)
            self.counts[key] = self.counts.get(key, 0) + 1

    def probability(self, previous: ChartType, current: ChartType) -> float:
        outgoing = sum(count for (source, _target), count in self.counts.items() if source == previous)
        if outgoing == 0:
            return 0.0
        return self.counts.get((previous, current), 0) / outgoing

    def matrix(self, charts: tuple[ChartType, ...] | None = None) -> tuple[np.ndarray, tuple[ChartType, ...]]:
        if charts is None:
            chart_set = set()
            for source, target in self.counts:
                chart_set.add(source)
                chart_set.add(target)
            charts = tuple(sorted(chart_set, key=str))
        index = {chart: row for row, chart in enumerate(charts)}
        matrix = np.zeros((len(charts), len(charts)), dtype=float)
        for (source, target), count in self.counts.items():
            if source in index and target in index:
                matrix[index[source], index[target]] = count
        row_sums = matrix.sum(axis=1, keepdims=True)
        np.divide(matrix, row_sums, out=matrix, where=row_sums > 0.0)
        return matrix, charts

    def rows(self) -> list[dict[str, float | int | str]]:
        rows = []
        for (source, target), count in sorted(self.counts.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
            rows.append(
                {
                    "from": str(source),
                    "to": str(target),
                    "count": count,
                    "probability": self.probability(source, target),
                }
            )
        return rows
