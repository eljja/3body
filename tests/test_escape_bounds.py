from __future__ import annotations

from threebody.analysis import (
    jacobi_energy_decomposition,
    jacobi_escape_sufficient_condition,
    jacobi_future_tail_bound,
    jacobi_inflated_margin_certificate,
    jacobi_interval_flow_tube_certificate,
    jacobi_interval_picard_flow_certificate,
    jacobi_interval_escape_certificate,
    jacobi_open_escape_cone_certificate,
    jacobi_quadrupole_acceleration_certificate,
    jacobi_self_consistent_escape_cone,
    jacobi_tail_interval_reserve_certificate,
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


def test_jacobi_quadrupole_acceleration_certificate_bounds_tail_perturbation() -> None:
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

    certificate = jacobi_quadrupole_acceleration_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.quadrupole_bound_resolved is True
    assert certificate.maximum_observed_perturbing_acceleration > 0.0
    assert certificate.minimum_declared_bound > 0.0
    assert certificate.maximum_bound_ratio <= 1.0


def test_jacobi_tail_interval_reserve_certificate_survives_terminal_state_radius() -> None:
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

    certificate = jacobi_tail_interval_reserve_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.interval_reserve_certified is True
    assert certificate.sampled_axis_count == trajectory.state_dim
    assert certificate.finite_difference_lipschitz > 0.0
    assert certificate.interval_margin_lower > 0.0


def test_jacobi_interval_escape_certificate_encloses_positive_tail_box() -> None:
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

    certificate = jacobi_interval_escape_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.split_identity_enclosed is True
    assert certificate.interval_tail_assumptions_satisfied is True
    assert certificate.interval_escape_certified is True
    assert certificate.state_box_radius > 0.0
    assert certificate.asymptotic_margin_lower > 0.0
    assert certificate.minimum_radial_velocity_lower > 0.0
    assert certificate.minimum_hierarchy_ratio_lower > 4.0


def test_jacobi_interval_flow_tube_certificate_links_tail_box_to_rhs() -> None:
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

    certificate = jacobi_interval_flow_tube_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.rhs_inclusion_passed is True
    assert certificate.interval_escape_certified is True
    assert certificate.flow_tube_certified is True
    assert certificate.tube_radius > certificate.maximum_trapezoid_defect
    assert certificate.interval_escape_margin_lower > 0.0


def test_jacobi_interval_picard_flow_certificate_propagates_tail_boxes() -> None:
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

    certificate = jacobi_interval_picard_flow_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.picard_inclusion_passed is True
    assert certificate.endpoint_inclusion_passed is True
    assert certificate.interval_escape_certified is True
    assert certificate.picard_flow_certified is True
    assert certificate.lipschitz_bound_method == "interval_newtonian_rhs_jacobian_inf_row_sum"
    assert certificate.maximum_propagated_endpoint_radius > certificate.tube_radius
    assert certificate.maximum_observed_contraction < certificate.target_contraction
    assert certificate.interval_escape_margin_lower > 0.0


def test_jacobi_interval_escape_certificate_rejects_uncertain_tail_box() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=500)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = jacobi_interval_escape_certificate(scenario.system, trajectory, inner_pair=(0, 1))

    assert certificate.interval_escape_certified is False
    assert certificate.asymptotic_margin_lower < 0.0


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
