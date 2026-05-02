from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .coordinates import PAIR_INDICES


@dataclass(frozen=True, slots=True)
class ShapeSpaceCoordinates:
    """Scale-separated triangle geometry for a general three-body state."""

    side_lengths: np.ndarray
    normalized_sides: np.ndarray
    signed_area: float
    normalized_area: float
    hyperradius: float
    anisotropy: float
    orientation: float


def shape_space_coordinates(system: object, state: np.ndarray) -> ShapeSpaceCoordinates:
    positions, _velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    centered = positions - center

    sides = np.array([np.linalg.norm(positions[i] - positions[j]) for i, j in PAIR_INDICES], dtype=float)
    perimeter = float(np.sum(sides))
    normalized_sides = sides / max(perimeter, 1.0e-12)

    area = _signed_area_2d(positions)
    side_sq_sum = float(np.sum(sides**2))
    normalized_area = float(4.0 * np.sqrt(3.0) * abs(area) / max(side_sq_sum, 1.0e-12))
    hyperradius = float(np.sqrt(np.sum(masses[:, None] * centered**2) / np.sum(masses)))
    anisotropy = float((np.max(sides) - np.min(sides)) / max(np.mean(sides), 1.0e-12))
    orientation = float(np.sign(area))

    return ShapeSpaceCoordinates(
        side_lengths=sides,
        normalized_sides=normalized_sides,
        signed_area=float(area),
        normalized_area=normalized_area,
        hyperradius=hyperradius,
        anisotropy=anisotropy,
        orientation=orientation,
    )


def _signed_area_2d(positions: np.ndarray) -> float:
    if positions.shape[1] < 2:
        return 0.0
    x = positions[:, 0]
    y = positions[:, 1]
    return float(0.5 * ((x[0] * (y[1] - y[2])) + (x[1] * (y[2] - y[0])) + (x[2] * (y[0] - y[1]))))
