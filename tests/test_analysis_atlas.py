from __future__ import annotations

import numpy as np

from threebody.analysis import AnalysisAtlas, ChartClassifier, ChartType
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.systems import GeneralThreeBodySystem, RestrictedThreeBodySystem


def test_general_classifier_detects_hierarchical_binary_chart() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.1), dimension=2)
    positions = np.array([[0.0, 0.0], [0.05, 0.0], [4.0, 0.0]])
    velocities = np.zeros_like(positions)
    state = system.flatten_state(positions, velocities)

    report = ChartClassifier().classify(system, state)

    assert report.primary_chart in {ChartType.CLOSE_ENCOUNTER, ChartType.TWO_BODY_HIERARCHY}
    assert any(score.chart == ChartType.TWO_BODY_HIERARCHY and score.score > 0.5 for score in report.scores)


def test_restricted_classifier_detects_lagrange_neighborhood() -> None:
    system = RestrictedThreeBodySystem()
    l4 = system.lagrange_points()["L4"]
    state = np.array([l4[0] + 0.01, l4[1], 0.0, 0.0])

    report = ChartClassifier().classify(system, state)

    assert report.primary_chart == ChartType.RESTRICTED_LAGRANGE
    assert report.confidence > 0.8


def test_analysis_atlas_follows_trajectory_and_reports_distribution() -> None:
    scenario = OrbitLibrary().general_figure_eight(periods=0.25, samples=300)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    atlas = AnalysisAtlas()
    reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=20)
    distribution = atlas.chart_distribution(reports)

    assert reports
    assert abs(sum(distribution.values()) - 1.0) < 1.0e-12
