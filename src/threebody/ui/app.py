from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from threebody.analysis import (
    AnalysisAtlas,
    ChartType,
    FeatureConditionedTransitionModel,
    feature_vector_for_report,
    hierarchical_elements,
)
from threebody.diagnostics import InvariantMonitor, PhaseSpaceTools, StabilityAnalyzer
from threebody.experiments import CompactModelFitter, InitialConditionScanner, OrbitLibrary
from threebody.solvers import AdaptiveIntegrator, AnalyticTwoBodySolver, StructureAwareIntegrator


st.set_page_config(page_title="ThreeBody", layout="wide")

PALETTE = ["#0b84f3", "#f95d6a", "#00a878", "#ffa600", "#6c63ff"]


def line_figure(x: np.ndarray, y: np.ndarray, title: str, yaxis_title: str) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=x, y=y, mode="lines", line={"width": 2}))
    figure.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title=yaxis_title,
        template="plotly_white",
        margin={"l": 30, "r": 20, "t": 50, "b": 30},
        height=280,
    )
    return figure


def orbit_figure_2d(paths: list[np.ndarray], labels: list[str], title: str) -> go.Figure:
    figure = go.Figure()
    for index, (path, label) in enumerate(zip(paths, labels, strict=True)):
        color = PALETTE[index % len(PALETTE)]
        figure.add_trace(
            go.Scatter(
                x=path[:, 0],
                y=path[:, 1],
                mode="lines",
                name=label,
                line={"width": 2.5, "color": color},
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[path[0, 0]],
                y=[path[0, 1]],
                mode="markers",
                marker={"size": 7, "symbol": "circle-open", "color": color},
                showlegend=False,
            )
        )
    figure.update_layout(
        title=title,
        xaxis_title="x",
        yaxis_title="y",
        yaxis={"scaleanchor": "x", "scaleratio": 1.0},
        template="plotly_white",
        margin={"l": 30, "r": 20, "t": 50, "b": 30},
        height=600,
    )
    return figure


def orbit_figure_3d(paths: list[np.ndarray], labels: list[str], title: str) -> go.Figure:
    figure = go.Figure()
    for index, (path, label) in enumerate(zip(paths, labels, strict=True)):
        figure.add_trace(
            go.Scatter3d(
                x=path[:, 0],
                y=path[:, 1],
                z=path[:, 2],
                mode="lines",
                name=label,
                line={"width": 6, "color": PALETTE[index % len(PALETTE)]},
            )
        )
    figure.update_layout(
        title=title,
        scene={"aspectmode": "data", "xaxis_title": "x", "yaxis_title": "y", "zaxis_title": "z"},
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        height=600,
    )
    return figure


def animation_indices(sample_count: int, target_frames: int = 180) -> np.ndarray:
    frame_count = min(sample_count, max(30, target_frames))
    return np.unique(np.linspace(0, sample_count - 1, frame_count, dtype=int))


def padded_axis_ranges(
    paths: list[np.ndarray],
    frame_index: int,
    static_points: np.ndarray | None = None,
    padding_ratio: float = 0.12,
    min_span: float = 0.5,
) -> tuple[list[float], list[float]]:
    visible_points = [path[: frame_index + 1] for path in paths]
    if static_points is not None:
        visible_points.append(np.asarray(static_points, dtype=float))
    points = np.vstack(visible_points)

    x_min = float(np.min(points[:, 0]))
    x_max = float(np.max(points[:, 0]))
    y_min = float(np.min(points[:, 1]))
    y_max = float(np.max(points[:, 1]))

    x_span = max(x_max - x_min, min_span)
    y_span = max(y_max - y_min, min_span)
    span = max(x_span, y_span)
    padding = span * padding_ratio

    x_center = 0.5 * (x_min + x_max)
    y_center = 0.5 * (y_min + y_max)
    half_span = 0.5 * span + padding

    return [x_center - half_span, x_center + half_span], [y_center - half_span, y_center + half_span]


