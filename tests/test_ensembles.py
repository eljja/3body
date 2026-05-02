from __future__ import annotations

import numpy as np

from threebody.analysis import PerturbationEnsemble
from threebody.experiments import OrbitLibrary


def test_perturbation_ensemble_preserves_general_centering() -> None:
    scenario = OrbitLibrary().general_figure_eight(samples=10)
    members = PerturbationEnsemble(seed=42).around_state(
        scenario.system,
        scenario.initial_state,
        count=4,
        position_scale=1.0e-3,
        velocity_scale=1.0e-3,
    )

    assert len(members) == 4
    positions, velocities = scenario.system.split_state(members[1].state)
    assert np.linalg.norm(np.mean(positions, axis=0)) < 1.0e-12
    assert np.linalg.norm(np.mean(velocities, axis=0)) < 1.0e-12
