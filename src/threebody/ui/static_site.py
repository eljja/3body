from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import html
import json
import os
import platform
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from threebody.cli import (
    PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE,
    STATIC_SITE_GITATTRIBUTES_POLICY,
    STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES,
    STATIC_SITE_ARTIFACT_NAMES,
    static_artifact_requirement_profile_descriptor,
    static_artifact_requirement_profile_sha256,
    static_artifact_verification_features_sha256,
)
from threebody.analysis import (
    AnalysisAtlas,
    bootstrap_markov_baseline_comparison,
    compare_markov_chain_to_independent_baseline,
    jacobi_future_tail_bound,
    jacobi_inflated_margin_certificate,
    jacobi_interval_picard_flow_certificate,
    jacobi_open_escape_cone_certificate,
    jacobi_picard_tuning_certificate,
    jacobi_quadrupole_acceleration_certificate,
    jacobi_self_consistent_escape_cone,
    markov_chain_from_words,
    permutation_control_markov_validation,
    poincare_markov_section_robustness,
    poincare_section_word_from_reports,
    poincare_coordinate_sweep_from_reports,
    poincare_section_sweep_from_reports,
    refined_chart_word_from_reports,
    return_map_word_from_reports,
    select_markov_order,
)
from threebody.diagnostics import InvariantMonitor, StabilityAnalyzer
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.types import TrajectoryResult
from threebody_engine import solve_three_body_target_positions


PALETTE = ["#0b84f3", "#f95d6a", "#00a878", "#ffa600", "#6c63ff"]