def smooth_axis_ranges(
    raw_ranges: list[tuple[list[float], list[float]]],
    easing: float = 0.18,
) -> list[tuple[list[float], list[float]]]:
    if not raw_ranges:
        return []

    smoothed: list[tuple[list[float], list[float]]] = []
    current_x = np.asarray(raw_ranges[0][0], dtype=float)
    current_y = np.asarray(raw_ranges[0][1], dtype=float)
    smoothed.append((current_x.tolist(), current_y.tolist()))

    for x_range, y_range in raw_ranges[1:]:
        target_x = np.asarray(x_range, dtype=float)
        target_y = np.asarray(y_range, dtype=float)
        current_x = current_x + easing * (target_x - current_x)
        current_y = current_y + easing * (target_y - current_y)
        smoothed.append((current_x.tolist(), current_y.tolist()))

    return smoothed


def animated_orbit_figure_2d(
    paths: list[np.ndarray],
    labels: list[str],
    times: np.ndarray,
    title: str,
    static_points: np.ndarray | None = None,
    static_labels: list[str] | None = None,
    frame_count: int = 180,
) -> go.Figure:
    indices = animation_indices(len(times), target_frames=frame_count)
    figure = go.Figure()
    raw_ranges = [padded_axis_ranges(paths, int(frame_index), static_points=static_points) for frame_index in indices]
    smoothed_ranges = smooth_axis_ranges(raw_ranges)
    initial_x_range, initial_y_range = smoothed_ranges[0]

    for index, (path, label) in enumerate(zip(paths, labels, strict=True)):
        color = PALETTE[index % len(PALETTE)]
        figure.add_trace(
            go.Scatter(
                x=path[:1, 0],
                y=path[:1, 1],
                mode="lines",
                name=f"{label} trail",
                line={"width": 2.5, "color": color},
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[path[0, 0]],
                y=[path[0, 1]],
                mode="markers",
                name=label,
                marker={"size": 10, "color": color},
            )
        )

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

    frames: list[go.Frame] = []
    for range_index, frame_index in enumerate(indices):
        traces: list[go.Scatter] = []
        for index, path in enumerate(paths):
            color = PALETTE[index % len(PALETTE)]
            traces.append(
                go.Scatter(
                    x=path[: frame_index + 1, 0],
                    y=path[: frame_index + 1, 1],
                    mode="lines",
                    line={"width": 2.5, "color": color},
                )
            )
            traces.append(
                go.Scatter(
                    x=[path[frame_index, 0]],
                    y=[path[frame_index, 1]],
                    mode="markers",
                    marker={"size": 10, "color": color},
                )
            )
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
        x_range, y_range = smoothed_ranges[range_index]
        frames.append(
            go.Frame(
                data=traces,
                name=str(frame_index),
                layout=go.Layout(xaxis={"range": x_range}, yaxis={"range": y_range}),
            )
        )

    figure.frames = frames
    figure.update_layout(
        title={"text": title, "x": 0.18, "xanchor": "left"},
        xaxis_title="x",
        yaxis_title="y",
        xaxis={"range": initial_x_range},
        yaxis={"scaleanchor": "x", "scaleratio": 1.0, "range": initial_y_range},
        template="plotly_white",
        height=620,
        margin={"l": 30, "r": 20, "t": 60, "b": 30},
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
                        "args": [
                            None,
                            {
                                "frame": {"duration": 65, "redraw": True},
                                "transition": {"duration": 45, "easing": "cubic-in-out"},
                                "fromcurrent": True,
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}},
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "Sample index: "},
                "pad": {"t": 45},
                "steps": [
                    {
                        "label": str(frame_index),
                        "method": "animate",
                        "args": [
                            [str(frame_index)],
                            {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}},
                        ],
                    }
                    for frame_index in indices
                ],
            }
        ],
    )
    return figure


