from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult


@dataclass(frozen=True, slots=True)
class NoetherInvariantDriftCertificate:
    """Pass/fail certificate for Noether invariant drift along a trajectory."""

    sample_count: int
    maximum_energy_drift: float
    maximum_relative_energy_drift: float
    maximum_linear_momentum_norm: float
    maximum_angular_momentum_drift: float
    energy_tolerance: float
    relative_energy_tolerance: float
    linear_momentum_tolerance: float
    angular_momentum_tolerance: float
    invariants_resolved: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "sample_count": self.sample_count,
            "maximum_energy_drift": self.maximum_energy_drift,
            "maximum_relative_energy_drift": self.maximum_relative_energy_drift,
            "maximum_linear_momentum_norm": self.maximum_linear_momentum_norm,
            "maximum_angular_momentum_drift": self.maximum_angular_momentum_drift,
            "energy_tolerance": self.energy_tolerance,
            "relative_energy_tolerance": self.relative_energy_tolerance,
            "linear_momentum_tolerance": self.linear_momentum_tolerance,
            "angular_momentum_tolerance": self.angular_momentum_tolerance,
            "invariants_resolved": self.invariants_resolved,
        }


@dataclass(slots=True)
class InvariantMonitor:
    """Evaluate conserved quantities and drift diagnostics for each system type."""

    system: object

    def evaluate(self, trajectory: TrajectoryResult) -> dict[str, np.ndarray]:
        if hasattr(self.system, "jacobi_constant"):
            jacobi = np.array([self.system.jacobi_constant(state) for state in trajectory.y], dtype=float)
            return {
                "jacobi_constant": jacobi,
                "jacobi_drift": jacobi - jacobi[0],
            }

        if hasattr(self.system, "laplace_runge_lenz"):
            energy = np.array([self.system.total_energy(state) for state in trajectory.y], dtype=float)
            angular = np.array([np.linalg.norm(self.system.angular_momentum(state)) for state in trajectory.y], dtype=float)
            lrl = np.array([np.linalg.norm(self.system.laplace_runge_lenz(state)) for state in trajectory.y], dtype=float)
            return {
                "energy": energy,
                "energy_drift": energy - energy[0],
                "angular_momentum_norm": angular,
                "angular_momentum_drift": angular - angular[0],
                "lrl_norm": lrl,
            }

        energy = np.array([self.system.total_energy(state) for state in trajectory.y], dtype=float)
        momentum = np.array([np.linalg.norm(self.system.linear_momentum(state)) for state in trajectory.y], dtype=float)
        angular = np.array([np.linalg.norm(self.system.angular_momentum(state)) for state in trajectory.y], dtype=float)
        return {
            "energy": energy,
            "energy_drift": energy - energy[0],
            "linear_momentum_norm": momentum,
            "linear_momentum_drift": momentum - momentum[0],
            "angular_momentum_norm": angular,
            "angular_momentum_drift": angular - angular[0],
        }

    @staticmethod
    def drift_summary(values: np.ndarray) -> dict[str, float]:
        values = np.asarray(values, dtype=float)
        drift = values - values[0]
        return {
            "initial": float(values[0]),
            "final": float(values[-1]),
            "max_abs_drift": float(np.max(np.abs(drift))),
            "rms_drift": float(np.sqrt(np.mean(drift**2))),
        }


def noether_invariant_drift_certificate(
    system: object,
    trajectory: TrajectoryResult,
    *,
    energy_tolerance: float = 1.0e-8,
    relative_energy_tolerance: float = 1.0e-9,
    linear_momentum_tolerance: float = 1.0e-10,
    angular_momentum_tolerance: float = 1.0e-8,
) -> NoetherInvariantDriftCertificate:
    """Certify conservation of energy, linear momentum, and angular momentum."""

    if not hasattr(system, "total_energy") or not hasattr(system, "linear_momentum") or not hasattr(system, "angular_momentum"):
        raise TypeError("noether_invariant_drift_certificate requires energy, linear momentum, and angular momentum methods.")
    if len(trajectory.y) == 0:
        return NoetherInvariantDriftCertificate(
            sample_count=0,
            maximum_energy_drift=np.inf,
            maximum_relative_energy_drift=np.inf,
            maximum_linear_momentum_norm=np.inf,
            maximum_angular_momentum_drift=np.inf,
            energy_tolerance=energy_tolerance,
            relative_energy_tolerance=relative_energy_tolerance,
            linear_momentum_tolerance=linear_momentum_tolerance,
            angular_momentum_tolerance=angular_momentum_tolerance,
            invariants_resolved=False,
        )

    energies = np.array([system.total_energy(state) for state in trajectory.y], dtype=float)
    linear_momenta = np.array([np.linalg.norm(system.linear_momentum(state)) for state in trajectory.y], dtype=float)
    angular_momenta = np.array([system.angular_momentum(state) for state in trajectory.y], dtype=float)
    energy_drift = np.abs(energies - energies[0])
    angular_drift = np.linalg.norm(angular_momenta - angular_momenta[0], axis=1)
    maximum_energy_drift = float(np.max(energy_drift))
    maximum_relative_energy_drift = float(maximum_energy_drift / max(abs(float(energies[0])), 1.0))
    maximum_linear_momentum_norm = float(np.max(linear_momenta))
    maximum_angular_momentum_drift = float(np.max(angular_drift))
    return NoetherInvariantDriftCertificate(
        sample_count=int(len(trajectory.y)),
        maximum_energy_drift=maximum_energy_drift,
        maximum_relative_energy_drift=maximum_relative_energy_drift,
        maximum_linear_momentum_norm=maximum_linear_momentum_norm,
        maximum_angular_momentum_drift=maximum_angular_momentum_drift,
        energy_tolerance=energy_tolerance,
        relative_energy_tolerance=relative_energy_tolerance,
        linear_momentum_tolerance=linear_momentum_tolerance,
        angular_momentum_tolerance=angular_momentum_tolerance,
        invariants_resolved=bool(
            maximum_energy_drift <= energy_tolerance
            and maximum_relative_energy_drift <= relative_energy_tolerance
            and maximum_linear_momentum_norm <= linear_momentum_tolerance
            and maximum_angular_momentum_drift <= angular_momentum_tolerance
        ),
    )
