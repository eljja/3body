from __future__ import annotations

from threebody.experiments import HierarchicalFlybySweep
from threebody.solvers import AdaptiveIntegrator


def test_hierarchical_flyby_sweep_returns_boundary_rows() -> None:
    sweep = HierarchicalFlybySweep(integrator=AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10))

    result = sweep.run(
        intruder_masses=(0.2,),
        impact_parameters=(0.0,),
        intruder_speed_y_values=(1.2,),
        duration=8.0,
        samples=300,
        stride=20,
    )

    summary = result.as_dict()
    assert summary["case_count"] == 1
    assert "high_crossing_cv" in summary
    assert "collapse_fits" in summary
    assert result.rows[0].encounter_adiabaticity > 0.0
    assert result.rows[0].tidal_impulse > 0.0
    assert result.rows[0].transition_count > 0
