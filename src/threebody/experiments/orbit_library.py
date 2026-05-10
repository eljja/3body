from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..solvers.analytic import AnalyticTwoBodySolver
from ..systems import GeneralThreeBodySystem, RestrictedThreeBodySystem, TwoBodySystem
from ..types import Scenario
from ..utils import orbit_period


@dataclass(slots=True)
class OrbitLibrary:
    """Reference scenarios used for validation and exploration."""

    two_body_solver: AnalyticTwoBodySolver = field(default_factory=AnalyticTwoBodySolver)

    def two_body_elliptic(
        self,
        semimajor_axis: float = 1.0,
        eccentricity: float = 0.2,
        primary_mass: float = 1.0,
        secondary_mass: float = 1.0e-3,
        periods: float = 1.0,
        samples: int = 2000,
    ) -> Scenario:
        system = TwoBodySystem(primary_mass=primary_mass, secondary_mass=secondary_mass)
        initial_state = self.two_body_solver.state_from_elements(system, semimajor_axis, eccentricity, 0.0)
        period = orbit_period(system.gravitational_parameter, semimajor_axis)
        t_eval = np.linspace(0.0, periods * period, samples)
        return Scenario(
            name="two-body-elliptic",
            system=system,
            initial_state=initial_state,
            t_span=(0.0, float(t_eval[-1])),
            t_eval=t_eval,
            description="Keplerian baseline orbit in relative coordinates.",
            metadata={"period": period, "eccentricity": eccentricity},
        )

    def restricted_l4(
        self,
        mass_ratio: float = 0.0121505856,
        perturbation: tuple[float, float, float, float] = (0.01, 0.0, 0.0, 0.0),
        periods: float = 15.0,
        samples: int = 4000,
    ) -> Scenario:
        system = RestrictedThreeBodySystem(mass_ratio=mass_ratio)
        lagrange = system.lagrange_points()["L4"]
        initial_state = np.array(
            [
                lagrange[0] + perturbation[0],
                lagrange[1] + perturbation[1],
                perturbation[2],
                perturbation[3],
            ],
            dtype=float,
        )
        end_time = 2.0 * math.pi * periods
        t_eval = np.linspace(0.0, end_time, samples)
        return Scenario(
            name="restricted-l4",
            system=system,
            initial_state=initial_state,
            t_span=(0.0, end_time),
            t_eval=t_eval,
            description="Perturbed planar restricted three-body trajectory near L4.",
            metadata={"lagrange_point": "L4"},
        )

    def restricted_l5(
        self,
        mass_ratio: float = 0.0121505856,
        perturbation: tuple[float, float, float, float] = (0.01, 0.0, 0.0, 0.0),
        periods: float = 15.0,
        samples: int = 4000,
    ) -> Scenario:
        system = RestrictedThreeBodySystem(mass_ratio=mass_ratio)
        lagrange = system.lagrange_points()["L5"]
        initial_state = np.array(
            [
                lagrange[0] + perturbation[0],
                lagrange[1] + perturbation[1],
                perturbation[2],
                perturbation[3],
            ],
            dtype=float,
        )
        end_time = 2.0 * math.pi * periods
        t_eval = np.linspace(0.0, end_time, samples)
        return Scenario(
            name="restricted-l5",
            system=system,
            initial_state=initial_state,
            t_span=(0.0, end_time),
            t_eval=t_eval,
            description="Perturbed planar restricted three-body trajectory near L5.",
            metadata={"lagrange_point": "L5"},
        )

    def general_figure_eight(
        self,
        periods: float = 1.0,
        samples: int = 5000,
        perturbation_scale: float = 0.0,
    ) -> Scenario:
        system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
        positions = np.array(
            [
                [0.97000436, -0.24308753],
                [-0.97000436, 0.24308753],
                [0.0, 0.0],
            ],
            dtype=float,
        )
        velocities = np.array(
            [
                [0.4662036850, 0.4323657300],
                [0.4662036850, 0.4323657300],
                [-0.93240737, -0.86473146],
            ],
            dtype=float,
        )
        if perturbation_scale:
            positions[0, 0] += perturbation_scale
            positions[1, 0] -= perturbation_scale
        initial_state = system.flatten_state(positions, velocities)
        figure_eight_period = 6.32591398
        end_time = periods * figure_eight_period
        t_eval = np.linspace(0.0, end_time, samples)
        return Scenario(
            name="general-figure-eight",
            system=system,
            initial_state=initial_state,
            t_span=(0.0, end_time),
            t_eval=t_eval,
            description="Chenciner-Montgomery style figure-eight orbit.",
            metadata={"period": figure_eight_period, "perturbation_scale": perturbation_scale},
        )

    def general_hierarchical_flyby(
        self,
        binary_separation: float = 0.2,
        binary_phase: float = 0.0,
        intruder_mass: float = 0.2,
        intruder_position: tuple[float, float] = (0.0, -2.0),
        intruder_velocity: tuple[float, float] = (0.8, 1.2),
        duration: float = 8.0,
        samples: int = 1200,
    ) -> Scenario:
        system = GeneralThreeBodySystem(masses=(1.0, 1.0, intruder_mass), dimension=2)
        half = 0.5 * binary_separation
        positions = np.array(
            [
                [-half, 0.0],
                [half, 0.0],
                [intruder_position[0], intruder_position[1]],
            ],
            dtype=float,
        )
        binary_speed = 0.5 * math.sqrt(
            system.gravitational_constant * (system.masses[0] + system.masses[1]) / binary_separation
        )
        velocities = np.array(
            [
                [0.0, binary_speed],
                [0.0, -binary_speed],
                [intruder_velocity[0], intruder_velocity[1]],
            ],
            dtype=float,
        )
        positions[:2] = _rotate_vectors(positions[:2], binary_phase)
        velocities[:2] = _rotate_vectors(velocities[:2], binary_phase)
        positions, velocities = _recenter(system, positions, velocities)
        initial_state = system.flatten_state(positions, velocities)
        t_eval = np.linspace(0.0, duration, samples)
        return Scenario(
            name="general-hierarchical-flyby",
            system=system,
            initial_state=initial_state,
            t_span=(0.0, duration),
            t_eval=t_eval,
            description="Tight binary perturbed by a third-body flyby, designed to create chart transitions.",
            metadata={
                "binary_separation": binary_separation,
                "binary_phase": binary_phase,
                "intruder_mass": intruder_mass,
                "intruder_position": intruder_position,
                "intruder_velocity": intruder_velocity,
            },
        )

    def general_close_encounter_probe(
        self,
        binary_separation: float = 0.02,
        intruder_mass: float = 0.05,
        intruder_position: tuple[float, float] = (1.0, 0.2),
        intruder_velocity: tuple[float, float] = (0.0, -0.1),
        duration: float = 0.02,
        samples: int = 401,
    ) -> Scenario:
        system = GeneralThreeBodySystem(masses=(1.0, 1.0, intruder_mass), dimension=2)
        half = 0.5 * binary_separation
        binary_speed = 0.5 * math.sqrt(
            system.gravitational_constant * (system.masses[0] + system.masses[1]) / binary_separation
        )
        positions = np.array(
            [
                [-half, 0.0],
                [half, 0.0],
                [intruder_position[0], intruder_position[1]],
            ],
            dtype=float,
        )
        velocities = np.array(
            [
                [0.0, binary_speed],
                [0.0, -binary_speed],
                [intruder_velocity[0], intruder_velocity[1]],
            ],
            dtype=float,
        )
        positions, velocities = _recenter(system, positions, velocities)
        initial_state = system.flatten_state(positions, velocities)
        t_eval = np.linspace(0.0, duration, samples)
        return Scenario(
            name="general-close-encounter-probe",
            system=system,
            initial_state=initial_state,
            t_span=(0.0, duration),
            t_eval=t_eval,
            description="Integrated close binary with third-body perturbation for Levi-Civita residual validation.",
            metadata={
                "binary_separation": binary_separation,
                "intruder_mass": intruder_mass,
                "intruder_position": intruder_position,
                "intruder_velocity": intruder_velocity,
            },
        )


def _recenter(system: GeneralThreeBodySystem, positions: np.ndarray, velocities: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    masses = np.asarray(system.masses, dtype=float)
    center = np.average(positions, axis=0, weights=masses)
    center_velocity = np.average(velocities, axis=0, weights=masses)
    return positions - center, velocities - center_velocity


def _rotate_vectors(vectors: np.ndarray, angle: float) -> np.ndarray:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    rotation = np.array([[cosine, -sine], [sine, cosine]], dtype=float)
    return vectors @ rotation.T

