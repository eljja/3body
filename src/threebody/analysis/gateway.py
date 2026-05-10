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
