from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from ..types import TrajectoryResult


@dataclass(slots=True)
class AdaptiveIntegrator:
    """High-precision adaptive integrator wrapper around scipy.solve_ivp."""

    method: str = "DOP853"
    rtol: float = 1.0e-10
    atol: float = 1.0e-12
    max_step: float = np.inf

    def integrate(
        self,
        system: object,
        t_span: tuple[float, float],
        initial_state: np.ndarray,
        t_eval: np.ndarray | None = None,
    ) -> TrajectoryResult:
        solution = solve_ivp(
            fun=system.rhs,
            t_span=t_span,
            y0=np.asarray(initial_state, dtype=float),
            method=self.method,
            t_eval=t_eval,
            rtol=self.rtol,
            atol=self.atol,
            max_step=self.max_step,
        )
        y = solution.y.T if solution.y.size else np.empty((0, np.asarray(initial_state).size))
        return TrajectoryResult(
            t=solution.t,
            y=y,
            success=bool(solution.success),
            message=str(solution.message),
            metadata={
                "method": self.method,
                "nfev": solution.nfev,
                "njev": solution.njev,
                "nlu": solution.nlu,
            },
        )
