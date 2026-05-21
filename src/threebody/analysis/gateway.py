from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from .variational import finite_difference_jacobian


@dataclass(frozen=True, slots=True)
class GatewayTransitEstimate:
    """Linearized L1/L2/L3 gateway transport estimate in the rotating CR3BP frame."""

    lagrange_point: str
    jacobi_constant: float
    critical_jacobi_constant: float
    jacobi_margin: float
    neck_open: bool
    unstable_projection: float
    stable_projection: float
    transit_likelihood: float

    def as_dict(self) -> dict[str, float | str | bool]:
        return {
            "lagrange_point": self.lagrange_point,
            "jacobi_constant": self.jacobi_constant,
            "critical_jacobi_constant": self.critical_jacobi_constant,
            "jacobi_margin": self.jacobi_margin,
            "neck_open": self.neck_open,
            "unstable_projection": self.unstable_projection,
            "stable_projection": self.stable_projection,
            "transit_likelihood": self.transit_likelihood,
        }


@dataclass(frozen=True, slots=True)
class RestrictedChartCertificate:
    """Interval-level certificate for CR3BP Lagrange/gateway interpretation."""

    nearest_lagrange: str
    certificate_kind: str
    sample_count: int
    min_lagrange_distance: float
    max_lagrange_distance: float
    max_abs_jacobi_drift: float
    min_gateway_margin: float | None
    neck_open_fraction: float
    max_transit_likelihood: float
    routh_stable_triangular: bool
    numerically_resolved: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | None]:
        return {
            "nearest_lagrange": self.nearest_lagrange,
            "certificate_kind": self.certificate_kind,
            "sample_count": self.sample_count,
            "min_lagrange_distance": self.min_lagrange_distance,
            "max_lagrange_distance": self.max_lagrange_distance,
            "max_abs_jacobi_drift": self.max_abs_jacobi_drift,
            "min_gateway_margin": self.min_gateway_margin,
            "neck_open_fraction": self.neck_open_fraction,
            "max_transit_likelihood": self.max_transit_likelihood,
            "routh_stable_triangular": self.routh_stable_triangular,
            "numerically_resolved": self.numerically_resolved,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class GatewayManifoldTubeCertificate:
    """Interval certificate for a linearized collinear-gateway manifold tube."""

    lagrange_point: str
    sample_count: int
    neck_open_fraction: float
    initial_unstable_projection: float
    terminal_unstable_projection: float
    initial_stable_projection: float
    terminal_stable_projection: float
    unstable_growth_ratio: float
    stable_decay_ratio: float
    minimum_projection_margin: float
    tube_resolved: bool
    classification: str
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str]:
        return {
            "lagrange_point": self.lagrange_point,
            "sample_count": self.sample_count,
            "neck_open_fraction": self.neck_open_fraction,
            "initial_unstable_projection": self.initial_unstable_projection,
            "terminal_unstable_projection": self.terminal_unstable_projection,
            "initial_stable_projection": self.initial_stable_projection,
            "terminal_stable_projection": self.terminal_stable_projection,
            "unstable_growth_ratio": self.unstable_growth_ratio,
            "stable_decay_ratio": self.stable_decay_ratio,
            "minimum_projection_margin": self.minimum_projection_margin,
            "tube_resolved": self.tube_resolved,
            "classification": self.classification,
            "warning": self.warning,
        }


