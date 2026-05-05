from __future__ import annotations

import numpy as np

from threebody.analysis import fit_power_law_boundary_collapse


def test_power_law_boundary_collapse_reduces_cv_for_scaled_boundary() -> None:
    adiabaticity = np.array([1.0, 2.0, 4.0, 8.0])
    hierarchy_ratio = np.array([3.0, 4.0, 5.0, 6.0])
    target = 0.01 * adiabaticity**0.5 * hierarchy_ratio**-1.0
    features = np.column_stack([adiabaticity, hierarchy_ratio])

    fit = fit_power_law_boundary_collapse(
        target,
        features,
        feature_names=("encounter_adiabaticity", "hierarchy_ratio"),
        target_name="boundary",
    )

    assert fit.support == 4
    assert fit.collapsed_cv is not None
    assert fit.raw_cv is not None
    assert fit.collapsed_cv < fit.raw_cv