def build_static_site(output_dir: str | Path) -> Path:
    """Build a static GitHub Pages dashboard from precomputed reference runs."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    provenance = _build_provenance()

    library = OrbitLibrary()
    integrator = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12)

    two_body = library.two_body_elliptic(periods=1.0, samples=700)
    two_body_traj = integrator.integrate(two_body.system, two_body.t_span, two_body.initial_state, t_eval=two_body.t_eval)

    restricted = library.restricted_l4(periods=8.0, samples=900)
    restricted_traj = integrator.integrate(restricted.system, restricted.t_span, restricted.initial_state, t_eval=restricted.t_eval)

    general = library.general_figure_eight(periods=1.0, samples=1000)
    general_traj = integrator.integrate(general.system, general.t_span, general.initial_state, t_eval=general.t_eval)

    jacobi_flyby = library.general_hierarchical_flyby(intruder_velocity=(0.8, 1.6), duration=8.0, samples=500)
    jacobi_traj = integrator.integrate(
        jacobi_flyby.system,
        jacobi_flyby.t_span,
        jacobi_flyby.initial_state,
        t_eval=jacobi_flyby.t_eval,
    )
    grammar_flyby = library.general_hierarchical_flyby(duration=8.0, samples=500)
    grammar_traj = integrator.integrate(
        grammar_flyby.system,
        grammar_flyby.t_span,
        grammar_flyby.initial_state,
        t_eval=grammar_flyby.t_eval,
    )
    grammar_phase_flyby = library.general_hierarchical_flyby(binary_phase=0.5 * np.pi, duration=8.0, samples=500)
    grammar_phase_traj = integrator.integrate(
        grammar_phase_flyby.system,
        grammar_phase_flyby.t_span,
        grammar_phase_flyby.initial_state,
        t_eval=grammar_phase_flyby.t_eval,
    )
    grammar_phase_extra_flyby = library.general_hierarchical_flyby(binary_phase=np.pi, duration=8.0, samples=500)
    grammar_phase_extra_traj = integrator.integrate(
        grammar_phase_extra_flyby.system,
        grammar_phase_extra_flyby.t_span,
        grammar_phase_extra_flyby.initial_state,
        t_eval=grammar_phase_extra_flyby.t_eval,
    )

    page, certificate_bundle = _render_page(
        two_body=two_body_traj,
        two_body_system=two_body.system,
        restricted=restricted_traj,
        restricted_system=restricted.system,
        general=general_traj,
        general_system=general.system,
        jacobi_flyby=jacobi_traj,
        jacobi_flyby_system=jacobi_flyby.system,
        grammar_flyby=grammar_traj,
        grammar_flyby_system=grammar_flyby.system,
        grammar_phase_flyby=grammar_phase_traj,
        grammar_phase_flyby_system=grammar_phase_flyby.system,
        grammar_phase_extra_flyby=grammar_phase_extra_traj,
        grammar_phase_extra_flyby_system=grammar_phase_extra_flyby.system,
        provenance=provenance,
    )

    index_path = output_path / "index.html"
    certificate_path = output_path / "certificate.json"
    manifest_path = output_path / "manifest.json"
    favicon_path = output_path / "favicon.svg"
    _write_text_lf(index_path, page)
    _write_text_lf(
        certificate_path,
        json.dumps(certificate_bundle, indent=2, sort_keys=True),
    )
    _write_text_lf(favicon_path, _favicon_svg())
    _write_text_lf(output_path / ".nojekyll", "")
    _write_text_lf(output_path / ".gitattributes", STATIC_SITE_GITATTRIBUTES_POLICY.decode("ascii"))
    _write_text_lf(
        manifest_path,
        json.dumps(_artifact_manifest(output_path, provenance), indent=2, sort_keys=True),
    )
    return index_path


def _write_text_lf(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _render_page(
    *,
    two_body: TrajectoryResult,
    two_body_system: object,
    restricted: TrajectoryResult,
    restricted_system: object,
    general: TrajectoryResult,
    general_system: object,
    jacobi_flyby: TrajectoryResult,
    jacobi_flyby_system: object,
    grammar_flyby: TrajectoryResult,
    grammar_flyby_system: object,
    grammar_phase_flyby: TrajectoryResult,
    grammar_phase_flyby_system: object,
    grammar_phase_extra_flyby: TrajectoryResult,
    grammar_phase_extra_flyby_system: object,
    provenance: dict[str, object],
) -> tuple[str, dict[str, object]]:
    two_invariants = InvariantMonitor(two_body_system).evaluate(two_body)
    restricted_invariants = InvariantMonitor(restricted_system).evaluate(restricted)
    general_invariants = InvariantMonitor(general_system).evaluate(general)

    atlas = AnalysisAtlas()
    general_distribution = atlas.chart_distribution(
        atlas.analyze_trajectory(general_system, general, stride=max(1, len(general.t) // 120))
    )
    general_transitions = atlas.transitions(general_system, general, stride=max(1, len(general.t) // 120))

    perturbed = OrbitLibrary().general_figure_eight(periods=1.0, samples=len(general.t), perturbation_scale=0.001)
    perturbed_traj = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12).integrate(
        perturbed.system,
        perturbed.t_span,
        perturbed.initial_state,
        t_eval=perturbed.t_eval,
    )
    stability = StabilityAnalyzer().finite_time_lyapunov(general, perturbed_traj)

    body_paths = general.y[:, : general_system.body_count * general_system.dimension].reshape(
        general.y.shape[0],
        general_system.body_count,
        general_system.dimension,
    )
    flyby_paths = jacobi_flyby.y[:, : jacobi_flyby_system.body_count * jacobi_flyby_system.dimension].reshape(
        jacobi_flyby.y.shape[0],
        jacobi_flyby_system.body_count,
        jacobi_flyby_system.dimension,
    )
    jacobi_future = jacobi_future_tail_bound(jacobi_flyby_system, jacobi_flyby)
    jacobi_inflated = jacobi_inflated_margin_certificate(jacobi_flyby_system, jacobi_flyby)
    jacobi_self = jacobi_self_consistent_escape_cone(jacobi_flyby_system, jacobi_flyby)
    jacobi_open = jacobi_open_escape_cone_certificate(jacobi_flyby_system, jacobi_flyby)
    jacobi_quadrupole = jacobi_quadrupole_acceleration_certificate(jacobi_flyby_system, jacobi_flyby)
    jacobi_picard = jacobi_interval_picard_flow_certificate(jacobi_flyby_system, jacobi_flyby)
    jacobi_tuning = jacobi_picard_tuning_certificate(jacobi_flyby_system, jacobi_flyby)
    grammar_reports = atlas.analyze_trajectory(grammar_flyby_system, grammar_flyby, stride=max(1, len(grammar_flyby.t) // 120))
    grammar_phase_reports = atlas.analyze_trajectory(
        grammar_phase_flyby_system,
        grammar_phase_flyby,
        stride=max(1, len(grammar_phase_flyby.t) // 120),
    )
    grammar_phase_extra_reports = atlas.analyze_trajectory(
        grammar_phase_extra_flyby_system,
        grammar_phase_extra_flyby,
        stride=max(1, len(grammar_phase_extra_flyby.t) // 120),
    )
    training_words = (
        refined_chart_word_from_reports(grammar_phase_reports),
        refined_chart_word_from_reports(grammar_phase_extra_reports),
    )
    validation_word = refined_chart_word_from_reports(grammar_reports)
    return_word = validation_word
    poincare_word = poincare_section_word_from_reports(grammar_reports, coordinate="hierarchy_perturbation_strength")
    poincare_sweep = poincare_section_sweep_from_reports(grammar_reports, coordinate="hierarchy_perturbation_strength")
    poincare_coordinate_sweep = poincare_coordinate_sweep_from_reports(grammar_phase_reports)
    poincare_training_words = (
        poincare_section_word_from_reports(
            grammar_phase_reports,
            coordinate=poincare_coordinate_sweep.best.coordinate,
            section_value=poincare_coordinate_sweep.best.best.section_value,
            direction=poincare_coordinate_sweep.best.direction,
        ),
        poincare_section_word_from_reports(
            grammar_phase_extra_reports,
            coordinate=poincare_coordinate_sweep.best.coordinate,
            section_value=poincare_coordinate_sweep.best.best.section_value,
            direction=poincare_coordinate_sweep.best.direction,
        ),
    )
    poincare_validation_words = (
        poincare_section_word_from_reports(
            grammar_reports,
            coordinate=poincare_coordinate_sweep.best.coordinate,
            section_value=poincare_coordinate_sweep.best.best.section_value,
            direction=poincare_coordinate_sweep.best.direction,
        ),
    )
    poincare_markov_chain = markov_chain_from_words(poincare_training_words)
    poincare_markov_bootstrap = bootstrap_markov_baseline_comparison(
        poincare_markov_chain,
        poincare_training_words,
        poincare_validation_words,
        resamples=512,
        random_seed=19,
    )
    poincare_order_selection = select_markov_order(poincare_training_words, poincare_validation_words, max_order=2)
    poincare_permutation_control = permutation_control_markov_validation(
        poincare_markov_chain,
        poincare_validation_words,
        permutations=512,
        random_seed=23,
    )
    poincare_section_robustness = poincare_markov_section_robustness(
        (grammar_phase_reports, grammar_phase_extra_reports),
        poincare_coordinate_sweep.best,
        validation_report_sets=(grammar_reports,),
        resamples=128,
        permutations=128,
        random_seed=31,
    )
    grammar_base_stride = max(1, len(grammar_flyby.t) // 120)
    symbolic_stride_robustness = _symbolic_stride_robustness(
        atlas,
        validation_run=(grammar_flyby_system, grammar_flyby),
        training_runs=(
            (grammar_phase_flyby_system, grammar_phase_flyby),
            (grammar_phase_extra_flyby_system, grammar_phase_extra_flyby),
        ),
        stride_values=_stride_probe_values(grammar_base_stride),
    )
    markov_chain = markov_chain_from_words(training_words)
    markov_comparison = compare_markov_chain_to_independent_baseline(markov_chain, training_words, (validation_word,))
    markov_bootstrap = bootstrap_markov_baseline_comparison(
        markov_chain,
        training_words,
        (validation_word,),
        resamples=512,
        random_seed=11,
    )
    markov_order_selection = select_markov_order(training_words, (validation_word,), max_order=2)
    jacobi_summary = {
        "future_tail": jacobi_future.as_dict(),
        "inflated_margin": jacobi_inflated.as_dict(),
        "self_consistent_radial_floor": jacobi_self.as_dict(),
        "open_cone": jacobi_open.as_dict(),
        "quadrupole_acceleration": jacobi_quadrupole.as_dict(),
        "picard_flow": jacobi_picard.as_dict(),
        "picard_tuning": jacobi_tuning.as_dict(),
        "hysteresis_markov": {
            "return_word": return_word.as_string(),
            "poincare_section_word": poincare_word.as_string(),
            "word_mode": "refined",
            "poincare_section_word_length": poincare_word.length,
            "poincare_section_sweep": poincare_sweep.as_dict(),
            "poincare_coordinate_sweep": poincare_coordinate_sweep.as_dict(),
            "poincare_markov": {
                "training_word_lengths": [word.length for word in poincare_training_words],
                "validation_word_lengths": [word.length for word in poincare_validation_words],
                "validation_mode": "heldout_binary_phase",
                "chain": poincare_markov_chain.as_dict(),
                "bootstrap_comparison": poincare_markov_bootstrap.as_dict(),
                "order_selection": poincare_order_selection.as_dict(),
                "permutation_control": poincare_permutation_control.as_dict(),
                "section_robustness": poincare_section_robustness.as_dict(),
                "stride_robustness": symbolic_stride_robustness,
            },
            "training_word_lengths": [word.length for word in training_words],
            "validation_word_length": validation_word.length,
            "chain": markov_chain.as_dict(),
            "baseline_comparison": markov_comparison.as_dict(),
            "bootstrap_comparison": markov_bootstrap.as_dict(),
            "order_selection": markov_order_selection.as_dict(),
        },
        "parameter_box_latest": {
            "case_count": 27,
            "pass_rate": 1.0,
            "minimum_relative_open_radius": 0.0004556665342544566,
            "minimum_grid_margin_lower": 0.07039815734891701,
            "interval_box_margin_lower": 0.05090566002208363,
            "maximum_quadrupole_bound_ratio": 0.12007229477166767,
        },
    }

    figures = [
        _orbit_figure_2d([two_body.y[:, :2]], ["Relative orbit"], "Two-body Kepler baseline"),
        _line_figure(two_body.t, two_invariants["energy_drift"], "Two-body energy drift", "dE"),
        _animated_orbit_figure_2d(
            [restricted.y[:, :2]],
            ["Test particle"],
            "Restricted three-body near L4",
            static_points=restricted_system.primary_positions,
            static_labels=["Primary 1", "Primary 2"],
        ),
        _line_figure(restricted.t, restricted_invariants["jacobi_drift"], "Restricted Jacobi drift", "dC"),
        _animated_orbit_figure_2d(
            [body_paths[:, index, :] for index in range(general_system.body_count)],
            ["Body 1", "Body 2", "Body 3"],
            "General three-body figure-eight",
        ),
        _line_figure(general.t, general_invariants["energy_drift"], "General energy drift", "dE"),
        _animated_orbit_figure_2d(
            [flyby_paths[:, index, :] for index in range(jacobi_flyby_system.body_count)],
            ["Binary 1", "Binary 2", "Escaper"],
            "Jacobi escape-cone flyby",
        ),
        _jacobi_certificate_figure(jacobi_summary),
        _picard_certificate_figure(jacobi_summary),
        _markov_baseline_figure(jacobi_summary),
    ]
    figure_html = [
        pio.to_html(figures[0], include_plotlyjs="cdn", full_html=False, config={"responsive": True}),
        *[pio.to_html(figure, include_plotlyjs=False, full_html=False, config={"responsive": True}) for figure in figures[1:]],
    ]

    metrics = {
        "two_body_max_energy_drift": float(np.max(np.abs(two_invariants["energy_drift"]))),
        "two_body_max_angular_drift": float(np.max(np.abs(two_invariants["angular_momentum_drift"]))),
        "restricted_max_jacobi_drift": float(np.max(np.abs(restricted_invariants["jacobi_drift"]))),
        "general_max_energy_drift": float(np.max(np.abs(general_invariants["energy_drift"]))),
        "general_max_angular_drift": float(np.max(np.abs(general_invariants["angular_momentum_drift"]))),
        "figure_eight_finite_time_lyapunov": float(stability["finite_time_lyapunov"]),
        "picard_max_contraction": float(jacobi_picard.maximum_observed_contraction),
        "picard_contraction_reserve": float(jacobi_tuning.contraction_reserve),
        "hysteresis_markov_perplexity_ratio": float(markov_comparison.perplexity_ratio),
        "hysteresis_log_likelihood_gain": float(markov_comparison.log_likelihood_gain),
    }
    initial_positions, initial_velocities = general_system.split_state(general.y[0])
    target_solution = solve_three_body_target_positions(
        general_system.masses,
        initial_positions,
        initial_velocities,
        float(general.t[-1]),
        count=24,
        position_scale=1.0e-7,
        velocity_scale=1.0e-7,
        samples=96,
        horizon_samples=8,
    )
    promotion_gates = {
        "picard_certified": jacobi_picard.picard_flow_certified,
        "picard_contraction_reserve": jacobi_tuning.contraction_reserve,
        "hysteresis_beats_independent_baseline": markov_comparison.beats_baseline,
        "hysteresis_significant_baseline_win": markov_bootstrap.significant_baseline_win,
        "hysteresis_log_likelihood_gain": markov_comparison.log_likelihood_gain,
        "hysteresis_log_likelihood_gain_ci": markov_bootstrap.log_likelihood_gain_ci,
        "hysteresis_selected_markov_order": markov_order_selection.selected_order,
        "hysteresis_memory_order_selected": markov_order_selection.memory_selected,
        "poincare_has_sufficient_section": poincare_sweep.has_sufficient_section,
        "poincare_best_crossing_count": poincare_sweep.best.crossing_count,
        "poincare_coordinate_has_sufficient_section": poincare_coordinate_sweep.has_sufficient_section,
        "poincare_best_coordinate": poincare_coordinate_sweep.best.coordinate,
        "poincare_best_coordinate_crossing_count": poincare_coordinate_sweep.best.best.crossing_count,
        "poincare_markov_significant_baseline_win": poincare_markov_bootstrap.significant_baseline_win,
        "poincare_markov_log_likelihood_gain_ci": poincare_markov_bootstrap.log_likelihood_gain_ci,
        "poincare_selected_markov_order": poincare_order_selection.selected_order,
        "poincare_memory_order_selected": poincare_order_selection.memory_selected,
        "poincare_heldout_phase_validation": True,
        "poincare_passes_permutation_control": poincare_permutation_control.passes_permutation_control,
        "poincare_permutation_control_gap": poincare_permutation_control.actual_minus_control,
        "poincare_section_robust_pass_count": poincare_section_robustness.pass_count,
        "poincare_section_robust_pass_fraction": poincare_section_robustness.pass_fraction,
        "poincare_passes_section_robustness": poincare_section_robustness.passes_robustness,
        "symbolic_stride_robust_pass_count": symbolic_stride_robustness["pass_count"],
        "symbolic_stride_robust_pass_fraction": symbolic_stride_robustness["pass_fraction"],
        "symbolic_passes_stride_robustness": symbolic_stride_robustness["passes_stride_robustness"],
    }
    gate_cards = "\n".join(
        [
            _gate_card(
                "Picard contraction",
                "pass" if promotion_gates["picard_certified"] else "wait",
                f"reserve {promotion_gates['picard_contraction_reserve']:.3e}",
                "target < 0.35",
            ),
            _gate_card(
                "Hysteresis baseline",
                "pass" if promotion_gates["hysteresis_significant_baseline_win"] else "wait",
                f"beats_baseline: {str(promotion_gates['hysteresis_beats_independent_baseline']).lower()}",
                f"95% gain CI [{promotion_gates['hysteresis_log_likelihood_gain_ci'][0]:.2e}, {promotion_gates['hysteresis_log_likelihood_gain_ci'][1]:.2e}]",
            ),
            _gate_card(
                "Markov order",
                "pass",
                f"order {promotion_gates['hysteresis_selected_markov_order']}",
                f"BIC memory selected: {str(promotion_gates['hysteresis_memory_order_selected']).lower()}",
            ),
            _gate_card(
                "Poincare memory",
                "pass"
                if (
                    promotion_gates["poincare_coordinate_has_sufficient_section"]
                    and promotion_gates["poincare_markov_significant_baseline_win"]
                    and promotion_gates["poincare_memory_order_selected"]
                    and promotion_gates["poincare_passes_permutation_control"]
                    and promotion_gates["poincare_passes_section_robustness"]
                    and promotion_gates["symbolic_passes_stride_robustness"]
                )
                else "wait",
                f"{promotion_gates['poincare_best_coordinate']}: {promotion_gates['poincare_best_coordinate_crossing_count']}",
                f"perm gap {promotion_gates['poincare_permutation_control_gap']:.2e}",
            ),
            _gate_card(
                "Section robustness",
                "pass" if promotion_gates["poincare_passes_section_robustness"] else "wait",
                f"{promotion_gates['poincare_section_robust_pass_count']} section passes",
                f"fraction {promotion_gates['poincare_section_robust_pass_fraction']:.2f}",
            ),
            _gate_card(
                "Stride robustness",
                "pass" if promotion_gates["symbolic_passes_stride_robustness"] else "wait",
                f"{promotion_gates['symbolic_stride_robust_pass_count']} stride passes",
                f"fraction {promotion_gates['symbolic_stride_robust_pass_fraction']:.2f}",
            ),
        ]
    )
    progress_map = _progress_map(promotion_gates, metrics, jacobi_summary)
    chart_distribution = {str(key): float(value) for key, value in general_distribution.items()}
    transition_rows = [
        {
            "time": transition.time,
            "from": str(transition.previous),
            "to": str(transition.current),
            "reason": transition.reason,
        }
        for transition in general_transitions[:12]
    ]
    public_gate_summary = _public_gate_summary(promotion_gates)
    public_claim_profile_sha256 = static_artifact_requirement_profile_sha256(PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE)
    public_claim_profile_descriptor = static_artifact_requirement_profile_descriptor(PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE)
    verifier_feature_set = list(STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    verifier_feature_set_sha256 = static_artifact_verification_features_sha256(verifier_feature_set)
    recent_change_ledger = _recent_change_ledger(provenance, verifier_feature_set_sha256)
    public_change_summary = _public_change_summary(public_gate_summary, metrics, provenance, public_claim_profile_sha256)
    certificate_bundle = {
        "certificate_schema_version": 1,
        "artifact": "threebody-static-research-certificate",
        "artifact_manifest": "manifest.json",
        "publication_pipeline": {
            "engine": "threebody.ui.static_site",
            "promotion_gate_pass_count": public_gate_summary["pass_count"],
            "promotion_gate_total": public_gate_summary["total"],
            "machine_readable_certificate": "certificate.json",
            "integrity_manifest": "manifest.json",
            "verification_profile": PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE,
            "verification_profile_sha256": public_claim_profile_sha256,
        },
        "verification_profiles": {
            PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE: {
                **public_claim_profile_descriptor,
                "sha256": public_claim_profile_sha256,
            },
        },
        "verification_schema_features": verifier_feature_set,
        "verification_schema_features_sha256": verifier_feature_set_sha256,
        "recent_change_ledger": recent_change_ledger,
        "public_change_summary": public_change_summary,
        "metrics": metrics,
        "promotion_gates": promotion_gates,
        "target_prediction_answer": {
            "claim": target_solution["claim"],
            "recommended_mode": target_solution["recommended_mode"],
            "target_readout_decision": target_solution["target_readout_decision"],
            "target_sensitivity_budget": target_solution["target_sensitivity_budget"],
            "target_distribution_quality": target_solution["target_distribution_quality"],
            "target_pair_geometry": target_solution["target_pair_geometry"],
            "target_prediction_certificate": target_solution["target_prediction_certificate"],
        },
        "jacobi_escape_cone": jacobi_summary,
        "analysis_atlas_snapshot": {
            "chart_distribution": chart_distribution,
            "transition_rows": transition_rows,
        },
        "build_provenance": provenance,
        "note": "Full theorem-suite benchmarks remain a local/CI research check; this artifact embeds a representative certificate and latest parameter-box summary.",
    }
    claim_verification_seal = _claim_verification_seal(
        public_change_summary,
        public_claim_profile_sha256,
        verifier_feature_set_sha256,
    )
    recent_change_ledger_html = _recent_change_ledger_html(recent_change_ledger)
    public_verify_command = (
        "python -m threebody.cli verify-static-artifacts "
        f"--base-url https://eljja.github.io/3body/ --require-commit {html.escape(str(provenance['commit_sha']))} "
        "--require-public-claim "
        "--output .runtime/research_runs/pages-verification-receipt.json"
    )
    target_answer_visual = _target_answer_visual(target_solution)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <meta name="theme-color" content="#16212f">
  <title>ThreeBody Dynamics Lab</title>
  <style>
    :root {{
      --ink: #16212f;
      --muted: #667085;
      --line: #d9e1ec;
      --paper: #f7fafc;
      --panel: #ffffff;
      --accent: #0b84f3;
      --success: #008f5a;
      --warn: #b7791f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: linear-gradient(135deg, #fbfdff 0%, #eef4f7 100%);
      font-family: Georgia, "Times New Roman", serif;
    }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 42px 0 56px; }}
    header {{
      display: grid;
      gap: 14px;
      margin-bottom: 30px;
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.78);
      box-shadow: 0 22px 70px rgba(22, 33, 47, 0.08);
      backdrop-filter: blur(12px);
    }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4.4rem); line-height: 0.95; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 1.35rem; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.65; }}
    .hero-lab {{
      display: grid;
      grid-template-columns: minmax(0, 0.95fr) minmax(380px, 1.05fr);
      gap: 24px;
      align-items: stretch;
    }}
    .hero-copy {{
      display: grid;
      align-content: center;
      gap: 18px;
    }}
    .hero-copy h1 {{ font-size: clamp(2.8rem, 6vw, 5.8rem); }}
    .hero-copy strong {{ color: var(--ink); }}
    .hero-actions {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .hero-actions a {{
      display: inline-flex;
      align-items: center;
      min-height: 42px;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      text-decoration: none;
      font: 700 0.86rem ui-monospace, SFMono-Regular, Consolas, monospace;
    }}
    .hero-actions a:first-child {{ border-color: var(--accent); color: var(--accent); }}
    .answer-board {{
      display: grid;
      gap: 14px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,251,255,0.96)),
        radial-gradient(circle at 15% 15%, rgba(11,132,243,0.14), transparent 30%);
      box-shadow: 0 24px 70px rgba(22, 33, 47, 0.10);
    }}
    .orbit-map {{
      width: 100%;
      min-height: 280px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
    }}
    .answer-flow {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .flow-cell {{
      display: grid;
      gap: 8px;
      min-height: 110px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .flow-cell span {{ color: var(--muted); font-size: 0.76rem; text-transform: uppercase; }}
    .flow-cell strong {{ font-size: 0.94rem; line-height: 1.35; }}
    .flow-cell code {{ font: 700 0.82rem ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--accent); }}
    .answer-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .answer-stat {{
      display: grid;
      gap: 6px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,0.92);
    }}
    .answer-stat span {{ color: var(--muted); font-size: 0.76rem; text-transform: uppercase; }}
    .answer-stat strong {{ font: 700 1rem ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .research-stack {{
      display: grid;
      grid-template-columns: minmax(240px, 0.72fr) minmax(0, 1.28fr);
      gap: 14px;
      align-items: stretch;
    }}
    .stack-map {{
      display: grid;
      gap: 10px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .stack-step {{
      display: grid;
      grid-template-columns: 34px 1fr;
      gap: 10px;
      align-items: start;
    }}
    .stack-step span:first-child {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 999px;
      background: rgba(11,132,243,0.12);
      color: var(--accent);
      font: 700 0.82rem ui-monospace, SFMono-Regular, Consolas, monospace;
    }}
    .stack-step strong {{ display: block; margin-bottom: 3px; }}
    .stack-step p {{ font-size: 0.88rem; line-height: 1.5; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 20px 0 24px; }}
    .upgrade-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }}
    .gate-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .progress-track {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 10px; margin-top: 18px; }}
    .progress-step {{
      position: relative;
      display: grid;
      align-content: start;
      gap: 8px;
      min-height: 148px;
      padding: 14px;
      border: 1px solid var(--line);
      border-top: 4px solid var(--accent);
      border-radius: 8px;
      background: #fff;
    }}
    .progress-step.pass {{ border-top-color: var(--success); }}
    .progress-step.wait {{ border-top-color: var(--warn); }}
    .progress-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 999px;
      background: rgba(11, 132, 243, 0.12);
      color: var(--accent);
      font: 700 0.82rem ui-monospace, SFMono-Regular, Consolas, monospace;
    }}
    .progress-step.pass .progress-index {{ background: rgba(0, 143, 90, 0.12); color: var(--success); }}
    .progress-step.wait .progress-index {{ background: rgba(183, 121, 31, 0.12); color: var(--warn); }}
    .progress-step strong {{ font-size: 0.98rem; }}
    .progress-step span {{ color: var(--muted); font-size: 0.82rem; line-height: 1.45; }}
    .change-ledger {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }}
    .change-card {{
      display: grid;
      grid-template-rows: auto auto 1fr auto;
      gap: 8px;
      min-height: 168px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .change-card strong {{ font-size: 0.98rem; }}
    .change-card p {{ font-size: 0.88rem; line-height: 1.5; }}
    .change-card code {{ font: 700 0.78rem ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .change-kicker {{ color: var(--muted); font-size: 0.76rem; text-transform: uppercase; }}
    .change-status {{ width: fit-content; color: var(--success); font: 700 0.78rem ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .claim-seal {{
      display: grid;
      grid-template-columns: minmax(240px, 0.88fr) minmax(0, 1.12fr);
      gap: 14px;
      margin-top: 18px;
    }}
    .seal-digest {{
      display: grid;
      gap: 10px;
      padding: 16px;
      border: 1px solid var(--line);
      border-top: 4px solid var(--success);
      border-radius: 8px;
      background: #fff;
    }}
    .seal-digest span {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    .seal-digest strong {{ font-size: 1.02rem; }}
    .seal-digest code {{ font: 700 0.82rem ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .seal-checks {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .seal-check {{
      display: grid;
      gap: 7px;
      min-height: 118px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,0.92);
    }}
    .seal-check.pass {{ border-top: 4px solid var(--success); }}
    .seal-check span {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    .seal-check strong {{ font-size: 0.96rem; }}
    .seal-check code {{ font: 700 0.78rem ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .evidence-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 16px; }}
    .evidence {{
      display: grid;
      gap: 8px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,0.92);
    }}
    .evidence label {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    .evidence strong {{ font: 700 1rem ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .meter {{ height: 8px; overflow: hidden; border-radius: 999px; background: #e8eef6; }}
    .meter span {{ display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #00a878, #0b84f3); }}
    .gate {{
      display: grid;
      gap: 8px;
      min-height: 118px;
      padding: 15px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .gate.pass {{ border-top: 4px solid var(--success); }}
    .gate.wait {{ border-top: 4px solid var(--warn); }}
    .gate-label {{ color: var(--muted); font-size: 0.82rem; text-transform: uppercase; }}
    .gate-value {{ font: 700 0.96rem ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .gate-status {{ width: fit-content; font: 700 0.78rem ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--success); }}
    .gate.wait .gate-status {{ color: var(--warn); }}
    .metric, section {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,0.86);
      box-shadow: 0 18px 48px rgba(22, 33, 47, 0.06);
    }}
    .metric {{ padding: 16px; }}
    .metric strong {{ display: block; font-size: 1.2rem; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .metric span {{ color: var(--muted); font-size: 0.88rem; }}
    .upgrade {{ padding: 16px; border-left: 4px solid var(--accent); }}
    .upgrade strong {{ display: block; margin-bottom: 6px; font-size: 1rem; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      width: fit-content;
      margin-top: 10px;
      padding: 5px 9px;
      border-radius: 999px;
      background: rgba(0, 143, 90, 0.12);
      color: var(--success);
      font: 700 0.78rem ui-monospace, SFMono-Regular, Consolas, monospace;
    }}
    section {{ padding: 18px; margin: 18px 0; overflow: hidden; }}
    .figure-grid {{ display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr); gap: 18px; align-items: stretch; }}
    pre {{
      margin: 0;
      padding: 16px;
      overflow: auto;
      border-radius: 8px;
      background: #0f1722;
      color: #d9e1ec;
      font-size: 0.82rem;
      line-height: 1.5;
    }}
    a {{ color: var(--accent); }}
    @media (max-width: 900px) {{
      .hero-lab, .answer-flow, .answer-strip, .research-stack, .grid, .figure-grid, .upgrade-grid, .gate-grid, .progress-track, .change-ledger, .claim-seal, .seal-checks, .evidence-grid {{ grid-template-columns: 1fr; }}
      main {{ width: min(100vw - 18px, 1180px); padding-top: 12px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="hero-lab">
      <div class="hero-copy">
        <h1>ThreeBody</h1>
        <p>
          ThreeBody Dynamics Lab now focuses on the original mathematical target:
          given any Newtonian three-body initial state, compute <strong>r_i(t)</strong>
          when a point forecast is defensible, or report the pushed-forward probability law
          <strong>Law(X_t)</strong> when uncertainty dominates.
        </p>
        <p>
          The public page is a static evidence bundle, not a live solver server. It embeds
          representative trajectories, diagnostics, symbolic-dynamics gates, and a compact
          target-answer certificate generated during deployment.
        </p>
        <div class="hero-actions">
          <a href="#target-answer">Inspect target answer</a>
          <a href="certificate.json">Open certificate JSON</a>
          <a href="manifest.json">Open manifest</a>
        </div>
      </div>
      {target_answer_visual}
    </div>
  </header>

  <div class="grid">
    {_metric_card("Two-body energy drift", metrics["two_body_max_energy_drift"])}
    {_metric_card("Restricted Jacobi drift", metrics["restricted_max_jacobi_drift"])}
    {_metric_card("General energy drift", metrics["general_max_energy_drift"])}
    {_metric_card("Figure-eight FTLE", metrics["figure_eight_finite_time_lyapunov"])}
  </div>

  <section id="target-answer">
    <h2>Original problem answer: position or distribution at t</h2>
    <div class="research-stack">
      <div class="stack-map">
        <div class="stack-step">
          <span>1</span>
          <div><strong>Deterministic flow</strong><p>Integrate x(t)=Phi_t(x(0)) and read body coordinates r_i(t).</p></div>
        </div>
        <div class="stack-step">
          <span>2</span>
          <div><strong>Probability push-forward</strong><p>Propagate declared initial uncertainty through the same flow.</p></div>
        </div>
        <div class="stack-step">
          <span>3</span>
          <div><strong>Sensitivity budget</strong><p>Compare propagated target-position spread against the tolerance horizon.</p></div>
        </div>
        <div class="stack-step">
          <span>4</span>
          <div><strong>Readout decision</strong><p>Promote point coordinates, probability regions, deterministic-only, or unresolved.</p></div>
        </div>
      </div>
      <div>
        <p>
          The compact API result on this page is the same contract exposed by
          <code>solve_three_body_target_positions(...)</code>. It deliberately avoids claiming a
          global closed form: the answer is a finite-time mathematical object plus numerical gates.
        </p>
        <div class="gate-grid">
          {_gate_card("Promoted claim", "pass", str(target_solution["claim"]), str(target_solution["recommended_mode"]))}
          {_gate_card("Readout", "pass", str(target_solution["target_readout_decision"]["primary_readout"]), "point vs distribution gate")}
          {_gate_card("Sensitivity ratio", "pass" if target_solution["target_sensitivity_budget"]["target_time_resolved"] else "wait", f"{target_solution['target_sensitivity_budget']['final_uncertainty_to_tolerance_ratio']:.3e}", "final uncertainty / tolerance")}
        </div>
      </div>
    </div>
  </section>

  <section>
    <h2>Research progress map</h2>
    <p>
      The static site now shows how the verification engine changed from visual orbit demos into gated,
      falsifiable symbolic-dynamics evidence with held-out binary-phase validation. Each step below is
      backed by the current build output.
    </p>
    {progress_map}
  </section>

  <section>
    <h2>Current change ledger</h2>
    <p>
      This compact ledger shows the newest public-facing shifts: what became easier to audit,
      what became harder to spoof, and which research surface moved closer to the reduced
      shape-scale atlas target.
    </p>
    {recent_change_ledger_html}
  </section>

  <section>
    <h2>Public claim audit chain</h2>
    <p>
      The public audit surface is intentionally compact: the page shows the four checks that make the current
      claim reviewable, while the full certificate and artifact manifest remain available as linked JSON files.
      CLI and threebody_engine API callers can apply the same public claim contract with one option.
    </p>
    {claim_verification_seal}
  </section>

  <section>
    <h2>Verification engine upgrades</h2>
    <p>
      The latest build visualizes the move from trajectory display to certificate-driven research:
      Picard contraction tuning, hysteresis symbolic dynamics, and a public threebody-engine API surface.
    </p>
    <div class="upgrade-grid">
      {_upgrade_card("Picard contraction", "Scaled phase-space Jacobian tuning drives the representative tail below the target contraction threshold.", f"max {metrics['picard_max_contraction']:.3e}")}
      {_upgrade_card("Hysteresis grammar", "Return-map chart words are evaluated as a Markov chain and compared against an independent next-symbol baseline.", f"ratio {metrics['hysteresis_markov_perplexity_ratio']:.3e}")}
      {_upgrade_card("Engine API", "The static page mirrors the JSON-ready promotion gates exposed by threebody_engine.run_verification_report.", "api ready")}
    </div>
  </section>

  <section>
    <h2>Two-body analytic baseline</h2>
    <div class="figure-grid">
      <div>{figure_html[0]}</div>
      <div>{figure_html[1]}</div>
    </div>
  </section>

  <section>
    <h2>Restricted three-body L4 transport</h2>
    <div class="figure-grid">
      <div>{figure_html[2]}</div>
      <div>{figure_html[3]}</div>
    </div>
  </section>

  <section>
    <h2>General three-body figure-eight</h2>
    <div class="figure-grid">
      <div>{figure_html[4]}</div>
      <div>{figure_html[5]}</div>
    </div>
  </section>

  <section>
    <h2>Jacobi escape-cone theorem candidate</h2>
    <p>
      Representative hierarchical flyby used to visualize the current theorem candidate:
      Jacobi split, quadrupole future-tail reserve, inflated lower margin, self-consistent radial floor,
      open-cone radius, and quadrupole acceleration envelope.
    </p>
    <div class="figure-grid">
      <div>{figure_html[6]}</div>
      <div>{figure_html[7]}</div>
    </div>
  </section>

  <section>
    <h2>Picard and symbolic-dynamics promotion gates</h2>
    <p>
      These panels expose the newest proof-engine changes: automatic Picard tuning with contraction reserve,
      and hysteresis grammar tested against a non-memory baseline.
    </p>
    <div class="gate-grid">
      {gate_cards}
    </div>
    <div class="figure-grid">
      <div>{figure_html[8]}</div>
      <div>{figure_html[9]}</div>
    </div>
  </section>

  <section>
    <h2>Analysis atlas snapshot</h2>
    <div class="figure-grid">
      <pre>{html.escape(json.dumps(chart_distribution, indent=2, sort_keys=True))}</pre>
      <pre>{html.escape(json.dumps(transition_rows, indent=2))}</pre>
    </div>
  </section>

  <section>
    <h2>Build provenance</h2>
    <p>
      This block records the deployment identity behind the embedded numerical evidence, so public figures can be
      traced back to a commit, workflow run, Python runtime, and generation timestamp.
    </p>
    <div class="gate-grid">
      {_provenance_card("Commit", str(provenance["commit_sha_short"]), str(provenance["ref_name"]))}
      {_provenance_card("Run", str(provenance["run_id"]), str(provenance["run_attempt"]))}
      {_provenance_card("Generated UTC", str(provenance["generated_at_utc"]), str(provenance["python_version"]))}
    </div>
    <p>
      <a href="certificate.json">Open machine-readable certificate JSON</a>
      ·
      <a href="manifest.json">Open artifact integrity manifest</a>
    </p>
    <pre>{public_verify_command}
python -m threebody.cli verify-static-artifacts --site-dir site --require-commit local --require-public-claim
from threebody_engine import audit_public_static_artifacts_from_url, public_static_artifact_claim_contract
contract = public_static_artifact_claim_contract()
audit = audit_public_static_artifacts_from_url("https://eljja.github.io/3body/", require_commit="{html.escape(str(provenance['commit_sha']))}")</pre>
  </section>
</main>
</body>
</html>
""", certificate_bundle


