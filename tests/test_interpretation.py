from __future__ import annotations

from threebody.analysis import ThreeBodyInterpreter
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.systems import GeneralThreeBodySystem
from threebody.types import Scenario, TrajectoryResult
import numpy as np


def test_three_body_interpreter_returns_chart_local_claims() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=4.0, samples=200)
    trajectory = AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    interpretation = ThreeBodyInterpreter().interpret(scenario.system, trajectory, stride=20)
    summary = interpretation.as_dict()

    assert interpretation.segments
    assert interpretation.certificate.local_interpretation_available
    assert interpretation.certificate.theorem_ready is False
    assert interpretation.certificate.regime_status == "locally_interpretable_not_theorem_ready"
    assert summary["method_statement"]
    assert summary["certificate"]["path_to_solution"]
    assert summary["chart_distribution"]
    assert all(segment.model_family for segment in interpretation.segments)
    assert all(segment.proof_status for segment in interpretation.segments)
    assert all(segment.interpretability_score > 0.0 for segment in interpretation.segments)
    assert all(segment.validity_statement for segment in interpretation.segments)
    hierarchy_segments = [segment for segment in interpretation.segments if segment.chart.value == "two_body_hierarchy"]
    assert not hierarchy_segments or "hierarchy_relative_action_drift" in hierarchy_segments[0].diagnostics
    assert not hierarchy_segments or "resonance_relative_detuning" in hierarchy_segments[0].diagnostics
    periodic_segments = [
        segment for segment in interpretation.segments if segment.chart.value == "periodic_orbit_neighborhood"
    ]
    assert not periodic_segments or "monodromy_spectral_radius" in periodic_segments[0].diagnostics
    assert interpretation.unresolved_obligations


def test_three_body_interpreter_attaches_escape_asymptotic_certificate() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.1), dimension=2)
    positions = np.array([[-0.1, 0.0], [0.1, 0.0], [8.0, 0.0]], dtype=float)
    velocities = np.array([[0.0, 0.4], [0.0, -0.4], [4.0, 0.0]], dtype=float)
    scenario = Scenario(
        name="escape-interpretation",
        system=system,
        initial_state=system.flatten_state(positions, velocities),
        t_span=(0.0, 1.0),
        t_eval=np.linspace(0.0, 1.0, 80),
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    interpretation = ThreeBodyInterpreter().interpret(system, trajectory, stride=10)
    escape_segments = [segment for segment in interpretation.segments if segment.chart.value == "escape_transport"]

    assert escape_segments
    assert "escape_outgoing_energy" in escape_segments[-1].diagnostics
    assert "escape_asymptotic_resolved" in escape_segments[-1].diagnostics


def test_three_body_interpreter_attaches_collision_regularization_certificate() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    state = system.flatten_state(
        np.array([[0.0, 0.0], [0.005, 0.0], [1.0, 0.0]], dtype=float),
        np.zeros((3, 2), dtype=float),
    )
    trajectory = TrajectoryResult(
        t=np.array([0.0, 0.01]),
        y=np.vstack([state, state]),
        success=True,
        message="synthetic close encounter",
    )

    interpretation = ThreeBodyInterpreter().interpret(system, trajectory, stride=1)
    close_segments = [segment for segment in interpretation.segments if segment.chart.value == "close_encounter"]

    assert close_segments
    assert "collision_minimum_pair_distance" in close_segments[0].diagnostics
    assert close_segments[0].diagnostics["collision_regularization_required"] is True


def test_three_body_interpreter_attaches_restricted_lagrange_certificate() -> None:
    scenario = OrbitLibrary().restricted_l4(periods=0.1, samples=80)
    trajectory = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    interpretation = ThreeBodyInterpreter().interpret(scenario.system, trajectory, stride=10)
    restricted_segments = [
        segment for segment in interpretation.segments if segment.chart.value == "restricted_lagrange"
    ]

    assert restricted_segments
    assert "restricted_max_abs_jacobi_drift" in restricted_segments[0].diagnostics
    assert "restricted_routh_stable_triangular" in restricted_segments[0].diagnostics
