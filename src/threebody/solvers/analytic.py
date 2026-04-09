from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult
from ..utils import orbit_period, pad_to_3d, solve_kepler_elliptic


@dataclass(slots=True)
class AnalyticTwoBodySolver:
    """Analytic Kepler solver for bound two-body orbits."""

    def orbital_elements_from_state(self, system: object, state: np.ndarray) -> dict[str, np.ndarray | float]:
        position, velocity = system.split_state(state)
        mu = system.gravitational_parameter
        radius = np.linalg.norm(position)
        speed_sq = float(np.dot(velocity, velocity))
        specific_energy = 0.5 * speed_sq - mu / radius
        semimajor_axis = -mu / (2.0 * specific_energy)
        angular_momentum = system.specific_angular_momentum(state)
        eccentricity_vector = np.cross(pad_to_3d(velocity), angular_momentum) / mu - pad_to_3d(position) / radius
        eccentricity = float(np.linalg.norm(eccentricity_vector))
        if not (0.0 <= eccentricity < 1.0):
            raise ValueError("AnalyticTwoBodySolver currently supports bound elliptical orbits only.")
        true_anomaly = self.true_anomaly_from_state(position, velocity, eccentricity_vector)
        return {
            "semimajor_axis": semimajor_axis,
            "eccentricity": eccentricity,
            "eccentricity_vector": eccentricity_vector,
            "angular_momentum": angular_momentum,
            "true_anomaly": true_anomaly,
            "period": orbit_period(mu, semimajor_axis),
        }

    def true_anomaly_from_state(self, position: np.ndarray, velocity: np.ndarray, eccentricity_vector: np.ndarray) -> float:
        radius = np.linalg.norm(position)
        eccentricity = np.linalg.norm(eccentricity_vector)
        if eccentricity < 1.0e-12:
            return float(np.arctan2(position[1], position[0]))
        cosine = np.dot(eccentricity_vector[: position.size], position) / (eccentricity * radius)
        cosine = np.clip(cosine, -1.0, 1.0)
        anomaly = float(np.arccos(cosine))
        if np.dot(position, velocity) < 0.0:
            anomaly = 2.0 * np.pi - anomaly
        return anomaly

    def state_from_elements(
        self,
        system: object,
        semimajor_axis: float,
        eccentricity: float,
        true_anomaly: float,
    ) -> np.ndarray:
        if not (0.0 <= eccentricity < 1.0):
            raise ValueError("Elliptic elements require 0 <= e < 1.")
        mu = system.gravitational_parameter
        radius = semimajor_axis * (1.0 - eccentricity**2) / (1.0 + eccentricity * np.cos(true_anomaly))
        position = radius * np.array([np.cos(true_anomaly), np.sin(true_anomaly)], dtype=float)
        angular_momentum = np.sqrt(mu * semimajor_axis * (1.0 - eccentricity**2))
        velocity = (mu / angular_momentum) * np.array(
            [-np.sin(true_anomaly), eccentricity + np.cos(true_anomaly)],
            dtype=float,
        )
        return np.concatenate([position[: system.dimension], velocity[: system.dimension]])

    def propagate(
        self,
        system: object,
        initial_state: np.ndarray,
        times: np.ndarray,
    ) -> TrajectoryResult:
        elements = self.orbital_elements_from_state(system, initial_state)
        semimajor_axis = float(elements["semimajor_axis"])
        eccentricity = float(elements["eccentricity"])
        eccentricity_vector = np.asarray(elements["eccentricity_vector"], dtype=float)
        angular_momentum = np.asarray(elements["angular_momentum"], dtype=float)
        true_anomaly_0 = float(elements["true_anomaly"])
        period = float(elements["period"])
        mu = system.gravitational_parameter
        times = np.asarray(times, dtype=float)

        eccentric_anomaly_0 = 2.0 * np.arctan2(
            np.sqrt(1.0 - eccentricity) * np.sin(true_anomaly_0 / 2.0),
            np.sqrt(1.0 + eccentricity) * np.cos(true_anomaly_0 / 2.0),
        )
        mean_motion = np.sqrt(mu / semimajor_axis**3)
        mean_anomaly_0 = eccentric_anomaly_0 - eccentricity * np.sin(eccentric_anomaly_0)
        mean_anomaly = mean_anomaly_0 + mean_motion * (times - times[0])
        eccentric_anomaly = solve_kepler_elliptic(mean_anomaly, eccentricity)

        if eccentricity > 1.0e-10:
            basis_x = eccentricity_vector / np.linalg.norm(eccentricity_vector)
        else:
            initial_position, _initial_velocity = system.split_state(initial_state)
            basis_x = pad_to_3d(initial_position) / np.linalg.norm(initial_position)
        basis_z = angular_momentum / np.linalg.norm(angular_momentum)
        basis_y = np.cross(basis_z, basis_x)

        x_pf = semimajor_axis * (np.cos(eccentric_anomaly) - eccentricity)
        y_pf = semimajor_axis * np.sqrt(1.0 - eccentricity**2) * np.sin(eccentric_anomaly)
        radius = semimajor_axis * (1.0 - eccentricity * np.cos(eccentric_anomaly))
        vx_pf = -np.sqrt(mu * semimajor_axis) * np.sin(eccentric_anomaly) / radius
        vy_pf = np.sqrt(mu * semimajor_axis) * np.sqrt(1.0 - eccentricity**2) * np.cos(eccentric_anomaly) / radius

        positions = np.outer(x_pf, basis_x) + np.outer(y_pf, basis_y)
        velocities = np.outer(vx_pf, basis_x) + np.outer(vy_pf, basis_y)
        states = np.hstack([positions[:, : system.dimension], velocities[:, : system.dimension]])

        return TrajectoryResult(
            t=times,
            y=states,
            success=True,
            message=f"Analytic propagation completed over {period:.6f} period units.",
            metadata={"period": period},
        )