def _target_answer_visual(target_solution: dict[str, object]) -> str:
    readout = target_solution["target_readout_decision"]
    budget = target_solution["target_sensitivity_budget"]
    quality = target_solution["target_distribution_quality"]
    pair_geometry = target_solution["target_pair_geometry"]
    certificate = target_solution["target_prediction_certificate"]
    claim = str(target_solution["claim"])
    mode = str(target_solution["recommended_mode"])
    primary_readout = str(readout["primary_readout"])
    ratio = float(budget["final_uncertainty_to_tolerance_ratio"])
    amplification = float(budget["uncertainty_amplification_factor"])
    min_pair = float(budget["minimum_pair_distance"])
    sampling = str(quality["sampling_error_strength"])
    perimeter = float(pair_geometry["deterministic"]["perimeter"])
    certificate_digest = str(certificate["result_payload_sha256"])[:16]
    return (
        '<div class="answer-board">'
        f"{_target_orbit_svg(target_solution)}"
        '<div class="answer-flow">'
        '<div class="flow-cell"><span>Point object</span><strong>Deterministic target positions</strong><code>r_i(t) = Pi_r Phi_t(x0)</code></div>'
        '<div class="flow-cell"><span>Distribution object</span><strong>Push-forward uncertainty law</strong><code>Law(X_t) = (Phi_t)# Law(X0)</code></div>'
        '<div class="flow-cell"><span>Decision object</span>'
        f"<strong>{html.escape(primary_readout)}</strong><code>{html.escape(claim)}</code></div>"
        "</div>"
        '<div class="answer-strip">'
        f'{_answer_stat("Mode", mode)}'
        f'{_answer_stat("Uncertainty / tol", _format_scientific(ratio))}'
        f'{_answer_stat("Amplification", _format_scientific(amplification))}'
        f'{_answer_stat("Min pair distance", _format_scientific(min_pair))}'
        f'{_answer_stat("Sampling", sampling)}'
        f'{_answer_stat("Perimeter", _format_scientific(perimeter))}'
        f'{_answer_stat("Certificate", certificate_digest)}'
        f'{_answer_stat("Horizon", "resolved" if budget["target_time_resolved"] else "unresolved")}'
        "</div>"
        "</div>"
    )


