from __future__ import annotations

import numpy as np

from threebody.analysis import fit_power_law_boundary_collapse, validate_power_law_boundary_collapse


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
    assert fit.log_residual_sum_squares is not None
    assert fit.aic is not None
    assert fit.bic is not None


def test_power_law_boundary_collapse_validates_on_heldout_data() -> None:
    train_features = np.array([[1.0, 3.0], [2.0, 4.0], [4.0, 5.0], [8.0, 6.0]])
    train_target = 0.01 * train_features[:, 0] ** 0.5 * train_features[:, 1] ** -1.0
    validation_features = np.array([[1.5, 3.5], [3.0, 4.5], [6.0, 5.5]])
    validation_target = 0.01 * validation_features[:, 0] ** 0.5 * validation_features[:, 1] ** -1.0
    fit = fit_power_law_boundary_collapse(
        train_target,
        train_features,
        feature_names=("encounter_adiabaticity", "hierarchy_ratio"),
        target_name="boundary",
    )

    validation = validate_power_law_boundary_collapse(fit, validation_target, validation_features)

    assert validation.validation_support == 3
    assert validation.validation_collapsed_cv is not None
    assert validation.validation_raw_cv is not None
    assert validation.validation_collapsed_cv < validation.validation_raw_cv
