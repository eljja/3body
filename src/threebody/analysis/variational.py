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


@dataclass(frozen=True, slots=True)
class VariationalMonodromyCertificate:
    """State-transition-matrix certificate for a candidate periodic orbit."""

    duration: float
    state_dimension: int
    jacobian_step: float
    closure_error: float
    closure_ratio: float
    determinant: float
    determinant_error: float
    reciprocal_pair_error: float
    symplectic_residual: float
    spectral_radius: float
    nontrivial_spectral_radius: float
    neutral_multiplier_count: int
    multiplier_magnitudes: tuple[float, ...]
    full_period_candidate: bool
    volume_preserving_proxy: bool
    reciprocal_pair_proxy: bool
    symplectic_proxy: bool
    linearly_stable_proxy: bool
    numerically_resolved: bool
    warning: str

    def as_dict(self) -> dict[str, float | int | bool | str | list[float]]:
        return {
            "duration": self.duration,
            "state_dimension": self.state_dimension,
            "jacobian_step": self.jacobian_step,
            "closure_error": self.closure_error,
            "closure_ratio": self.closure_ratio,
            "determinant": self.determinant,
            "determinant_error": self.determinant_error,
            "reciprocal_pair_error": self.reciprocal_pair_error,
            "symplectic_residual": self.symplectic_residual,
            "spectral_radius": self.spectral_radius,
            "nontrivial_spectral_radius": self.nontrivial_spectral_radius,
            "neutral_multiplier_count": self.neutral_multiplier_count,
            "multiplier_magnitudes": list(self.multiplier_magnitudes),
            "full_period_candidate": self.full_period_candidate,
            "volume_preserving_proxy": self.volume_preserving_proxy,
            "reciprocal_pair_proxy": self.reciprocal_pair_proxy,
            "symplectic_proxy": self.symplectic_proxy,
            "linearly_stable_proxy": self.linearly_stable_proxy,
            "numerically_resolved": self.numerically_resolved,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class VariationalMonodromyConvergenceCertificate:
    """Step-convergence guardrail for variational monodromy certificates."""

    certificates: tuple[VariationalMonodromyCertificate, ...]
    maximum_multiplier_spread: float
    maximum_closure_ratio: float
    maximum_determinant_error: float
    maximum_reciprocal_pair_error: float
    maximum_symplectic_residual: float
    all_linearly_stable: bool
    convergence_resolved: bool
    warning: str

    @property
    def reference(self) -> VariationalMonodromyCertificate:
        return self.certificates[len(self.certificates) // 2]

    def as_dict(self) -> dict[str, object]:
        return {
            "certificates": [certificate.as_dict() for certificate in self.certificates],
            "maximum_multiplier_spread": self.maximum_multiplier_spread,
            "maximum_closure_ratio": self.maximum_closure_ratio,
            "maximum_determinant_error": self.maximum_determinant_error,
            "maximum_reciprocal_pair_error": self.maximum_reciprocal_pair_error,
            "maximum_symplectic_residual": self.maximum_symplectic_residual,
            "all_linearly_stable": self.all_linearly_stable,
            "convergence_resolved": self.convergence_resolved,
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


def variational_monodromy_certificate(
    system: object,
    initial_state: np.ndarray,
    period: float,
    *,
    jacobian_step: float = 1.0e-6,
    rtol: float = 1.0e-7,
    atol: float = 1.0e-9,
    closure_tolerance: float = 5.0e-3,
    determinant_tolerance: float = 1.0e-4,
    reciprocal_tolerance: float = 1.0e-4,
    symplectic_tolerance: float = 1.0e-4,
    neutral_tolerance: float = 5.0e-2,
    stability_tolerance: float = 2.0e-3,
) -> VariationalMonodromyCertificate:
    """Integrate the variational equation and report Floquet-style diagnostics.

    The certificate is intentionally conservative: it promotes a periodic chart only
    when the orbit closes, the state-transition matrix is volume-preserving to the
    declared tolerance, and multiplier magnitudes are reciprocal-paired.
    """

    state = np.asarray(initial_state, dtype=float)
    state_dimension = int(state.size)
    if period <= 0.0:
        return _failed_variational_certificate(
            duration=float(period),
            state_dimension=state_dimension,
            jacobian_step=jacobian_step,
            warning="non-positive period; variational monodromy is undefined",
        )

    identity = np.eye(state_dimension, dtype=float)
    combined_initial = np.concatenate([state, identity.reshape(-1)])

    def combined_rhs(time: float, combined_state: np.ndarray) -> np.ndarray:
        current_state = combined_state[:state_dimension]
        transition = combined_state[state_dimension:].reshape(state_dimension, state_dimension)
        jacobian = finite_difference_jacobian(system, current_state, time=time, step=jacobian_step)
        transition_dot = jacobian @ transition
        return np.concatenate([system.rhs(time, current_state), transition_dot.reshape(-1)])

    solution = solve_ivp(
        fun=combined_rhs,
        t_span=(0.0, float(period)),
        y0=combined_initial,
        method="DOP853",
        rtol=rtol,
        atol=atol,
        t_eval=(float(period),),
    )
    if not solution.success or solution.y.size == 0:
        return _failed_variational_certificate(
            duration=float(period),
            state_dimension=state_dimension,
            jacobian_step=jacobian_step,
            warning="combined state/variational integration failed",
        )

    final = np.asarray(solution.y[:, -1], dtype=float)
    final_state = final[:state_dimension]
    transition = final[state_dimension:].reshape(state_dimension, state_dimension)
    multipliers = np.linalg.eigvals(transition)
    magnitudes = tuple(float(value) for value in sorted(np.abs(multipliers)))
    determinant = float(np.linalg.det(transition))
    determinant_error = float(abs(determinant - 1.0))
    reciprocal_pair_error = _reciprocal_pair_error(magnitudes)
    symplectic_residual = _symplectic_residual(system, transition, state_dimension)
    spectral_radius = float(max(magnitudes))
    nontrivial = [value for value in magnitudes if abs(value - 1.0) > neutral_tolerance]
    nontrivial_spectral_radius = float(max(nontrivial)) if nontrivial else 1.0
    neutral_multiplier_count = len(magnitudes) - len(nontrivial)
    closure_error = float(np.linalg.norm(final_state - state))
    closure_ratio = float(closure_error / max(float(np.linalg.norm(state)), 1.0e-12))

    full_period_candidate = closure_ratio <= closure_tolerance
    volume_preserving_proxy = determinant_error <= determinant_tolerance
    reciprocal_pair_proxy = reciprocal_pair_error <= reciprocal_tolerance
    symplectic_proxy = symplectic_residual <= symplectic_tolerance
    linearly_stable_proxy = (
        full_period_candidate
        and volume_preserving_proxy
        and reciprocal_pair_proxy
        and symplectic_proxy
        and nontrivial_spectral_radius <= 1.0 + stability_tolerance
    )
    numerically_resolved = bool(np.all(np.isfinite(magnitudes)) and np.isfinite(determinant))
    warning = ""
    if not full_period_candidate:
        warning = "orbit does not close tightly enough for periodic-chart promotion"
    elif not volume_preserving_proxy:
        warning = "state-transition determinant is outside the volume-preserving tolerance"
    elif not reciprocal_pair_proxy:
        warning = "multiplier magnitudes do not pass the reciprocal-pair tolerance"
    elif not symplectic_proxy:
        warning = "state-transition matrix is outside the symplectic residual tolerance"
    elif not linearly_stable_proxy:
        warning = "nontrivial Floquet multiplier magnitude exceeds the stability tolerance"

    return VariationalMonodromyCertificate(
        duration=float(period),
        state_dimension=state_dimension,
        jacobian_step=jacobian_step,
        closure_error=closure_error,
        closure_ratio=closure_ratio,
        determinant=determinant,
        determinant_error=determinant_error,
        reciprocal_pair_error=reciprocal_pair_error,
        symplectic_residual=symplectic_residual,
        spectral_radius=spectral_radius,
        nontrivial_spectral_radius=nontrivial_spectral_radius,
        neutral_multiplier_count=neutral_multiplier_count,
        multiplier_magnitudes=magnitudes,
        full_period_candidate=full_period_candidate,
        volume_preserving_proxy=volume_preserving_proxy,
        reciprocal_pair_proxy=reciprocal_pair_proxy,
        symplectic_proxy=symplectic_proxy,
        linearly_stable_proxy=linearly_stable_proxy,
        numerically_resolved=numerically_resolved,
        warning=warning,
    )


def variational_monodromy_convergence_certificate(
    system: object,
    initial_state: np.ndarray,
    period: float,
    *,
    jacobian_steps: tuple[float, ...] = (2.0e-6, 1.0e-6, 5.0e-7),
    multiplier_spread_tolerance: float = 2.0e-3,
    rtol: float = 1.0e-7,
    atol: float = 1.0e-9,
) -> VariationalMonodromyConvergenceCertificate:
    """Check that a periodic monodromy certificate is not a step-size artifact."""

    certificates = tuple(
        variational_monodromy_certificate(
            system,
            initial_state,
            period,
            jacobian_step=step,
            rtol=rtol,
            atol=atol,
        )
        for step in jacobian_steps
    )
    if not certificates:
        return VariationalMonodromyConvergenceCertificate(
            certificates=(),
            maximum_multiplier_spread=np.inf,
            maximum_closure_ratio=np.inf,
            maximum_determinant_error=np.inf,
            maximum_reciprocal_pair_error=np.inf,
            maximum_symplectic_residual=np.inf,
            all_linearly_stable=False,
            convergence_resolved=False,
            warning="no jacobian steps were supplied",
        )

    multiplier_matrix = np.array([certificate.multiplier_magnitudes for certificate in certificates], dtype=float)
    maximum_multiplier_spread = float(np.max(np.ptp(multiplier_matrix, axis=0))) if multiplier_matrix.size else np.inf
    maximum_closure_ratio = float(max(certificate.closure_ratio for certificate in certificates))
    maximum_determinant_error = float(max(certificate.determinant_error for certificate in certificates))
    maximum_reciprocal_pair_error = float(max(certificate.reciprocal_pair_error for certificate in certificates))
    maximum_symplectic_residual = float(max(certificate.symplectic_residual for certificate in certificates))
    all_linearly_stable = all(certificate.linearly_stable_proxy for certificate in certificates)
    convergence_resolved = bool(
        all_linearly_stable
        and maximum_multiplier_spread <= multiplier_spread_tolerance
        and all(certificate.numerically_resolved for certificate in certificates)
    )
    warning = ""
    if not all_linearly_stable:
        warning = "at least one step failed the variational stability proxy"
    elif maximum_multiplier_spread > multiplier_spread_tolerance:
        warning = "Floquet multiplier magnitudes vary too much across jacobian steps"

    return VariationalMonodromyConvergenceCertificate(
        certificates=certificates,
        maximum_multiplier_spread=maximum_multiplier_spread,
        maximum_closure_ratio=maximum_closure_ratio,
        maximum_determinant_error=maximum_determinant_error,
        maximum_reciprocal_pair_error=maximum_reciprocal_pair_error,
        maximum_symplectic_residual=maximum_symplectic_residual,
        all_linearly_stable=all_linearly_stable,
        convergence_resolved=convergence_resolved,
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


def _reciprocal_pair_error(magnitudes: tuple[float, ...]) -> float:
    if not magnitudes:
        return np.inf
    return float(max(abs(magnitudes[index] * magnitudes[-1 - index] - 1.0) for index in range(len(magnitudes))))


def _symplectic_residual(system: object, transition: np.ndarray, state_dimension: int) -> float:
    form = _velocity_state_symplectic_form(system, state_dimension)
    residual = transition.T @ form @ transition - form
    return float(np.linalg.norm(residual, ord="fro") / max(np.linalg.norm(form, ord="fro"), 1.0e-12))


def _velocity_state_symplectic_form(system: object, state_dimension: int) -> np.ndarray:
    half_dimension = state_dimension // 2
    if state_dimension % 2:
        return np.full((state_dimension, state_dimension), np.nan, dtype=float)

    if hasattr(system, "masses") and hasattr(system, "body_count") and hasattr(system, "dimension"):
        masses = np.asarray(getattr(system, "masses"), dtype=float)
        body_count = int(getattr(system, "body_count"))
        dimension = int(getattr(system, "dimension"))
        if body_count * dimension == half_dimension and masses.size == body_count:
            mass_entries = np.repeat(masses, dimension)
            mass_matrix = np.diag(mass_entries)
        else:
            mass_matrix = np.eye(half_dimension, dtype=float)
    else:
        mass_matrix = np.eye(half_dimension, dtype=float)

    zero = np.zeros((half_dimension, half_dimension), dtype=float)
    return np.block([[zero, mass_matrix], [-mass_matrix, zero]])


def _failed_variational_certificate(
    *,
    duration: float,
    state_dimension: int,
    jacobian_step: float,
    warning: str,
) -> VariationalMonodromyCertificate:
    return VariationalMonodromyCertificate(
        duration=duration,
        state_dimension=state_dimension,
        jacobian_step=jacobian_step,
        closure_error=np.inf,
        closure_ratio=np.inf,
        determinant=np.nan,
        determinant_error=np.inf,
        reciprocal_pair_error=np.inf,
        symplectic_residual=np.inf,
        spectral_radius=np.inf,
        nontrivial_spectral_radius=np.inf,
        neutral_multiplier_count=0,
        multiplier_magnitudes=(),
        full_period_candidate=False,
        volume_preserving_proxy=False,
        reciprocal_pair_proxy=False,
        symplectic_proxy=False,
        linearly_stable_proxy=False,
        numerically_resolved=False,
        warning=warning,
    )