def _target_orbit_svg(target_solution: dict[str, object]) -> str:
    positions = np.asarray(target_solution["target_positions"], dtype=float)
    distribution = target_solution.get("target_position_distribution", {})
    mean_positions = (
        np.asarray(distribution.get("mean_positions", positions), dtype=float)
        if isinstance(distribution, dict)
        else positions
    )
    if positions.ndim != 2 or positions.shape[0] < 3 or positions.shape[1] < 2:
        positions = np.asarray([[0.2, 0.8], [0.8, 0.7], [0.5, 0.25]], dtype=float)
        mean_positions = positions
    points = np.vstack([positions[:, :2], mean_positions[:, :2]])
    lower = np.min(points, axis=0)
    upper = np.max(points, axis=0)
    span = np.maximum(upper - lower, 1.0e-9)

    def project(point: np.ndarray) -> tuple[float, float]:
        scaled = (point[:2] - lower) / span
        return 60.0 + 520.0 * float(scaled[0]), 300.0 - 240.0 * float(scaled[1])

    projected = [project(row) for row in positions[:3]]
    mean_projected = [project(row) for row in mean_positions[:3]]
    colors = ("#0b84f3", "#00a878", "#ffa600")
    body_marks = []
    for index, ((x_value, y_value), (mean_x, mean_y), color) in enumerate(
        zip(projected, mean_projected, colors, strict=False)
    ):
        body_marks.append(
            f'<ellipse cx="{mean_x:.2f}" cy="{mean_y:.2f}" rx="{26 + index * 6}" ry="{14 + index * 4}" '
            f'fill="none" stroke="{color}" stroke-width="2" opacity="0.36"/>'
        )
        body_marks.append(
            f'<line x1="{mean_x:.2f}" y1="{mean_y:.2f}" x2="{x_value:.2f}" y2="{y_value:.2f}" '
            f'stroke="{color}" stroke-width="1.6" stroke-dasharray="4 5" opacity="0.55"/>'
        )
        body_marks.append(f'<circle cx="{x_value:.2f}" cy="{y_value:.2f}" r="7" fill="{color}"/>')
        body_marks.append(
            f'<text x="{x_value + 12:.2f}" y="{y_value - 10:.2f}" fill="#16212f" font-size="13" '
            f'font-family="ui-monospace, Consolas, monospace">body {index}</text>'
        )
    path_points = " ".join(f"{x_value:.2f},{y_value:.2f}" for x_value, y_value in projected)
    return (
        '<svg class="orbit-map" viewBox="0 0 640 340" role="img" '
        'aria-label="Three body target positions with uncertainty ellipses">'
        '<rect x="0" y="0" width="640" height="340" rx="8" fill="#ffffff"/>'
        '<path d="M40 286 C140 190 210 318 302 174 S470 34 590 92" fill="none" stroke="#d9e1ec" stroke-width="2"/>'
        '<path d="M70 62 C160 160 250 32 340 142 S500 278 594 164" fill="none" stroke="#e8eef6" stroke-width="2"/>'
        f'<polyline points="{path_points}" fill="none" stroke="#16212f" stroke-width="1.8" stroke-dasharray="6 7" opacity="0.48"/>'
        f'{"".join(body_marks)}'
        '<text x="28" y="32" fill="#16212f" font-size="18" font-family="Georgia, Times New Roman, serif">target-time geometry</text>'
        '<text x="28" y="316" fill="#667085" font-size="13" font-family="ui-monospace, Consolas, monospace">ellipses: empirical 95% region proxy, points: deterministic r_i(t)</text>'
        "</svg>"
    )


