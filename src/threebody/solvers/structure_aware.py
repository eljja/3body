from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import TrajectoryResult


@dataclass(slots=True)
class StructureAwareIntegrator:
    """Velocity-Verlet integrator for separable Newtonian systems."""

    step_size: float = 1.0e-3

    def supports(self, system: object) -> bool:
        return hasattr(system, "acceleration_field") and hasattr(system, "body_count") and hasattr(system, "dimension")

    def integrate(
        self,
        system: object,
        t_span: tuple[float, float],
        initial_state: np.ndarray,
    ) -> TrajectoryResult:
        if not self.supports(system):
            raise ValueError("StructureAwareIntegrator requires an inertial position-velocity system with acceleration_field.")

        initial_state = np.asarray(initial_state, dtype=float)
        body_count = int(system.body_count)
        dimension = int(system.dimension)
        position_width = body_count * dimension
        if initial_state.size != 2 * position_width:
            raise ValueError("Initial state size does not match the system dimension.")

        start, stop = t_span
        span = stop - start
        steps = max(2, int(np.ceil(span / self.step_size)) + 1)
        dt = span / (steps - 1)
        t = np.linspace(start, stop, steps)
        y = np.zeros((steps, initial_state.size), dtype=float)
        y[0] = initial_state

        positions = initial_state[:position_width].reshape(body_count, dimension)
        velocities = initial_state[position_width:].reshape(body_count, dimension)
        acceleration = system.acceleration_field(positions)

        for index in range(1, steps):
            half_velocity = velocities + 0.5 * dt * acceleration
            next_positions = positions + dt * half_velocity
            next_acceleration = system.acceleration_field(next_positions)
            next_velocities = half_velocity + 0.5 * dt * next_acceleration

            positions = next_positions
            velocities = next_velocities
            acceleration = next_acceleration
            y[index] = np.concatenate([positions.reshape(-1), velocities.reshape(-1)])

        return TrajectoryResult(
            t=t,
            y=y,
            success=True,
            message=f"Structure-aware integration completed with fixed step {dt:.3e}.",
            metadata={"step_size": dt, "steps": steps},
        )
