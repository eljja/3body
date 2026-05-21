from __future__ import annotations

import math
from itertools import product

import numpy as np


def pad_to_3d(vector: np.ndarray) -> np.ndarray:
    array = np.asarray(vector, dtype=float)
    if array.shape == (3,):
        return array
    if array.shape == (2,):
        return np.array([array[0], array[1], 0.0], dtype=float)
    raise ValueError(f"Expected 2D or 3D vector, got {array.shape}.")


def cross_3d(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.cross(pad_to_3d(a), pad_to_3d(b))


def monomial_powers(dimension: int, degree: int) -> list[tuple[int, ...]]:
    powers: list[tuple[int, ...]] = []
    for total_degree in range(degree + 1):
        for candidate in product(range(total_degree + 1), repeat=dimension):
            if sum(candidate) == total_degree:
                powers.append(candidate)
    return powers


def solve_kepler_elliptic(mean_anomaly: np.ndarray, eccentricity: float, iterations: int = 12) -> np.ndarray:
    mean_anomaly = np.asarray(mean_anomaly, dtype=float)
    eccentric_anomaly = np.where(
        eccentricity < 0.8,
        mean_anomaly,
        np.pi * np.ones_like(mean_anomaly),
    )
    for _ in range(iterations):
        residual = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly) - mean_anomaly
        derivative = 1.0 - eccentricity * np.cos(eccentric_anomaly)
        eccentric_anomaly -= residual / derivative
    return eccentric_anomaly


def orbit_period(gravitational_parameter: float, semimajor_axis: float) -> float:
    return 2.0 * math.pi * math.sqrt(semimajor_axis**3 / gravitational_parameter)


def trapezoid_integral(values: np.ndarray, samples: np.ndarray) -> float:
    """Integrate sampled values with NumPy 1.x/2.x compatibility."""

    if hasattr(np, "trapezoid"):
        integrate = np.trapezoid
    else:
        integrate = np.trapz
    return float(integrate(values, samples))