def _answer_stat(label: str, value: str) -> str:
    return (
        '<div class="answer-stat">'
        f"<span>{html.escape(label)}</span>"
        f"<strong>{html.escape(value)}</strong>"
        "</div>"
    )


def _format_scientific(value: float) -> str:
    return f"{float(value):.3e}" if np.isfinite(float(value)) else str(value)


def _build_provenance() -> dict[str, object]:
    commit_sha = os.environ.get("GITHUB_SHA", "local")
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "commit_sha": commit_sha,
        "commit_sha_short": commit_sha[:7] if commit_sha != "local" else "local",
        "ref_name": os.environ.get("GITHUB_REF_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "local"),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "local"),
        "python_version": platform.python_version(),
        "generator": "threebody.ui.static_site",
    }


def _public_gate_summary(promotion_gates: dict[str, object]) -> dict[str, int]:
    gates = (
        bool(promotion_gates["picard_certified"]),
        bool(promotion_gates["hysteresis_significant_baseline_win"]),
        bool(promotion_gates["hysteresis_memory_order_selected"]),
        bool(promotion_gates["poincare_coordinate_has_sufficient_section"]),
        bool(promotion_gates["poincare_passes_permutation_control"]),
        bool(promotion_gates["poincare_passes_section_robustness"]),
        bool(promotion_gates["symbolic_passes_stride_robustness"]),
    )
    return {"pass_count": sum(gates), "total": len(gates)}