def restricted_zero_velocity_figure(system: object, jacobi_constant: float) -> go.Figure:
    x_values = np.linspace(-1.6, 1.6, 220)
    y_values = np.linspace(-1.4, 1.4, 200)
    x_grid, y_grid = np.meshgrid(x_values, y_values)
    zvc = system.zero_velocity_curve(x_grid, y_grid, jacobi_constant)
    figure = go.Figure()
    figure.add_trace(
        go.Contour(
            x=x_values,
            y=y_values,
            z=zvc,
            contours={"start": 0.0, "end": 0.0, "size": 1.0, "coloring": "lines"},
            line={"color": "#2f4858", "width": 2},
            showscale=False,
            name="Zero Velocity Curve",
        )
    )
    lagrange = system.lagrange_points()
    for label, point in lagrange.items():
        figure.add_trace(
            go.Scatter(
                x=[point[0]],
                y=[point[1]],
                mode="markers+text",
                text=[label],
                textposition="top center",
                marker={"size": 8, "color": "#bc5090"},
                showlegend=False,
            )
        )
    primaries = system.primary_positions
    figure.add_trace(
        go.Scatter(
            x=primaries[:, 0],
            y=primaries[:, 1],
            mode="markers",
            marker={"size": 12, "color": "#003f5c"},
            name="Primaries",
        )
    )
    figure.update_layout(
        title="Restricted Three-Body Zero-Velocity Geometry",
        xaxis_title="x",
        yaxis_title="y",
        yaxis={"scaleanchor": "x", "scaleratio": 1.0},
        template="plotly_white",
        height=600,
        margin={"l": 30, "r": 20, "t": 50, "b": 30},
    )
    return figure