def gateway_transit_estimate(system: object, state: np.ndarray) -> GatewayTransitEstimate:
    """Estimate transit tendency near the nearest collinear Lagrange gateway."""

    state = np.asarray(state, dtype=float)
    lagrange_points = system.lagrange_points()
    collinear = {name: point for name, point in lagrange_points.items() if name in {"L1", "L2", "L3"}}
    position = state[:2]
    nearest = min(collinear, key=lambda name: float(np.linalg.norm(position - collinear[name])))
    point = collinear[nearest]
    equilibrium = np.array([point[0], point[1], 0.0, 0.0], dtype=float)
    jacobi = float(system.jacobi_constant(state))
    critical = float(system.jacobi_constant(equilibrium))
    jacobi_margin = float(critical - jacobi)
    jacobian = finite_difference_jacobian(system, equilibrium)
    eigenvalues, eigenvectors = np.linalg.eig(jacobian)
    real_parts = np.real(eigenvalues)
    unstable_index = int(np.argmax(real_parts))
    stable_index = int(np.argmin(real_parts))
    displacement = state - equilibrium
    unstable_projection = _normalized_projection(displacement, np.real(eigenvectors[:, unstable_index]))
    stable_projection = _normalized_projection(displacement, np.real(eigenvectors[:, stable_index]))
    projection_score = abs(unstable_projection) / (abs(unstable_projection) + abs(stable_projection) + 1.0e-12)
    openness = 1.0 if jacobi_margin > 0.0 else 0.0
    transit_likelihood = float(openness * projection_score)
    return GatewayTransitEstimate(
        lagrange_point=nearest,
        jacobi_constant=jacobi,
        critical_jacobi_constant=critical,
        jacobi_margin=jacobi_margin,
        neck_open=jacobi_margin > 0.0,
        unstable_projection=float(unstable_projection),
        stable_projection=float(stable_projection),
        transit_likelihood=transit_likelihood,
    )