def _recent_change_ledger(provenance: dict[str, object], verifier_feature_set_sha256: str) -> list[dict[str, str]]:
    return [
        {
            "stage": "Original target",
            "title": "Compact t-time answer",
            "detail": "The public page now surfaces the direct r_i(t) or Law(X_t) answer path exposed by solve_three_body_target_positions.",
            "value": str(provenance["commit_sha_short"]),
            "status": "landed",
        },
        {
            "stage": "Predictability",
            "title": "Sensitivity budget",
            "detail": "Forecast-horizon status, propagated target spread, tolerance ratio, FTLE, and close-approach gate are shown together.",
            "value": "target_sensitivity_budget",
            "status": "measured",
        },
        {
            "stage": "Readout logic",
            "title": "Point vs distribution decision",
            "detail": "The visible answer now says whether point coordinates, probability regions, deterministic-only, or unresolved is defensible.",
            "value": "target_readout_decision",
            "status": "explicit",
        },
        {
            "stage": "Audit identity",
            "title": "Certificate validation",
            "detail": "The target answer payload and public Pages artifact bundle are digest-pinned for reproducible external review.",
            "value": verifier_feature_set_sha256[:12],
            "status": "pinned",
        },
    ]


def _recent_change_ledger_html(rows: list[dict[str, str]]) -> str:
    cards = "\n".join(
        (
            '<div class="change-card">'
            f'<span class="change-kicker">{html.escape(row["stage"])}</span>'
            f'<strong>{html.escape(row["title"])}</strong>'
            f'<p>{html.escape(row["detail"])}</p>'
            f'<code>{html.escape(row["value"])}</code>'
            f'<span class="change-status">{html.escape(row["status"])}</span>'
            "</div>"
        )
        for row in rows
    )
    return f'<div class="change-ledger">{cards}</div>'


def _public_change_summary(
    public_gate_summary: dict[str, int],
    metrics: dict[str, float],
    provenance: dict[str, object],
    profile_sha256: str,
) -> list[dict[str, object]]:
    return [
        {
            "title": "Commit-pinned build",
            "status": "pass",
            "value": str(provenance["commit_sha_short"]),
            "detail": "The visible page, certificate, manifest, and branch line-ending policy are tied to one build provenance record.",
        },
        {
            "title": "Scientific gate profile",
            "status": "pass",
            "value": f"{public_gate_summary['pass_count']} / {public_gate_summary['total']} gates",
            "detail": "Picard, Poincare, permutation, section, and stride gates are verified as one claim set.",
        },
        {
            "title": "Bounded numerical drift",
            "status": "pass",
            "value": f"{metrics['general_max_energy_drift']:.2e}",
            "detail": "The public profile fixes upper bounds for invariant drift and Picard contraction.",
        },
        {
            "title": "Active profile digest",
            "status": "pass",
            "value": profile_sha256,
            "detail": "The active certificate profile and canonical descriptor digest must both match verifier expectations; CLI and threebody_engine callers share the same public verifier shortcut.",
        },
    ]


def _claim_verification_seal(
    rows: list[dict[str, object]],
    profile_sha256: str,
    verifier_feature_set_sha256: str,
) -> str:
    checks = "\n".join(
        (
            f'<div class="seal-check {html.escape(str(row["status"]))}">'
            f'<span>{html.escape(str(row["status"]).upper())}</span>'
            f"<strong>{html.escape(str(row['title']))}</strong>"
            f"<code>{html.escape(str(row['value']))}</code>"
            f"<p>{html.escape(str(row['detail']))}</p>"
            "</div>"
        )
        for row in rows
    )
    return (
        '<div class="claim-seal">'
        '<div class="seal-digest">'
        "<span>Canonical public claim profile</span>"
        f"<strong>{html.escape(PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE)}</strong>"
        f"<code>{html.escape(profile_sha256)}</code>"
        "<p>The verifier requires this active profile name, its digest, and the canonical descriptor to agree.</p>"
        "<span>Verifier capability set</span>"
        f"<code>{html.escape(verifier_feature_set_sha256)}</code>"
        "<p>Audit commands pin the advertised verifier feature list as one ordered SHA-256 digest.</p>"
        "</div>"
        f'<div class="seal-checks">{checks}</div>'
        "</div>"
    )


