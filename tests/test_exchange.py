from __future__ import annotations

from threebody.analysis import encounter_exchange_metrics
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_encounter_exchange_metrics_are_positive_for_flyby() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=300)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    metrics = encounter_exchange_metrics(scenario.system, trajectory, inner_pair=(0, 1))

    assert metrics.inner_pair == (0, 1)
    assert metrics.relative_inner_energy_exchange >= 0.0
    assert metrics.relative_angular_momentum_exchange >= 0.0
    assert metrics.tidal_impulse > 0.0
