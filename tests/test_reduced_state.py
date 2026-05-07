from __future__ import annotations

from threebody.analysis import reduced_state_series, reduced_three_body_state
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_reduced_three_body_state_reports_shared_atlas_coordinates() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(samples=50)

    reduced = reduced_three_body_state(scenario.system, scenario.initial_state)

    assert reduced.hyperradius > 0.0
    assert reduced.nearest_distance > 0.0
    assert reduced.hierarchy_ratio > 1.0
    assert reduced.reduced_regime_hint in {
        "collision_boundary",
        "escape_boundary",
        "hierarchy_chart",
        "democratic_shape",
        "transition_region",
    }


def test_reduced_state_series_tracks_trajectory_time() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=1.0, samples=80)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    series = reduced_state_series(scenario.system, trajectory, stride=10)

    assert len(series) == 8
    assert series[0].time == trajectory.t[0]
    assert series[-1].time == trajectory.t[70]
