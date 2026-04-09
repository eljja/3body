from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult


@dataclass(slots=True)
class StabilityAnalyzer:
    """Finite-time stability diagnostics based on trajectory separation."""

    epsilon: float = 1.0e-15

    def finite_time_lyapunov(
        self,
        reference: TrajectoryResult,
        perturbed: TrajectoryResult,
    ) -> dict[str, np.ndarray | float | str]:
        if reference.y.shape != perturbed.y.shape:
            raise ValueError("Reference and perturbed trajectories must share the same sampling.")
        if not np.allclose(reference.t, perturbed.t):
            raise ValueError("Reference and perturbed trajectories must share the same time grid.")

        separation = np.linalg.norm(perturbed.y - reference.y, axis=1)
        separation = np.maximum(separation, self.epsilon)
        baseline = separation[0]
        elapsed = np.maximum(reference.t - reference.t[0], self.epsilon)
        exponent = np.log(separation / baseline) / elapsed
        exponent[0] = 0.0
        classification = "chaotic-like" if exponent[-1] > 0.05 else "regular-like"
        return {
            "separation": separation,
            "lyapunov_series": exponent,
            "finite_time_lyapunov": float(exponent[-1]),
            "classification": classification,
        }
