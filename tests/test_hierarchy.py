from __future__ import annotations

import numpy as np

from threebody.analysis import hierarchical_elements, hierarchy_action_drift_bound
from threebody.solvers import AdaptiveIntegrator
from threebody.types import Scenario
from threebody.analysis.coordinates import general_three_body_features
from threebody.analysis.transition_model import feature_names_for_report
from threebody.analysis.types import AnalysisReport, ChartScore, ChartType
from threebody.systems import GeneralThreeBodySystem


def test_hierarchical_elements_detects_bound_inner_binary() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.1), dimension=2)
    relative_speed = np.sqrt(2.0 / 0.1)
    positions = np.array([[-0.05, 0.0], [0.05, 0.0], [10.0, 0.0]])
    velocities = np.array([[0.0, -0.5 * relative_speed], [0.0, 0.5 * relative_speed], [0.0, 0.0]])
    state = system.flatten_state(positions, velocities)

    elements = hierarchical_elements(system, state)

    assert elements.inner_pair == (0, 1)
    assert elements.outer_body == 2
    assert elements.is_inner_bound
    assert elements.inner_eccentricity < 1.0e-8
    assert elements.perturbation_strength < 1.0e-6

    features = general_three_body_features(system, state)
    report = AnalysisReport(
        primary_chart=ChartType.TWO_BODY_HIERARCHY,
        scores=(ChartScore(ChartType.TWO_BODY_HIERARCHY, 1.0, "test"),),
        features=features,
    )
    assert "hierarchy_perturbation_strength" in feature_names_for_report(report)
    assert np.isclose(features.hierarchy_perturbation_strength, elements.perturbation_strength)


def test_hierarchy_action_drift_bound_tracks_perturbation_budget() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.01), dimension=2)
    relative_speed = np.sqrt(2.0 / 0.1)
    positions = np.array([[-0.05, 0.0], [0.05, 0.0], [12.0, 0.0]])
    velocities = np.array([[0.0, -0.5 * relative_speed], [0.0, 0.5 * relative_speed], [0.0, 0.02]])
    state = system.flatten_state(positions, velocities)
    scenario = Scenario(
        name="weak-hierarchy",
        system=system,
        initial_state=state,
        t_span=(0.0, 0.2),
        t_eval=np.linspace(0.0, 0.2, 80),
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    bound = hierarchy_action_drift_bound(system, trajectory)

    assert bound.sample_count == 80
    assert bound.inner_pair == (0, 1)
    assert bound.max_perturbation_strength < 1.0e-7
    assert bound.relative_action_drift >= 0.0
    assert bound.relative_angular_momentum_drift >= 0.0
