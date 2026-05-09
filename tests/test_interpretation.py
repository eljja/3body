from __future__ import annotations

from threebody.analysis import ThreeBodyInterpreter
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


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
    assert summary["method_statement"]
    assert summary["chart_distribution"]
    assert all(segment.model_family for segment in interpretation.segments)
    assert all(segment.validity_statement for segment in interpretation.segments)
    assert interpretation.unresolved_obligations
