from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class PerturbationMember:
    name: str
    state: np.ndarray
    perturbation: np.ndarray
    scale: float


@dataclass(slots=True)
class PerturbationEnsemble:
    """Deterministic state perturbations for transition surveys."""

    seed: int = 0
    recenter_general_three_body: bool = True

    def around_state(
        self,
        system: object,
        state: np.ndarray,
        count: int,
        position_scale: float,
        velocity_scale: float,
    ) -> tuple[PerturbationMember, ...]:
        if count < 1:
            raise ValueError("count must be >= 1.")
        rng = np.random.default_rng(self.seed)
        state = np.asarray(state, dtype=float)
        members = [PerturbationMember("base", state.copy(), np.zeros_like(state), 0.0)]
        for index in range(1, count):
            perturbation = self._sample_perturbation(system, state, rng, position_scale, velocity_scale)
            perturbed = state + perturbation
            if self.recenter_general_three_body and getattr(system, "body_count", None) == 3:
                perturbed = recenter_general_state(system, perturbed)
            members.append(PerturbationMember(f"perturb-{index:03d}", perturbed, perturbation, max(position_scale, velocity_scale)))
        return tuple(members)

    def _sample_perturbation(
        self,
        system: object,
        state: np.ndarray,
        rng: np.random.Generator,
        position_scale: float,
        velocity_scale: float,
    ) -> np.ndarray:
        perturbation = np.zeros_like(state)
        if getattr(system, "body_count", None) == 3:
            dimension = int(system.dimension)
            width = system.body_count * dimension
            perturbation[:width] = rng.normal(0.0, position_scale, size=width)
            perturbation[width:] = rng.normal(0.0, velocity_scale, size=width)
            return perturbation
        half = state.size // 2
        perturbation[:half] = rng.normal(0.0, position_scale, size=half)
        perturbation[half:] = rng.normal(0.0, velocity_scale, size=state.size - half)
        return perturbation


def recenter_general_state(system: object, state: np.ndarray) -> np.ndarray:
    positions, velocities = system.split_state(state)
    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    center_velocity = np.average(velocities, axis=0, weights=masses)
    positions = positions - center
    velocities = velocities - center_velocity
    return system.flatten_state(positions, velocities)