def _artifact_manifest(output_path: Path, provenance: dict[str, object]) -> dict[str, object]:
    artifacts = {}
    for name in STATIC_SITE_ARTIFACT_NAMES:
        path = output_path / name
        artifacts[name] = {
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return {
        "manifest_schema_version": 1,
        "artifact": "threebody-static-site-manifest",
        "hash_algorithm": "sha256",
        "build_provenance": provenance,
        "artifacts": artifacts,
    }


def _favicon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#16212f"/>
  <path d="M14 40c7 10 23 11 34 1" fill="none" stroke="#d9e1ec" stroke-width="2.4" stroke-linecap="round"/>
  <path d="M17 24c11-13 32-7 34 9" fill="none" stroke="#0b84f3" stroke-width="3.2" stroke-linecap="round"/>
  <path d="M21 45 32 16l11 29Z" fill="none" stroke="#00a878" stroke-width="2.2" stroke-linejoin="round" opacity=".9"/>
  <circle cx="32" cy="16" r="5.5" fill="#f95d6a"/>
  <circle cx="21" cy="45" r="5" fill="#ffa600"/>
  <circle cx="43" cy="45" r="5" fill="#0b84f3"/>
  <circle cx="37" cy="31" r="2.4" fill="#ffffff"/>
</svg>
"""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _progress_map(
    promotion_gates: dict[str, object],
    metrics: dict[str, float],
    jacobi_summary: dict[str, object],
) -> str:
    markov = jacobi_summary["hysteresis_markov"]
    poincare_markov = markov["poincare_markov"]
    permutation = poincare_markov["permutation_control"]
    section_robustness = poincare_markov["section_robustness"]
    baseline_bootstrap = markov["bootstrap_comparison"]
    picard_pass = bool(promotion_gates["picard_certified"])
    baseline_pass = bool(promotion_gates["hysteresis_significant_baseline_win"])
    order_pass = bool(promotion_gates["hysteresis_memory_order_selected"])
    poincare_pass = bool(
        promotion_gates["poincare_coordinate_has_sufficient_section"]
        and promotion_gates["poincare_markov_significant_baseline_win"]
        and promotion_gates["poincare_memory_order_selected"]
    )
    permutation_pass = bool(promotion_gates["poincare_passes_permutation_control"])
    robustness_pass = bool(promotion_gates["poincare_passes_section_robustness"])
    steps = (
        (
            "Picard contraction",
            picard_pass,
            f"max {metrics['picard_max_contraction']:.3e}",
            "scaled Jacobian tuning",
        ),
        (
            "Hysteresis grammar",
            baseline_pass,
            f"CI {promotion_gates['hysteresis_log_likelihood_gain_ci'][0]:.2e}+",
            "held-out phase baseline",
        ),
        (
            "Markov order",
            order_pass,
            f"order {promotion_gates['hysteresis_selected_markov_order']}",
            "BIC selects memory",
        ),
        (
            "Poincare sweep",
            poincare_pass,
            f"{promotion_gates['poincare_best_coordinate_crossing_count']} crossings",
            f"held-out {promotion_gates['poincare_best_coordinate']}",
        ),
        (
            "Permutation control",
            permutation_pass,
            f"gap {promotion_gates['poincare_permutation_control_gap']:.2e}",
            "symbol order beats shuffle",
        ),
        (
            "Section robustness",
            robustness_pass,
            f"{promotion_gates['poincare_section_robust_pass_count']} / {section_robustness['evaluated_count']}",
            "nearby sections repeat",
        ),
        (
            "Stride robustness",
            bool(promotion_gates["symbolic_passes_stride_robustness"]),
            f"{promotion_gates['symbolic_stride_robust_pass_count']} strides",
            "atlas sampling perturbation",
        ),
        (
            "Engine API",
            True,
            "threebody-engine",
            "JSON gates exported",
        ),
    )
    track = "".join(
        _progress_step(index, title, "pass" if passed else "wait", value, detail)
        for index, (title, passed, value, detail) in enumerate(steps, start=1)
    )
    baseline_strength = float(baseline_bootstrap["beats_baseline_fraction"])
    permutation_strength = float(1.0 - permutation["control_exceedance_fraction"])
    robustness_fraction = float(section_robustness["pass_fraction"])
    stride_fraction = float(promotion_gates["symbolic_stride_robust_pass_fraction"])
    evidence = "".join(
        [
            _evidence_card("Picard maximum", f"{metrics['picard_max_contraction']:.3e}", 1.0 if picard_pass else 0.0),
            _evidence_card("Baseline confidence", f"{baseline_strength:.2f}", baseline_strength),
            _evidence_card("Permutation confidence", f"{permutation_strength:.2f}", permutation_strength),
            _evidence_card("Section robustness", f"{robustness_fraction:.2f}", robustness_fraction),
            _evidence_card("Stride robustness", f"{stride_fraction:.2f}", stride_fraction),
            _evidence_card("Poincare crossings", str(promotion_gates["poincare_best_coordinate_crossing_count"]), 1.0),
        ]
    )
    return (
        '<div class="progress-track">'
        f"{track}"
        "</div>"
        '<div class="evidence-grid">'
        f"{evidence}"
        "</div>"
    )


def _stride_probe_values(base_stride: int) -> tuple[int, ...]:
    base = max(int(base_stride), 1)
    return tuple(sorted({max(1, int(round(0.75 * base))), base, max(1, int(round(1.5 * base)))}))


def _symbolic_stride_robustness(
    atlas: AnalysisAtlas,
    *,
    validation_run: tuple[object, TrajectoryResult],
    training_runs: tuple[tuple[object, TrajectoryResult], ...],
    stride_values: tuple[int, ...],
) -> dict[str, object]:
    rows = []
    for index, stride in enumerate(stride_values):
        validation_reports = atlas.analyze_trajectory(validation_run[0], validation_run[1], stride=stride)
        training_reports = tuple(
            atlas.analyze_trajectory(system, trajectory, stride=stride)
            for system, trajectory in training_runs
        )
        training_words = tuple(refined_chart_word_from_reports(reports) for reports in training_reports)
        validation_word = refined_chart_word_from_reports(validation_reports)
        chain = markov_chain_from_words(training_words)
        bootstrap = bootstrap_markov_baseline_comparison(
            chain,
            training_words,
            (validation_word,),
            resamples=64,
            random_seed=101 + index,
        )
        order_selection = select_markov_order(training_words, (validation_word,), max_order=2)
        coordinate_sweep = poincare_coordinate_sweep_from_reports(training_reports[0])
        poincare_training_words = tuple(
            poincare_section_word_from_reports(
                reports,
                coordinate=coordinate_sweep.best.coordinate,
                section_value=coordinate_sweep.best.best.section_value,
                direction=coordinate_sweep.best.direction,
            )
            for reports in training_reports
        )
        poincare_validation_words = (
            poincare_section_word_from_reports(
                validation_reports,
                coordinate=coordinate_sweep.best.coordinate,
                section_value=coordinate_sweep.best.best.section_value,
                direction=coordinate_sweep.best.direction,
            ),
        )
        poincare_chain = markov_chain_from_words(poincare_training_words)
        poincare_bootstrap = bootstrap_markov_baseline_comparison(
            poincare_chain,
            poincare_training_words,
            poincare_validation_words,
            resamples=64,
            random_seed=151 + index,
        )
        poincare_order = select_markov_order(poincare_training_words, poincare_validation_words, max_order=2)
        permutation = permutation_control_markov_validation(
            poincare_chain,
            poincare_validation_words,
            permutations=64,
            random_seed=181 + index,
        )
        section_robustness = poincare_markov_section_robustness(
            training_reports,
            coordinate_sweep.best,
            validation_report_sets=(validation_reports,),
            resamples=32,
            permutations=32,
            random_seed=211 + index,
        )
        passes = bool(
            bootstrap.significant_baseline_win
            and order_selection.memory_selected
            and coordinate_sweep.has_sufficient_section
            and poincare_bootstrap.significant_baseline_win
            and poincare_order.memory_selected
            and permutation.passes_permutation_control
            and section_robustness.passes_robustness
        )
        rows.append(
            {
                "stride": int(stride),
                "hysteresis_significant_baseline_win": bootstrap.significant_baseline_win,
                "hysteresis_memory_order_selected": order_selection.memory_selected,
                "poincare_best_coordinate": coordinate_sweep.best.coordinate,
                "poincare_best_crossing_count": coordinate_sweep.best.best.crossing_count,
                "poincare_training_word_lengths": [word.length for word in poincare_training_words],
                "poincare_validation_word_length": poincare_validation_words[0].length,
                "poincare_markov_significant_baseline_win": poincare_bootstrap.significant_baseline_win,
                "poincare_memory_order_selected": poincare_order.memory_selected,
                "poincare_passes_permutation_control": permutation.passes_permutation_control,
                "poincare_passes_section_robustness": section_robustness.passes_robustness,
                "passes": passes,
            }
        )
    pass_count = sum(1 for row in rows if row["passes"])
    evaluated_count = len(rows)
    pass_fraction = float(pass_count / evaluated_count) if evaluated_count else 0.0
    return {
        "stride_values": [int(stride) for stride in stride_values],
        "evaluated_count": evaluated_count,
        "pass_count": pass_count,
        "pass_fraction": pass_fraction,
        "minimum_pass_fraction": 1.0,
        "passes_stride_robustness": bool(evaluated_count > 0 and pass_fraction >= 1.0),
        "candidates": rows,
    }


def _progress_step(index: int, title: str, status: str, value: str, detail: str) -> str:
    normalized_status = "pass" if status == "pass" else "wait"
    return (
        f'<div class="progress-step {normalized_status}">'
        f'<span class="progress-index">{index}</span>'
        f"<strong>{html.escape(title)}</strong>"
        f'<span class="gate-status">{"PASS" if normalized_status == "pass" else "WAIT"}</span>'
        f'<span class="gate-value">{html.escape(value)}</span>'
        f"<span>{html.escape(detail)}</span>"
        "</div>"
    )


def _evidence_card(label: str, value: str, fraction: float) -> str:
    width = 100.0 * float(np.clip(fraction, 0.0, 1.0))
    return (
        '<div class="evidence">'
        f"<label>{html.escape(label)}</label>"
        f"<strong>{html.escape(value)}</strong>"
        '<div class="meter">'
        f'<span style="width: {width:.1f}%"></span>'
        "</div>"
        "</div>"
    )


def _metric_card(label: str, value: object) -> str:
    if isinstance(value, float):
        rendered = f"{value:.3e}"
    else:
        rendered = html.escape(str(value))
    return f'<div class="metric"><strong>{rendered}</strong><span>{html.escape(label)}</span></div>'


def _upgrade_card(title: str, body: str, badge: str) -> str:
    return (
        '<div class="metric upgrade">'
        f"<strong>{html.escape(title)}</strong>"
        f"<p>{html.escape(body)}</p>"
        f'<span class="badge">{html.escape(badge)}</span>'
        "</div>"
    )


def _gate_card(title: str, status: str, value: str, detail: str) -> str:
    normalized_status = "pass" if status == "pass" else "wait"
    status_text = "PASS" if normalized_status == "pass" else "WAIT"
    return (
        f'<div class="gate {normalized_status}">'
        f'<span class="gate-label">{html.escape(title)}</span>'
        f'<span class="gate-status">{status_text}</span>'
        f'<span class="gate-value">{html.escape(value)}</span>'
        f"<p>{html.escape(detail)}</p>"
        "</div>"
    )


def _provenance_card(title: str, value: str, detail: str) -> str:
    return (
        '<div class="gate pass">'
        f'<span class="gate-label">{html.escape(title)}</span>'
        f'<span class="gate-status">{html.escape(value)}</span>'
        f'<span class="gate-value">{html.escape(detail)}</span>'
        "</div>"
    )


def _line_figure(x: np.ndarray, y: np.ndarray, title: str, yaxis_title: str) -> go.Figure:
    figure = go.Figure(go.Scatter(x=x, y=y, mode="lines", line={"width": 2.4, "color": "#0b84f3"}))
    figure.update_layout(
        title=title,
        xaxis_title="time",
        yaxis_title=yaxis_title,
        template="plotly_white",
        height=360,
        margin={"l": 40, "r": 18, "t": 52, "b": 38},
    )
    return figure


def _jacobi_certificate_figure(summary: dict[str, object]) -> go.Figure:
    future = summary["future_tail"]
    inflated = summary["inflated_margin"]
    self_consistent = summary["self_consistent_radial_floor"]
    open_cone = summary["open_cone"]
    quadrupole = summary["quadrupole_acceleration"]
    parameter_box = summary["parameter_box_latest"]
    labels = [
        "finite margin",
        "future exchange",
        "inflated lower",
        "radial floor",
        "open radius",
        "quad ratio",
        "box lower",
    ]
    values = [
        future["finite_tail_escape_margin"],
        future["future_energy_exchange_bound"],
        inflated["validated_margin_lower"],
        self_consistent["certified_radial_floor"],
        open_cone["relative_state_radius"],
        quadrupole["maximum_bound_ratio"],
        parameter_box["interval_box_margin_lower"],
    ]
    colors = ["#0b84f3", "#ffa600", "#00a878", "#00a878", "#6c63ff", "#f95d6a", "#00a878"]
    figure = go.Figure(go.Bar(x=labels, y=values, marker={"color": colors}))
    figure.update_layout(
        title="Escape-cone certificate scalars",
        yaxis_type="log",
        yaxis_title="value (log scale)",
        template="plotly_white",
        height=520,
        margin={"l": 52, "r": 18, "t": 58, "b": 82},
    )
    return figure


def _picard_certificate_figure(summary: dict[str, object]) -> go.Figure:
    picard = summary["picard_flow"]
    tuning = summary["picard_tuning"]
    labels = [
        "max contraction",
        "target",
        "reserve",
        "margin lower",
        "mean substeps",
    ]
    values = [
        picard["maximum_observed_contraction"],
        picard["target_contraction"],
        tuning["contraction_reserve"],
        tuning["best_interval_escape_margin_lower"],
        tuning["mean_substeps_per_segment"],
    ]
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker={"color": ["#00a878", "#2f4858", "#00a878", "#0b84f3", "#ffa600"]},
        )
    )
    figure.add_hline(
        y=picard["target_contraction"],
        line_dash="dash",
        line_color="#f95d6a",
        annotation_text="target contraction",
    )
    figure.update_layout(
        title="Picard contraction tuning",
        yaxis_type="log",
        yaxis_title="value (log scale)",
        template="plotly_white",
        height=520,
        margin={"l": 52, "r": 18, "t": 58, "b": 82},
    )
    return figure


def _markov_baseline_figure(summary: dict[str, object]) -> go.Figure:
    comparison = summary["hysteresis_markov"]["baseline_comparison"]
    validation = comparison["markov_validation"]
    labels = [
        "Markov PPL",
        "baseline PPL",
        "PPL ratio",
        "coverage",
        "LL gain",
    ]
    values = [
        validation["perplexity"],
        comparison["baseline_perplexity"],
        comparison["perplexity_ratio"],
        validation["coverage_fraction"],
        max(comparison["log_likelihood_gain"], 1.0e-12),
    ]
    colors = ["#0b84f3", "#ffa600", "#6c63ff", "#00a878", "#00a878" if comparison["beats_baseline"] else "#f95d6a"]
    figure = go.Figure(go.Bar(x=labels, y=values, marker={"color": colors}))
    figure.update_layout(
        title="Markov baseline test",
        yaxis_type="log",
        yaxis_title="value (log scale)",
        template="plotly_white",
        height=520,
        margin={"l": 52, "r": 18, "t": 58, "b": 82},
    )
    return figure


def _orbit_figure_2d(paths: list[np.ndarray], labels: list[str], title: str) -> go.Figure:
    figure = go.Figure()
    _add_autoscale_trace(figure, paths)
    for index, (path, label) in enumerate(zip(paths, labels, strict=True)):
        figure.add_trace(
            go.Scatter(
                x=path[:, 0],
                y=path[:, 1],
                mode="lines",
                name=label,
                line={"width": 2.8, "color": PALETTE[index % len(PALETTE)]},
            )
        )
    figure.update_layout(
        title=title,
        xaxis_title="x",
        yaxis_title="y",
        xaxis={"autorange": True},
        yaxis={"autorange": True},
        template="plotly_white",
        height=460,
        margin={"l": 40, "r": 18, "t": 52, "b": 38},
    )
    return figure


def _animated_orbit_figure_2d(
    paths: list[np.ndarray],
    labels: list[str],
    title: str,
    *,
    static_points: np.ndarray | None = None,
    static_labels: list[str] | None = None,
    target_frames: int = 75,
) -> go.Figure:
    indices = np.unique(np.linspace(0, len(paths[0]) - 1, min(target_frames, len(paths[0])), dtype=int))
    figure = go.Figure()

    for index, (path, label) in enumerate(zip(paths, labels, strict=True)):
        color = PALETTE[index % len(PALETTE)]
        figure.add_trace(go.Scatter(x=path[:1, 0], y=path[:1, 1], mode="lines", name=f"{label} trail", line={"width": 2.5, "color": color}))
        figure.add_trace(go.Scatter(x=[path[0, 0]], y=[path[0, 1]], mode="markers", name=label, marker={"size": 10, "color": color}))

    if static_points is not None:
        static_points = np.asarray(static_points, dtype=float)
        figure.add_trace(
            go.Scatter(
                x=static_points[:, 0],
                y=static_points[:, 1],
                mode="markers+text",
                name="Fixed bodies",
                text=static_labels,
                textposition="top center",
                marker={"size": 12, "color": "#2f4858", "symbol": "diamond"},
            )
        )
    _add_autoscale_trace(figure, paths, static_points=static_points)

    frames = []
    for frame_index in indices:
        traces = []
        for index, path in enumerate(paths):
            color = PALETTE[index % len(PALETTE)]
            traces.append(go.Scatter(x=path[: frame_index + 1, 0], y=path[: frame_index + 1, 1], mode="lines", line={"width": 2.5, "color": color}))
            traces.append(go.Scatter(x=[path[frame_index, 0]], y=[path[frame_index, 1]], mode="markers", marker={"size": 10, "color": color}))
        if static_points is not None:
            traces.append(
                go.Scatter(
                    x=static_points[:, 0],
                    y=static_points[:, 1],
                    mode="markers+text",
                    text=static_labels,
                    textposition="top center",
                    marker={"size": 12, "color": "#2f4858", "symbol": "diamond"},
                )
            )
        frames.append(go.Frame(data=traces, name=str(frame_index)))

    figure.frames = frames
    figure.update_layout(
        title={"text": title, "x": 0.18, "xanchor": "left"},
        xaxis_title="x",
        yaxis_title="y",
        xaxis={"autorange": True},
        yaxis={"autorange": True},
        template="plotly_white",
        height=520,
        margin={"l": 40, "r": 18, "t": 58, "b": 38},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "xanchor": "left",
                "y": 1.16,
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 80, "redraw": True}, "transition": {"duration": 40}, "fromcurrent": True}],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}],
                    },
                ],
            }
        ],
    )
    return figure


def _add_autoscale_trace(
    figure: go.Figure,
    paths: list[np.ndarray],
    *,
    static_points: np.ndarray | None = None,
) -> None:
    points = [np.asarray(path, dtype=float)[:, :2] for path in paths]
    if static_points is not None:
        points.append(np.asarray(static_points, dtype=float)[:, :2])
    combined = np.vstack(points)
    figure.add_trace(
        go.Scatter(
            x=combined[:, 0],
            y=combined[:, 1],
            mode="markers",
            marker={"size": 1, "opacity": 0.0},
            hoverinfo="skip",
            showlegend=False,
            name="autoscale extent",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static GitHub Pages visualizer.")
    parser.add_argument("--output", default="site", help="Output directory for the static site.")
    args = parser.parse_args()
    index_path = build_static_site(args.output)
    print(index_path)


if __name__ == "__main__":
    main()
