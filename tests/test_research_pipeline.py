from __future__ import annotations

from threebody.analysis import ResearchPipeline
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_research_pipeline_runs_small_perturbation_study() -> None:
    scenario = OrbitLibrary().general_figure_eight(periods=0.1, samples=120)
    pipeline = ResearchPipeline(integrator=AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10))

    result = pipeline.run_perturbation_study(
        scenario,
        count=3,
        position_scale=1.0e-4,
        velocity_scale=1.0e-4,
        stride=20,
    )

    assert len(result.trajectories) == 3
    assert result.survey.chart_distribution_rows()
    assert isinstance(pipeline.law_rows(result.candidate_laws), list)
    assert result.summary()["trajectory_count"] == 3
