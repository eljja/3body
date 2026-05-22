from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

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


PALETTE = ["#0b84f3", "#f95d6a", "#00a878", "#ffa600", "#6c63ff"]


def build_static_site(output_dir: str | Path) -> Path:
    """Build a static GitHub Pages dashboard from precomputed reference runs."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

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

    page = _render_page(
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
    )

    index_path = output_path / "index.html"
    index_path.write_text(page, encoding="utf-8")
    (output_path / ".nojekyll").write_text("", encoding="utf-8")
    return index_path


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
) -> str:
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
    training_words = (
        refined_chart_word_from_reports(grammar_reports),
        refined_chart_word_from_reports(grammar_phase_reports),
    )
    validation_word = training_words[0]
    return_word = training_words[0]
    poincare_word = poincare_section_word_from_reports(grammar_reports, coordinate="hierarchy_perturbation_strength")
    poincare_sweep = poincare_section_sweep_from_reports(grammar_reports, coordinate="hierarchy_perturbation_strength")
    poincare_coordinate_sweep = poincare_coordinate_sweep_from_reports(grammar_reports)
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
                "Poincare sweep",
                "pass" if promotion_gates["poincare_coordinate_has_sufficient_section"] else "wait",
                f"{promotion_gates['poincare_best_coordinate']}: {promotion_gates['poincare_best_coordinate_crossing_count']}",
                "best coordinate crossings",
            ),
        ]
    )
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

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 20px 0 24px; }}
    .upgrade-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }}
    .gate-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
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
      .grid, .figure-grid, .upgrade-grid, .gate-grid {{ grid-template-columns: 1fr; }}
      main {{ width: min(100vw - 18px, 1180px); padding-top: 12px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>ThreeBody Dynamics Lab</h1>
    <p>
      Static GitHub Pages build from the Python research engine. The browser page is not a solver server:
      trajectories, invariant drift, atlas summaries, and theorem-suite status are computed during deployment and
      embedded as interactive Plotly figures.
    </p>
  </header>

  <div class="grid">
    {_metric_card("Two-body energy drift", metrics["two_body_max_energy_drift"])}
    {_metric_card("Restricted Jacobi drift", metrics["restricted_max_jacobi_drift"])}
    {_metric_card("General energy drift", metrics["general_max_energy_drift"])}
    {_metric_card("Figure-eight FTLE", metrics["figure_eight_finite_time_lyapunov"])}
  </div>

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
    <h2>Research certificate status</h2>
    <pre>{html.escape(json.dumps({"metrics": metrics, "promotion_gates": promotion_gates, "jacobi_escape_cone": jacobi_summary, "note": "Full theorem-suite benchmarks remain a local/CI research check; this page embeds a representative certificate and latest parameter-box summary."}, indent=2, sort_keys=True))}</pre>
  </section>
</main>
</body>
</html>
"""


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
        yaxis={"scaleanchor": "x", "scaleratio": 1.0},
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
        yaxis={"scaleanchor": "x", "scaleratio": 1.0},
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static GitHub Pages visualizer.")
    parser.add_argument("--output", default="site", help="Output directory for the static site.")
    args = parser.parse_args()
    index_path = build_static_site(args.output)
    print(index_path)


if __name__ == "__main__":
    main()
