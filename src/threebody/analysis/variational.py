from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from ..types import TrajectoryResult


@dataclass(frozen=True, slots=True)
class LocalLinearization:
    """Finite-difference linearization of the flow around one state."""

    jacobian: np.ndarray
    eigenvalues: np.ndarray
    spectral_radius: float
    stiffness_ratio: float


@dataclass(frozen=True, slots=True)
class PeriodicMonodromyCertificate:
    """Finite-difference flow-map certificate for a periodic-neighborhood segment."""

    start_time: float
    end_time: float
    duration: float
    state_dimension: int
    perturbation: float
    spectral_radius: float
    condition_number: float
    endpoint_error: float
    closure_error: float
    closure_ratio: float
    shadowing_radius_proxy: float
    full_period_candidate: bool
    numerically_resolved: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "state_dimension": self.state_dimension,
            "perturbation": self.perturbation,
            "spectral_radius": self.spectral_radius,
            "condition_number": self.condition_number,
            "endpoint_error": self.endpoint_error,
            "closure_error": self.closure_error,
            "closure_ratio": self.closure_ratio,
            "shadowing_radius_proxy": self.shadowing_radius_proxy,
            "full_period_candidate": self.full_period_candidate,
            "numerically_resolved": self.numerically_resolved,
            "warning": self.warning,
        }


def finite_difference_jacobian(
    system: object,
    state: np.ndarray,
    time: float = 0.0,
    step: float = 1.0e-6,
) -> np.ndarray:
    state = np.asarray(state, dtype=float)
    jacobian = np.zeros((state.size, state.size), dtype=float)
    for column in range(state.size):
        perturbation = np.zeros_like(state)
        perturbation[column] = step
        forward = system.rhs(time, state + perturbation)
        backward = system.rhs(time, state - perturbation)
        jacobian[:, column] = (forward - backward) / (2.0 * step)
    return jacobian


def local_linearization(
    system: object,
    state: np.ndarray,
    time: float = 0.0,
    step: float = 1.0e-6,
) -> LocalLinearization:
    jacobian = finite_difference_jacobian(system, state, time=time, step=step)
    eigenvalues = np.linalg.eigvals(jacobian)
    magnitudes = np.abs(eigenvalues)
    spectral_radius = float(np.max(magnitudes))
    nonzero = magnitudes[magnitudes > 1.0e-12]
    stiffness_ratio = float(np.max(nonzero) / np.min(nonzero)) if nonzero.size else 0.0
    return LocalLinearization(
        jacobian=jacobian,
        eigenvalues=eigenvalues,
        spectral_radius=spectral_radius,
        stiffness_ratio=stiffness_ratio,
    )


def periodic_monodromy_certificate(
    system: object,
    trajectory: TrajectoryResult,
    start_index: int = 0,
    end_index: int | None = None,
    perturbation: float = 1.0e-7,
    rtol: float = 1.0e-7,
    atol: float = 1.0e-9,
) -> PeriodicMonodromyCertificate:
    """Approximate a segment flow map and report monodromy/shadowing diagnostics.

    This is a numerical certificate. It is not a Floquet proof unless the segment is also
    independently certified as a full return period.
    """

    end = len(trajectory.t) - 1 if end_index is None else min(end_index, len(trajectory.t) - 1)
    start = max(0, min(start_index, end))
    start_time = float(trajectory.t[start])
    end_time = float(trajectory.t[end])
    duration = float(end_time - start_time)
    state = np.asarray(trajectory.y[start], dtype=float)
    target = np.asarray(trajectory.y[end], dtype=float)
    if duration <= 0.0:
        return PeriodicMonodromyCertificate(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            state_dimension=state.size,
            perturbation=perturbation,
            spectral_radius=0.0,
            condition_number=np.inf,
            endpoint_error=0.0,
            closure_error=float(np.linalg.norm(target - state)),
            closure_ratio=0.0,
            shadowing_radius_proxy=0.0,
            full_period_candidate=False,
            numerically_resolved=False,
            warning="zero-duration segment; monodromy is not resolved",
        )

    base_end, base_success = _flow_endpoint(system, (start_time, end_time), state, rtol=rtol, atol=atol)
    matrix = np.zeros((state.size, state.size), dtype=float)
    success = base_success
    for column in range(state.size):
        delta = np.zeros_like(state)
        delta[column] = perturbation
        forward, forward_success = _flow_endpoint(system, (start_time, end_time), state + delta, rtol=rtol, atol=atol)
        backward, backward_success = _flow_endpoint(system, (start_time, end_time), state - delta, rtol=rtol, atol=atol)
        matrix[:, column] = (forward - backward) / (2.0 * perturbation)
        success = success and forward_success and backward_success

    eigenvalues = np.linalg.eigvals(matrix)
    spectral_radius = float(np.max(np.abs(eigenvalues)))
    condition_number = float(np.linalg.cond(matrix))
    endpoint_error = float(np.linalg.norm(base_end - target))
    closure_error = float(np.linalg.norm(target - state))
    state_scale = max(float(np.linalg.norm(state)), 1.0e-12)
    closure_ratio = float(closure_error / state_scale)
    amplification = max(spectral_radius * condition_number, 1.0)
    shadowing_radius = float(perturbation / amplification)
    full_period_candidate = bool(closure_ratio < 1.0e-2)
    numerically_resolved = bool(success and np.isfinite(condition_number) and endpoint_error < 1.0e-5)
    warning = ""
    if not success:
        warning = "one or more perturbed flow integrations failed"
    elif not full_period_candidate:
        warning = "segment is not a full-period return; monodromy is a local flow-map proxy"
    elif not numerically_resolved:
        warning = "flow-map endpoint error or conditioning is too large for promotion"
    return PeriodicMonodromyCertificate(
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        state_dimension=state.size,
        perturbation=perturbation,
        spectral_radius=spectral_radius,
        condition_number=condition_number,
        endpoint_error=endpoint_error,
        closure_error=closure_error,
        closure_ratio=closure_ratio,
        shadowing_radius_proxy=shadowing_radius,
        full_period_candidate=full_period_candidate,
        numerically_resolved=numerically_resolved,
        warning=warning,
    )


def _flow_endpoint(
    system: object,
    t_span: tuple[float, float],
    state: np.ndarray,
    *,
    rtol: float,
    atol: float,
) -> tuple[np.ndarray, bool]:
    solution = solve_ivp(
        fun=system.rhs,
        t_span=t_span,
        y0=np.asarray(state, dtype=float),
        method="DOP853",
        rtol=rtol,
        atol=atol,
        t_eval=(t_span[1],),
    )
    if solution.y.size == 0:
        return np.full_like(state, np.nan, dtype=float), False
    return np.asarray(solution.y[:, -1], dtype=float), bool(solution.success)
