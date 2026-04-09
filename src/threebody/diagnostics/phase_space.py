from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from ..types import TrajectoryResult


@dataclass(slots=True)
class PhaseSpaceTools:
    """Poincare sections, return maps, and basin scans."""

    def planar_poincare_section(
        self,
        trajectory: TrajectoryResult,
        x_index: int,
        y_index: int,
        vx_index: int,
        vy_index: int,
        crossing_value: float = 0.0,
        direction: str = "positive",
    ) -> np.ndarray:
        samples: list[np.ndarray] = []
        y_values = trajectory.y[:, y_index] - crossing_value
        for idx in range(trajectory.y.shape[0] - 1):
            first = y_values[idx]
            second = y_values[idx + 1]
            if first == 0.0 and second == 0.0:
                continue
            crossed = (first <= 0.0 < second) or (first >= 0.0 > second)
            if not crossed:
                continue
            fraction = abs(first) / (abs(first) + abs(second))
            state = (1.0 - fraction) * trajectory.y[idx] + fraction * trajectory.y[idx + 1]
            vy = state[vy_index]
            if direction == "positive" and vy <= 0.0:
                continue
            if direction == "negative" and vy >= 0.0:
                continue
            samples.append(np.array([state[x_index], state[vx_index], state[vy_index]], dtype=float))
        if not samples:
            return np.empty((0, 3), dtype=float)
        return np.vstack(samples)

    def return_map(self, section_points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        section_points = np.asarray(section_points, dtype=float)
        if len(section_points) < 2:
            return np.empty((0,)), np.empty((0,))
        return section_points[:-1, 0], section_points[1:, 0]

    def basin_scan(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        evaluator: Callable[[float, float], str],
    ) -> np.ndarray:
        classes = np.empty((y_values.size, x_values.size), dtype=object)
        for row, y_value in enumerate(y_values):
            for column, x_value in enumerate(x_values):
                classes[row, column] = evaluator(float(x_value), float(y_value))
        return classes
