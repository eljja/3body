from __future__ import annotations

import numpy as np

from threebody.analysis import hierarchical_elements
from threebody.systems import GeneralThreeBodySystem


def test_hierarchical_elements_detects_bound_inner_binary() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.1), dimension=2)
    relative_speed = np.sqrt(2.0 / 0.1)
    positions = np.array([[-0.05, 0.0], [0.05, 0.0], [10.0, 0.0]])
    velocities = np.array([[0.0, -0.5 * relative_speed], [0.0, 0.5 * relative_speed], [0.0, 0.0]])
    state = system.flatten_state(positions, velocities)

    elements = hierarchical_elements(system, state)

    assert elements.inner_pair == (0, 1)
    assert elements.outer_body == 2
    assert elements.is_inner_bound
    assert elements.inner_eccentricity < 1.0e-8
    assert elements.perturbation_strength < 1.0e-6
