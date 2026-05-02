from __future__ import annotations

from threebody.analysis import TransitionSurvey
from threebody.analysis import AnalysisAtlas
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_transition_survey_collects_reports_for_multiple_cases() -> None:
    library = OrbitLibrary()
    integrator = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11)
    first = library.general_figure_eight(periods=0.2, samples=200)
    second = library.general_figure_eight(periods=0.2, samples=200, perturbation_scale=1.0e-3)
    first_trajectory = integrator.integrate(first.system, first.t_span, first.initial_state, t_eval=first.t_eval)
    second_trajectory = integrator.integrate(second.system, second.t_span, second.initial_state, t_eval=second.t_eval)

    result = TransitionSurvey().run(
        {
            "figure-eight": (first.system, first_trajectory),
            "perturbed": (second.system, second_trajectory),
        },
        stride=20,
    )

    assert set(result.reports_by_name) == {"figure-eight", "perturbed"}
    assert result.chart_distribution_rows()


def test_hierarchical_flyby_produces_chart_transitions() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=600)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    transitions = AnalysisAtlas().transitions(scenario.system, trajectory, stride=20)

    assert transitions
