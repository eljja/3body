from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import CompactModelFit
from ..utils import monomial_powers


@dataclass(slots=True)
class CompactModelFitter:
    """Fit a local polynomial reduced model inside a declared validity radius."""

    degree: int = 2

    def fit(
        self,
        inputs: np.ndarray,
        outputs: np.ndarray,
        feature_names: tuple[str, ...],
        target_name: str,
        center: np.ndarray | None = None,
        valid_radius: float | None = None,
    ) -> CompactModelFit:
        inputs = np.atleast_2d(np.asarray(inputs, dtype=float))
        outputs = np.asarray(outputs, dtype=float)
        if inputs.shape[0] != outputs.shape[0]:
            raise ValueError("Input and output sample counts must match.")
        if center is None:
            center = np.mean(inputs, axis=0)
        center = np.asarray(center, dtype=float)
        shifted = inputs - center
        powers = monomial_powers(inputs.shape[1], self.degree)
        design = []
        for power in powers:
            term = np.ones(inputs.shape[0], dtype=float)
            for column, exponent in enumerate(power):
                if exponent:
                    term *= shifted[:, column] ** exponent
            design.append(term)
        matrix = np.column_stack(design)
        coefficients, *_rest = np.linalg.lstsq(matrix, outputs, rcond=None)
        prediction = matrix @ coefficients
        rmse = float(np.sqrt(np.mean((prediction - outputs) ** 2)))
        if valid_radius is None:
            valid_radius = float(np.percentile(np.linalg.norm(shifted, axis=1), 90))
        return CompactModelFit(
            coefficients=coefficients,
            powers=powers,
            center=center,
            valid_radius=float(valid_radius),
            rmse=rmse,
            feature_names=feature_names,
            target_name=target_name,
        )
