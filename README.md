# ThreeBody

`ThreeBody` is a research project for building an analysis atlas of the two-body, restricted three-body, and general Newtonian three-body problems.

The project is built around five ideas:

- Use the two-body problem as an analytic baseline.
- Treat simulation as instrumentation, not as the final objective.
- Combine classical mechanics, perturbation theory, regularization, continuation, invariant manifolds, and data-assisted discovery.
- Decompose state space into interpretive charts and track transitions between them.
- Build compact models only inside explicitly identified charts.

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
- `analysis`
  - `AnalysisAtlas`
  - `ChartClassifier`
  - `jacobi_open_escape_cone_certificate`
  - `jacobi_quadrupole_acceleration_certificate`
  - `finite_difference_jacobian`
  - local chart transition detection
- `experiments`
  - `OrbitLibrary`
  - `InitialConditionScanner`
  - `CompactModelFitter`
- `ui`
  - Streamlit application for interactive exploration
  - Static GitHub Pages visualizer generated from precomputed reference runs

## Scientific Position

The project does not treat the three-body problem as something to merely visualize.
The goal is to construct a working analysis method.

- The two-body problem remains the analytic reference because center-of-mass separation and relative-coordinate reduction turn it into a one-body central-force problem.
- The general three-body problem is not generically integrable by one global formula, so the project treats it as an atlas problem.
- Each region of state space should be assigned an interpretive chart: hierarchy, restricted/Lagrange, close encounter, periodic-orbit neighborhood, chaotic transport, or escape/scattering.
- A real result is a chart, a validity condition, a reduced model, and a transition rule to neighboring charts.
- The current theorem candidate is the conditional Jacobi escape cone: a hierarchy/escape regime certified by Jacobi energy split, quadrupole future-tail bound, inflated margin, self-consistent radial floor, open-cone radius, and parameter-box reserve checks.

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

Build the static GitHub Pages visualizer:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.ui.static_site --output site
```

Run a transition survey:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli survey --scenario hierarchical-flyby --count 16 --validation-count 16 --periods 8 --samples 1200 --stride 20
```

## Documentation

- [Project Scope](docs/PROJECT_SCOPE.md)
- [Science Foundation](docs/SCIENCE_FOUNDATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Research Program](docs/RESEARCH_PROGRAM.md)
- [Research Runs](docs/RESEARCH_RUNS.md)
- [Current Hypotheses](docs/CURRENT_HYPOTHESES.md)
- [Jacobi Escape Cone Theorem](docs/JACOBI_ESCAPE_CONE_THEOREM.md)
- [GitHub Pages Static Visualizer](docs/GITHUB_PAGES.md)
- [Roadmap](docs/ROADMAP.md)

## Suggested Workflow

1. Use the simulator to generate trusted trajectories and invariant diagnostics.
2. Classify each trajectory segment into an analysis chart.
3. Apply the chart-specific method: Kepler reduction, restricted manifolds, regularization, continuation, sections, or local linearization.
4. Record where chart transitions occur and build reduced models only inside validated chart domains.
