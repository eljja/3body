from __future__ import annotations

import numpy as np

from threebody.analysis import shape_space_coordinates
from threebody.analysis.coordinates import general_three_body_features
from threebody.systems import GeneralThreeBodySystem


def test_shape_space_coordinates_equilateral_triangle() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    positions = np.array(
        [
            [1.0, 0.0],
            [-0.5, np.sqrt(3.0) / 2.0],
            [-0.5, -np.sqrt(3.0) / 2.0],
        ]
    )
    velocities = np.zeros_like(positions)
    state = system.flatten_state(positions, velocities)

    shape = shape_space_coordinates(system, state)

    assert np.allclose(shape.normalized_sides, np.ones(3) / 3.0)
    assert shape.normalized_area > 0.9
    assert shape.anisotropy < 1.0e-12

    features = general_three_body_features(system, state)
    assert np.isclose(features.normalized_area, shape.normalized_area)
    assert np.isclose(features.hyperradius, shape.hyperradius)
    assert np.isclose(features.shape_anisotropy, shape.anisotropy)