def render_analysis_atlas(system: object, trajectory: object, stride: int | None = None) -> None:
    atlas = AnalysisAtlas()
    if stride is None:
        stride = max(1, len(trajectory.t) // 120)
    reports = atlas.analyze_trajectory(system, trajectory, stride=stride)
    distribution = atlas.chart_distribution(reports)
    transitions = atlas.transitions(system, trajectory, stride=stride)

    distribution_rows = [
        {"chart": str(chart), "share": round(share, 3)}
        for chart, share in sorted(distribution.items(), key=lambda item: item[1], reverse=True)
    ]
    transition_rows = [
        {
            "time": round(transition.time, 4),
            "from": str(transition.previous),
            "to": str(transition.current),
            "reason": transition.reason,
        }
        for transition in transitions[:20]
    ]

    st.subheader("Analysis Atlas")
    left, right = st.columns(2)
    left.dataframe(distribution_rows, use_container_width=True, hide_index=True)
    if transition_rows:
        right.dataframe(transition_rows, use_container_width=True, hide_index=True)
    else:
        right.info("No chart transitions detected at the current sampling stride.")

    model = FeatureConditionedTransitionModel.from_reports(reports)
    if reports and model.centroids:
        current_report = reports[-1]
        predictions = model.predict(current_report.primary_chart, feature_vector_for_report(current_report))
        prediction_rows = [
            {
                "from": str(prediction.previous),
                "to": str(prediction.current),
                "score": round(prediction.score, 4),
                "prior": round(prediction.prior, 4),
                "distance": round(prediction.feature_distance, 4),
                "samples": prediction.samples,
            }
            for prediction in predictions
        ]
        if prediction_rows:
            st.dataframe(prediction_rows, use_container_width=True, hide_index=True)

    if getattr(system, "body_count", None) == 3 and reports:
        latest = reports[-1]
        hierarchy_score = next((score.score for score in latest.scores if score.chart == ChartType.TWO_BODY_HIERARCHY), 0.0)
        if hierarchy_score > 0.2:
            elements = hierarchical_elements(system, trajectory.y[-1])
            st.dataframe(
                [
                    {
                        "inner_pair": str(elements.inner_pair),
                        "outer_body": elements.outer_body,
                        "a_inner": elements.inner_semimajor_axis,
                        "e_inner": elements.inner_eccentricity,
                        "perturbation": elements.perturbation_strength,
                        "hierarchy_ratio": elements.hierarchy_ratio,
                        "inner_bound": elements.is_inner_bound,
                    }
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_two_body() -> None:
    st.subheader("Two-Body Baseline")
    library = OrbitLibrary()
    analytic = AnalyticTwoBodySolver()
    adaptive = AdaptiveIntegrator()
    structure_aware = StructureAwareIntegrator()

    col1, col2, col3 = st.columns(3)
    semimajor_axis = col1.slider("Semimajor axis", 0.5, 3.0, 1.0, 0.1)
    eccentricity = col2.slider("Eccentricity", 0.0, 0.9, 0.2, 0.01)
    periods = col3.slider("Periods", 1.0, 5.0, 1.0, 0.5)

    scenario = library.two_body_elliptic(semimajor_axis=semimajor_axis, eccentricity=eccentricity, periods=periods)
    integrator_name = st.radio("Integrator", ["Adaptive", "Structure-Aware"], horizontal=True)
    if integrator_name == "Adaptive":
        trajectory = adaptive.integrate(scenario.system, scenario.t_span, scenario.initial_state, t_eval=scenario.t_eval)
    else:
        trajectory = structure_aware.integrate(scenario.system, scenario.t_span, scenario.initial_state)
    analytic_solution = analytic.propagate(scenario.system, scenario.initial_state, trajectory.t)
    monitor = InvariantMonitor(scenario.system)
    invariants = monitor.evaluate(trajectory)

    numerical_positions = trajectory.y[:, :2]
    analytic_positions = analytic_solution.y[:, :2]
    error = np.linalg.norm(numerical_positions - analytic_positions, axis=1)

    left, right = st.columns([2, 1])
    left.plotly_chart(
        orbit_figure_2d([analytic_positions, numerical_positions], ["Analytic", "Numerical"], "Two-Body Orbit"),
        use_container_width=True,
    )
    right.metric("Max position error", f"{np.max(error):.2e}")
    right.metric("Max energy drift", f"{np.max(np.abs(invariants['energy_drift'])):.2e}")
    right.metric("Max angular drift", f"{np.max(np.abs(invariants['angular_momentum_drift'])):.2e}")

    lower_left, lower_right = st.columns(2)
    lower_left.plotly_chart(line_figure(trajectory.t, error, "Analytic vs Numerical Error", "Position error"), use_container_width=True)
    lower_right.plotly_chart(line_figure(trajectory.t, invariants["energy_drift"], "Energy Drift", "ΔE"), use_container_width=True)


def render_restricted_three_body() -> None:
    st.subheader("Restricted Three-Body")
    library = OrbitLibrary()
    adaptive = AdaptiveIntegrator()
    phase_tools = PhaseSpaceTools()
    scanner = InitialConditionScanner(adaptive)
    fitter = CompactModelFitter()

    col1, col2, col3 = st.columns(3)
    mass_ratio = col1.slider("Mass ratio μ", 0.001, 0.2, 0.0121505856, 0.001)
    perturb_x = col2.slider("L4 x perturbation", -0.08, 0.08, 0.01, 0.005)
    periods = col3.slider("Periods", 5.0, 30.0, 15.0, 1.0)

    st.caption("Restricted problem uses the adaptive solver because the rotating-frame equations include velocity coupling.")
    scenario = library.restricted_l4(mass_ratio=mass_ratio, perturbation=(perturb_x, 0.0, 0.0, 0.0), periods=periods)
    trajectory = adaptive.integrate(scenario.system, scenario.t_span, scenario.initial_state, t_eval=scenario.t_eval)
    monitor = InvariantMonitor(scenario.system)
    invariants = monitor.evaluate(trajectory)
    section = phase_tools.planar_poincare_section(trajectory, x_index=0, y_index=1, vx_index=2, vy_index=3)

    left, right = st.columns([2, 1])
    left.plotly_chart(restricted_zero_velocity_figure(scenario.system, invariants["jacobi_constant"][0]), use_container_width=True)
    right.metric("Jacobi drift max", f"{np.max(np.abs(invariants['jacobi_drift'])):.2e}")
    right.metric("Section points", f"{len(section)}")
    right.metric("Primary minimum approach", f"{np.min(scenario.system.distances(trajectory.y[:, :2])[0]):.3f}")

    orbit_panel, drift_panel = st.columns(2)
    orbit_panel.plotly_chart(
        orbit_figure_2d([trajectory.y[:, :2]], ["Test particle"], "Rotating-Frame Trajectory"),
        use_container_width=True,
    )
    drift_panel.plotly_chart(line_figure(trajectory.t, invariants["jacobi_drift"], "Jacobi Constant Drift", "ΔC"), use_container_width=True)

    st.plotly_chart(
        animated_orbit_figure_2d(
            [trajectory.y[:, :2]],
            ["Test particle"],
            trajectory.t,
            "Restricted Three-Body Animation",
            static_points=scenario.system.primary_positions,
            static_labels=["Primary 1", "Primary 2"],
        ),
        use_container_width=True,
    )
    render_analysis_atlas(scenario.system, trajectory)

    section_left, section_right = st.columns(2)
    if len(section) >= 2:
        x_n, x_next = phase_tools.return_map(section)
        map_figure = go.Figure(go.Scatter(x=x_n, y=x_next, mode="markers", marker={"size": 6, "color": "#ef5675"}))
        map_figure.update_layout(
            title="Poincare Return Map",
            xaxis_title="x_n",
            yaxis_title="x_(n+1)",
            template="plotly_white",
            height=320,
            margin={"l": 30, "r": 20, "t": 50, "b": 30},
        )
        section_left.plotly_chart(map_figure, use_container_width=True)
    else:
        section_left.info("No Poincare crossings detected for the current trajectory.")

    if st.checkbox("Run a small basin scan", value=False):
        x_values = np.linspace(0.6, 1.2, 16)
        y_values = np.linspace(0.2, 1.0, 16)
        classes = scanner.scan_restricted_grid(scenario.system, invariants["jacobi_constant"][0], x_values, y_values)
        mapping = {"bounded": 0, "escape": 1, "collision": 2, "forbidden": 3}
        numeric = np.vectorize(mapping.get)(classes)
        heatmap = go.Figure(
            go.Heatmap(
                x=x_values,
                y=y_values,
                z=numeric,
                colorscale=[
                    [0.0, "#00a878"],
                    [0.33, "#00a878"],
                    [0.34, "#ffa600"],
                    [0.66, "#ffa600"],
                    [0.67, "#ef5675"],
                    [0.9, "#ef5675"],
                    [0.91, "#58508d"],
                    [1.0, "#58508d"],
                ],
                showscale=False,
            )
        )
        heatmap.update_layout(
            title="Restricted Basin Scan",
            xaxis_title="x",
            yaxis_title="y",
            template="plotly_white",
            height=320,
            margin={"l": 30, "r": 20, "t": 50, "b": 30},
        )
        section_right.plotly_chart(heatmap, use_container_width=True)
    else:
        compact_inputs = section[:, :2] if len(section) else np.array([[perturb_x, 0.0], [perturb_x * 1.1, 0.02], [perturb_x * 0.9, -0.02]])
        compact_outputs = np.sum(compact_inputs**2, axis=1)
        fit = fitter.fit(compact_inputs, compact_outputs, ("x", "vx"), "local_action_proxy")
        section_right.write(
            {
                "compact_model": fit.target_name,
                "rmse": fit.rmse,
                "valid_radius": fit.valid_radius,
                "center": fit.center.tolist(),
            }
        )


def render_general_three_body() -> None:
    st.subheader("General Newtonian Three-Body")
    library = OrbitLibrary()
    adaptive = AdaptiveIntegrator()
    structure_aware = StructureAwareIntegrator()
    stability = StabilityAnalyzer()

    col1, col2, col3 = st.columns(3)
    periods = col1.slider("Figure-eight periods", 0.5, 2.0, 1.0, 0.25)
    perturbation = col2.slider("Initial perturbation", 0.0, 0.05, 0.001, 0.001)
    integrator_name = col3.radio("Integrator", ["Adaptive", "Structure-Aware"], horizontal=False)

    reference = library.general_figure_eight(periods=periods, perturbation_scale=0.0)
    perturbed = library.general_figure_eight(periods=periods, perturbation_scale=perturbation)

    if integrator_name == "Adaptive":
        reference_traj = adaptive.integrate(reference.system, reference.t_span, reference.initial_state, t_eval=reference.t_eval)
        perturbed_traj = adaptive.integrate(perturbed.system, perturbed.t_span, perturbed.initial_state, t_eval=perturbed.t_eval)
    else:
        reference_traj = structure_aware.integrate(reference.system, reference.t_span, reference.initial_state)
        perturbed_traj = structure_aware.integrate(perturbed.system, perturbed.t_span, perturbed.initial_state)

    monitor = InvariantMonitor(reference.system)
    invariants = monitor.evaluate(reference_traj)
    stability_report = stability.finite_time_lyapunov(reference_traj, perturbed_traj)
    positions_final, _ = reference.system.split_state(reference_traj.y[-1])
    positions_initial, _ = reference.system.split_state(reference_traj.y[0])
    return_error = np.linalg.norm(positions_final - positions_initial)

    body_paths = reference_traj.y[:, : reference.system.body_count * reference.system.dimension].reshape(
        reference_traj.y.shape[0],
        reference.system.body_count,
        reference.system.dimension,
    )

    left, right = st.columns([2, 1])
    if reference.system.dimension == 3:
        left.plotly_chart(
            orbit_figure_3d([body_paths[:, i, :] for i in range(reference.system.body_count)], ["Body 1", "Body 2", "Body 3"], "Three-Body Trajectories"),
            use_container_width=True,
        )
    else:
        left.plotly_chart(
            orbit_figure_2d([body_paths[:, i, :] for i in range(reference.system.body_count)], ["Body 1", "Body 2", "Body 3"], "Three-Body Trajectories"),
            use_container_width=True,
        )
    right.metric("Return error", f"{return_error:.2e}")
    right.metric("Energy drift max", f"{np.max(np.abs(invariants['energy_drift'])):.2e}")
    right.metric("Finite-time Lyapunov", f"{stability_report['finite_time_lyapunov']:.3e}")
    right.write({"classification": stability_report["classification"]})

    lower_left, lower_right = st.columns(2)
    lower_left.plotly_chart(line_figure(reference_traj.t, invariants["energy_drift"], "Three-Body Energy Drift", "ΔE"), use_container_width=True)
    lower_right.plotly_chart(
        line_figure(reference_traj.t, stability_report["lyapunov_series"], "Finite-Time Lyapunov Series", "λ(t)"),
        use_container_width=True,
    )

    st.plotly_chart(
        animated_orbit_figure_2d(
            [body_paths[:, i, :] for i in range(reference.system.body_count)],
            ["Body 1", "Body 2", "Body 3"],
            reference_traj.t,
            "General Three-Body Animation",
        ),
        use_container_width=True,
    )
    render_analysis_atlas(reference.system, reference_traj)


def main() -> None:
    st.title("ThreeBody Dynamics Lab")
    st.caption("Analytic two-body baseline, structured restricted three-body analysis, and precision-focused general three-body experiments.")
    st.markdown(
        """
        This application is intentionally solver-first.
        It exposes invariants, return maps, and sensitivity metrics instead of treating visualization as a standalone demo.
        """
    )

    mode = st.sidebar.selectbox("Mode", ["Two-Body", "Restricted Three-Body", "General Three-Body"])
    st.sidebar.markdown(
        """
        **Scientific framing**

        - Two-body is the analytic reference.
        - Restricted three-body is the first nonlinear structured target.
        - General three-body is handled numerically with invariant monitoring.
        """
    )

    if mode == "Two-Body":
        render_two_body()
    elif mode == "Restricted Three-Body":
        render_restricted_three_body()
    else:
        render_general_three_body()


if __name__ == "__main__":
    main()


