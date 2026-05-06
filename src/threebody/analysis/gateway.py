from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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


def _normalized_projection(displacement: np.ndarray, direction: np.ndarray) -> float:
    norm = float(np.linalg.norm(direction))
    if norm < 1.0e-12:
        return 0.0
    unit = direction / norm
    return float(np.dot(displacement, unit))
