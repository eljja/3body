from __future__ import annotations

from threebody.analysis import (
    jacobi_energy_decomposition,
    jacobi_escape_sufficient_condition,
    jacobi_future_tail_bound,
    jacobi_inflated_margin_certificate,
    jacobi_open_escape_cone_certificate,
    jacobi_self_consistent_escape_cone,
)
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_jacobi_energy_decomposition_closes_hamiltonian_split() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=2.0, samples=120)

    decomposition = jacobi_energy_decomposition(scenario.system, scenario.initial_state, inner_pair=(0, 1))

    assert decomposition.inner_pair == (0, 1)
    assert decomposition.outer_body == 2
    assert decomposition.closure_residual < 1.0e-12
    assert decomposition.interaction_bound >= abs(decomposition.interaction_remainder)
    assert decomposition.quadrupole_interaction_bound >= abs(decomposition.interaction_remainder)
    assert decomposition.quadrupole_interaction_bound < decomposition.interaction_bound
    assert decomposition.hierarchy_ratio > 1.0


def test_jacobi_escape_sufficient_condition_certifies_fast_outgoing_flyby() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=500,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_escape_sufficient_condition(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.decomposition_resolved is True
    assert certificate.sufficient_escape is True
    assert certificate.escape_margin > 0.0
    assert certificate.radius_growth_fraction == 1.0
    assert certificate.minimum_radial_velocity > 0.0


def test_jacobi_future_tail_bound_certifies_conditional_asymptotic_escape() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=500,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_future_tail_bound(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.assumptions_satisfied is True
    assert certificate.conditional_asymptotic_escape is True
    assert certificate.future_energy_exchange_bound > 0.0
    assert certificate.asymptotic_escape_margin > 0.0


def test_jacobi_inflated_margin_certificate_keeps_positive_lower_bound() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=500,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_inflated_margin_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.validated_positive is True
    assert certificate.validated_margin_lower > 0.0
    assert certificate.validated_margin_lower < certificate.nominal_asymptotic_margin


def test_jacobi_self_consistent_escape_cone_has_radial_floor() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=500,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_self_consistent_escape_cone(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.self_consistent is True
    assert certificate.certified_radial_floor > 0.0
    assert certificate.energy_radial_floor > 0.0
    assert certificate.future_exchange_bound < certificate.asymptotic_margin_lower


def test_jacobi_open_escape_cone_certificate_has_positive_radius() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(
        intruder_velocity=(0.8, 1.6),
        duration=8.0,
        samples=500,
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_open_escape_cone_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.open_cone_certified is True
    assert certificate.absolute_state_radius > 0.0
    assert certificate.relative_state_radius > 1.0e-8
    assert certificate.validated_margin_lower > 0.0


def test_jacobi_escape_sufficient_condition_rejects_uncertain_bound_tail() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=500)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_escape_sufficient_condition(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.decomposition_resolved is True
    assert certificate.sufficient_escape is False
    assert certificate.escape_margin < 0.0
