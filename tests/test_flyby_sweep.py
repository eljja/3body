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
    assert result.rows[0].chart_word
    assert result.rows[0].refined_chart_word
    assert result.rows[0].return_chart_word
    assert result.rows[0].refined_word_grammar_rank >= result.rows[0].word_grammar_rank


def test_hierarchical_flyby_sweep_tracks_phase_features() -> None:
    sweep = HierarchicalFlybySweep(integrator=AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10))

    result = sweep.run(
        intruder_masses=(0.2,),
        impact_parameters=(0.0,),
        intruder_speed_y_values=(1.2,),
        binary_phases=(0.0, 1.5707963267948966),
        duration=8.0,
        samples=250,
        stride=20,
    )

    assert result.as_dict()["case_count"] == 2
    assert result.rows[0].case.binary_phase != result.rows[1].case.binary_phase
    assert result.rows[0].phase_alignment != result.rows[1].phase_alignment
    assert result.rows[0].nonlinear_tidal_exposure > 0.0


def test_hierarchical_flyby_sweep_runs_heldout_validation() -> None:
    sweep = HierarchicalFlybySweep(integrator=AdaptiveIntegrator(rtol=1.0e-8, atol=1.0e-10))

    result = sweep.run_discovery_validation(
        discovery_intruder_masses=(0.2,),
        discovery_impact_parameters=(0.0,),
        discovery_intruder_speed_y_values=(1.2,),
        validation_intruder_masses=(0.3,),
        validation_impact_parameters=(0.1,),
        validation_intruder_speed_y_values=(1.1,),
        discovery_binary_phases=(0.0, 1.5707963267948966),
        validation_binary_phases=(0.7853981633974483,),
        duration=8.0,
        samples=250,
        stride=20,
    )

    summary = result.as_dict()
    assert summary["discovery"]["case_count"] == 2
    assert summary["validation"]["case_count"] == 1
    assert summary["collapse_validations"]
    assert "best_validation_models" in summary
    assert "worst_validation_residuals" in summary
    assert any(row["target"].endswith("phase_nonlinear") for row in summary["collapse_validations"])
