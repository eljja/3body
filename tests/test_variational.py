from __future__ import annotations

import numpy as np

from threebody.analysis import (
    finite_difference_jacobian,
    local_linearization,
    periodic_monodromy_certificate,
    variational_monodromy_certificate,
)
from threebody.solvers import AdaptiveIntegrator
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


def test_periodic_monodromy_certificate_reports_flow_map_diagnostics() -> None:
    scenario = OrbitLibrary().general_figure_eight(periods=0.02, samples=20)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = periodic_monodromy_certificate(scenario.system, trajectory, start_index=0, end_index=5)

    assert certificate.state_dimension == scenario.initial_state.size
    assert certificate.duration > 0.0
    assert certificate.spectral_radius > 0.0
    assert certificate.shadowing_radius_proxy >= 0.0
    assert np.isfinite(certificate.endpoint_error)


def test_variational_monodromy_certificate_resolves_figure_eight_period() -> None:
    scenario = OrbitLibrary().general_figure_eight(periods=1.0, samples=10)

    certificate = variational_monodromy_certificate(
        scenario.system,
        scenario.initial_state,
        float(scenario.metadata["period"]),
    )

    assert certificate.state_dimension == scenario.initial_state.size
    assert certificate.full_period_candidate is True
    assert certificate.volume_preserving_proxy is True
    assert certificate.reciprocal_pair_proxy is True
    assert certificate.linearly_stable_proxy is True
    assert certificate.closure_ratio < 5.0e-3
    assert certificate.determinant_error < 1.0e-4
    assert certificate.reciprocal_pair_error < 1.0e-4
