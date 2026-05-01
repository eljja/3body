from __future__ import annotations

from threebody.analysis import TransitionSurvey
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
