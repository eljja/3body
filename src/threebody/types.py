from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class TrajectoryResult:
    """Container for a solved trajectory."""

    t: np.ndarray
    y: np.ndarray
    success: bool
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def state_dim(self) -> int:
        return int(self.y.shape[1])


@dataclass(slots=True)
class Scenario:
    """Reusable simulation scenario."""

    name: str
    system: Any
    initial_state: np.ndarray
    t_span: tuple[float, float]
    t_eval: np.ndarray | None = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CompactModelFit:
    """Local reduced-order polynomial surrogate."""

    coefficients: np.ndarray
    powers: list[tuple[int, ...]]
    center: np.ndarray
    valid_radius: float
    rmse: float
    feature_names: tuple[str, ...]
    target_name: str

    def predict(self, inputs: np.ndarray) -> np.ndarray:
        x = np.atleast_2d(np.asarray(inputs, dtype=float)) - self.center
        design = []
        for power in self.powers:
            term = np.ones(x.shape[0], dtype=float)
            for column, exponent in enumerate(power):
                if exponent:
                    term *= x[:, column] ** exponent
            design.append(term)
        matrix = np.column_stack(design)
        return matrix @ self.coefficients

    def within_validity(self, inputs: np.ndarray) -> np.ndarray:
        x = np.atleast_2d(np.asarray(inputs, dtype=float)) - self.center
        radius = np.linalg.norm(x, axis=1)
        return radius <= self.valid_radius
