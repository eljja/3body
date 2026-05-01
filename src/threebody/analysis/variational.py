from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class LocalLinearization:
    """Finite-difference linearization of the flow around one state."""

    jacobian: np.ndarray
    eigenvalues: np.ndarray
    spectral_radius: float
    stiffness_ratio: float


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
