from __future__ import annotations

from threebody.experiments import BoundaryResolutionStudy
from threebody.solvers import AdaptiveIntegrator


def test_boundary_resolution_study_reports_crossing_rows() -> None:
    study = BoundaryResolutionStudy(integrator=AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10))

    result = study.run(sample_values=(250,), stride_values=(20,), duration=8.0)

    summary = result.as_dict()
    assert summary["case_count"] == 1
    assert result.rows[0].transition_count > 0