def gateway_manifold_tube_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    minimum_neck_open_fraction: float = 1.0,
    minimum_projection_margin: float = 0.0,
) -> GatewayManifoldTubeCertificate:
    """Track stable/unstable projections over a sampled gateway interval.

    This is a local linear tube proxy. It does not replace invariant-manifold
    continuation, but it promotes the gateway check from a single-state score to
    an interval-level transit/non-transit target.
    """

    if not hasattr(system, "jacobi_constant") or not hasattr(system, "lagrange_points"):
        raise TypeError("gateway_manifold_tube_certificate requires a restricted three-body system.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    states = np.asarray(trajectory.y[start : end + 1], dtype=float)
    midpoint = states[len(states) // 2]
    lagrange_points = system.lagrange_points()
    collinear = {name: point for name, point in lagrange_points.items() if name in {"L1", "L2", "L3"}}
    nearest = min(collinear, key=lambda name: float(np.linalg.norm(midpoint[:2] - collinear[name])))
    point = collinear[nearest]
    equilibrium = np.array([point[0], point[1], 0.0, 0.0], dtype=float)
    jacobian = finite_difference_jacobian(system, equilibrium)
    eigenvalues, eigenvectors = np.linalg.eig(jacobian)
    real_parts = np.real(eigenvalues)
    unstable_direction = np.real(eigenvectors[:, int(np.argmax(real_parts))])
    stable_direction = np.real(eigenvectors[:, int(np.argmin(real_parts))])
    critical = float(system.jacobi_constant(equilibrium))
    neck_open = []
    unstable = []
    stable = []
    margins = []
    for state in states:
        displacement = state - equilibrium
        unstable_projection = _normalized_projection(displacement, unstable_direction)
        stable_projection = _normalized_projection(displacement, stable_direction)
        unstable.append(abs(unstable_projection))
        stable.append(abs(stable_projection))
        margins.append(abs(unstable_projection) - abs(stable_projection))
        neck_open.append(float(critical - float(system.jacobi_constant(state)) > 0.0))
    unstable_array = np.asarray(unstable, dtype=float)
    stable_array = np.asarray(stable, dtype=float)
    neck_open_fraction = float(np.mean(neck_open)) if neck_open else 0.0
    unstable_growth = float(unstable_array[-1] / max(unstable_array[0], 1.0e-12))
    stable_decay = float(stable_array[0] / max(stable_array[-1], 1.0e-12))
    projection_margin = float(np.min(margins))
    tube_resolved = bool(
        neck_open_fraction >= minimum_neck_open_fraction
        and projection_margin > minimum_projection_margin
        and np.all(np.isfinite(unstable_array))
        and np.all(np.isfinite(stable_array))
    )
    if tube_resolved and unstable_growth >= 1.0:
        classification = "linearized_unstable_transit_tube"
        warning = ""
    elif tube_resolved:
        classification = "linearized_gateway_tube"
        warning = ""
    elif neck_open_fraction < minimum_neck_open_fraction:
        classification = "neck_closed_or_intermittent"
        warning = "gateway neck is not open over the required interval fraction"
    else:
        classification = "projection_margin_unresolved"
        warning = "stable projection is not dominated by the unstable tube coordinate"
    return GatewayManifoldTubeCertificate(
        lagrange_point=nearest,
        sample_count=len(states),
        neck_open_fraction=neck_open_fraction,
        initial_unstable_projection=float(unstable_array[0]),
        terminal_unstable_projection=float(unstable_array[-1]),
        initial_stable_projection=float(stable_array[0]),
        terminal_stable_projection=float(stable_array[-1]),
        unstable_growth_ratio=unstable_growth,
        stable_decay_ratio=stable_decay,
        minimum_projection_margin=projection_margin,
        tube_resolved=tube_resolved,
        classification=classification,
        warning=warning,
    )


def restricted_chart_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    jacobi_tolerance: float = 1.0e-7,
) -> RestrictedChartCertificate:
    """Summarize CR3BP chart validity over a Lagrange or gateway interval."""

    if not hasattr(system, "jacobi_constant") or not hasattr(system, "lagrange_points"):
        raise TypeError("restricted_chart_certificate requires a restricted three-body system.")
    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    states = trajectory.y[start : end + 1]
    points = system.lagrange_points()
    names = tuple(points.keys())
    nearest_names = []
    nearest_distances = []
    jacobi_values = []
    for state in states:
        position = np.asarray(state[:2], dtype=float)
        distances = {name: float(np.linalg.norm(position - point)) for name, point in points.items()}
        nearest = min(distances, key=distances.get)
        nearest_names.append(nearest)
        nearest_distances.append(distances[nearest])
        jacobi_values.append(float(system.jacobi_constant(state)))
    nearest_lagrange = max(names, key=nearest_names.count)
    certificate_kind = "gateway_neck" if nearest_lagrange in {"L1", "L2", "L3"} else "lagrange_neighborhood"
    jacobi = np.asarray(jacobi_values, dtype=float)
    max_abs_jacobi_drift = float(np.max(np.abs(jacobi - jacobi[0]))) if jacobi.size else 0.0
    gateway_margins = []
    transit_likelihoods = []
    neck_open = []
    if certificate_kind == "gateway_neck":
        for state in states:
            estimate = gateway_transit_estimate(system, state)
            gateway_margins.append(estimate.jacobi_margin)
            transit_likelihoods.append(estimate.transit_likelihood)
            neck_open.append(float(estimate.neck_open))
    min_gateway_margin = float(np.min(gateway_margins)) if gateway_margins else None
    neck_open_fraction = float(np.mean(neck_open)) if neck_open else 0.0
    max_transit_likelihood = float(np.max(transit_likelihoods)) if transit_likelihoods else 0.0
    routh_stable = bool(
        nearest_lagrange in {"L4", "L5"}
        and float(system.mass_ratio) < 0.5 * (1.0 - np.sqrt(69.0) / 9.0)
    )
    numerically_resolved = bool(max_abs_jacobi_drift <= jacobi_tolerance)
    warning = ""
    if not numerically_resolved:
        warning = "Jacobi drift exceeds tolerance for restricted chart promotion"
    elif certificate_kind == "gateway_neck" and neck_open_fraction == 0.0:
        warning = "gateway neck is closed over the sampled interval"
    return RestrictedChartCertificate(
        nearest_lagrange=nearest_lagrange,
        certificate_kind=certificate_kind,
        sample_count=len(states),
        min_lagrange_distance=float(np.min(nearest_distances)),
        max_lagrange_distance=float(np.max(nearest_distances)),
        max_abs_jacobi_drift=max_abs_jacobi_drift,
        min_gateway_margin=min_gateway_margin,
        neck_open_fraction=neck_open_fraction,
        max_transit_likelihood=max_transit_likelihood,
        routh_stable_triangular=routh_stable,
        numerically_resolved=numerically_resolved,
        warning=warning,
    )


def _normalized_projection(displacement: np.ndarray, direction: np.ndarray) -> float:
    norm = float(np.linalg.norm(direction))
    if norm < 1.0e-12:
        return 0.0
    unit = direction / norm
    return float(np.dot(displacement, unit))
