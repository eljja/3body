from __future__ import annotations

import numpy as np

from threebody.experiments import CompactModelFitter


def test_local_polynomial_fit_recovers_quadratic_response() -> None:
    x = np.linspace(-0.2, 0.2, 12)
    y = np.linspace(-0.1, 0.1, 10)
    xx, yy = np.meshgrid(x, y)
    inputs = np.column_stack([xx.ravel(), yy.ravel()])
    outputs = 1.5 + 2.0 * inputs[:, 0] - 0.75 * inputs[:, 1] + 0.5 * inputs[:, 0] ** 2 + 0.25 * inputs[:, 0] * inputs[:, 1]

    fit = CompactModelFitter(degree=2).fit(inputs, outputs, ("x", "vx"), "proxy")
    prediction = fit.predict(inputs)

    assert np.max(np.abs(prediction - outputs)) < 1.0e-10
