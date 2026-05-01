from __future__ import annotations

import numpy as np

from threebody.analysis import finite_difference_jacobian, local_linearization
from threebody.experiments import OrbitLibrary


def test_finite_difference_jacobian_matches_state_dimension() -> None:
    scenario = OrbitLibrary().general_figure_eight(samples=10)

    jacobian = finite_difference_jacobian(scenario.system, scenario.initial_state)

    assert jacobian.shape == (scenario.initial_state.size, scenario.initial_state.size)
    assert np.all(np.isfinite(jacobian))


def test_local_linearization_reports_spectral_radius() -> None:
    scenario = OrbitLibrary().restricted_l4(samples=10)

    linearization = local_linearization(scenario.system, scenario.initial_state)

    assert linearization.jacobian.shape == (4, 4)
    assert linearization.spectral_radius > 0.0
    assert np.all(np.isfinite(linearization.eigenvalues))
