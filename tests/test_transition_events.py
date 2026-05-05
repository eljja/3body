from __future__ import annotations

from threebody.analysis import AnalysisAtlas, transition_event_evidence
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_transition_event_evidence_identifies_changing_feature() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=500)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    reports = AnalysisAtlas().analyze_trajectory(scenario.system, trajectory, stride=20)

    events = transition_event_evidence({"flyby": reports})

    assert events
    assert events[0].strongest_feature
    assert events[0].abs_delta >= 0.0
