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
    assert interpretation.unresolved_obligations
