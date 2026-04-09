# ThreeBody

`ThreeBody` is a Python research sandbox for the two-body problem, the circular restricted three-body problem, and the general Newtonian three-body problem.

The project is built around four ideas:

- Use the two-body problem as an analytic baseline.
- Treat the restricted three-body problem as the first structured nonlinear target.
- Treat the general three-body problem as a high-precision numerical and dynamical-systems problem.
- Only propose compact models inside clearly declared validity regimes.

## What Is Implemented

- `systems`
  - `TwoBodySystem`
  - `RestrictedThreeBodySystem`
  - `GeneralThreeBodySystem`
- `solvers`
  - `AnalyticTwoBodySolver`
  - `AdaptiveIntegrator`
  - `StructureAwareIntegrator`
- `diagnostics`
  - `InvariantMonitor`
  - `StabilityAnalyzer`
  - `PhaseSpaceTools`
- `experiments`
  - `OrbitLibrary`
  - `InitialConditionScanner`
  - `CompactModelFitter`
- `ui`
  - Streamlit application for interactive exploration

## Scientific Position

The project does not attempt a universal closed-form solution of the three-body problem.

- The two-body problem is integrable because center-of-mass separation and relative-coordinate reduction turn it into a one-body central-force problem.
- The general three-body problem is not generically integrable in the same way because simultaneous interactions prevent the same variable separation and the system lacks enough independent first integrals for a global closed-form solution.
- The practical path is precise integration, invariant monitoring, phase-space analysis, and regime-specific reduced models.

## Quick Start

Install the package in editable mode:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pip install -e .[dev]
```

Run the test suite:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest
```

Launch the visualizer:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m streamlit run src/threebody/ui/app.py
```

## Documentation

- [Project Scope](docs/PROJECT_SCOPE.md)
- [Science Foundation](docs/SCIENCE_FOUNDATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Roadmap](docs/ROADMAP.md)

## Suggested Workflow

1. Validate the integrators against the analytic two-body baseline.
2. Explore Lagrange points, Jacobi drift, and zero-velocity curves in the restricted problem.
3. Reproduce the figure-eight orbit and perturb it to inspect sensitivity.
4. Fit compact local models only after selecting a narrow regime and declaring a validity radius.
