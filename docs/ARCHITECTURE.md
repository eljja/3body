# Architecture

## Package Layout

### `src/threebody/systems`

Defines the equations of motion and invariant-related helpers.

- `TwoBodySystem`
- `RestrictedThreeBodySystem`
- `GeneralThreeBodySystem`

### `src/threebody/solvers`

Provides propagation strategies.

- `AnalyticTwoBodySolver`
- `AdaptiveIntegrator`
- `StructureAwareIntegrator`

### `src/threebody/diagnostics`

Converts trajectories into interpretable physical signals.

- `InvariantMonitor`
- `StabilityAnalyzer`
- `PhaseSpaceTools`

### `src/threebody/analysis`

Turns trajectories into interpretive structure.

- `AnalysisAtlas`
- `ChartClassifier`
- `ChartScore`
- `ChartTransition`
- `TransitionGraph`
- `FeatureConditionedTransitionModel`
- `hierarchical_elements`
- `shape_space_coordinates`
- `TransitionSurvey`
- `ResearchPipeline`
- `TransitionLawValidator`
- `finite_difference_jacobian`
- `local_linearization`

### `src/threebody/cli.py`

Runs repeatable research jobs from the command line.

- `threebody survey`
- `python -m threebody.cli survey`
- `python -m threebody.cli verify-static-artifacts --site-dir site --require-commit local --require-profile public-claims-v1 --require-current-feature-set`
- `python -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-commit <sha-or-prefix> --require-profile public-claims-v1 --require-current-feature-set --output .runtime/research_runs/pages-verification-receipt.json`

### `src/threebody/experiments`

Packages repeatable experiment setup.

- `OrbitLibrary`
- `InitialConditionScanner`
- `CompactModelFitter`

### `src/threebody/ui`

Contains the Streamlit interface for interactive inspection.
The static Pages build also renders a compact public claim audit chain that mirrors the certificate JSON: commit provenance, scientific gates, bounded numerical drift, public artifacts, active profile digest checks, and the verifier capability-set digest are visible in the browser and machine-readable in `certificate.json`.

## Design Principles

- Solver-first: the visualizer is built on top of a reusable simulation core.
- Verification-first: every major subsystem should be benchmarkable.
- Structure-aware: invariants and geometry matter as much as raw trajectory output.
- Regime-specific reduction: reduced models must declare scope and error.

## Current Data Flow

1. A scenario is created by `OrbitLibrary`.
2. A solver integrates the chosen system.
3. Diagnostics derive invariant drift, sensitivity, or phase-space summaries.
4. The analysis atlas classifies trajectory segments into interpretive charts.
5. `ResearchPipeline` can perturb the initial condition, repeat the integration, and mine candidate transition laws.
6. The UI renders trajectories, diagnostic panels, chart distributions, and transition events.
7. Compact modeling tools fit local surrogates only after a chart has been identified.

## Immediate Extension Points

- collision regularization for close encounters
- richer phase-space sampling
- manifold tracking near equilibrium points
- better compact-model validation and reporting
- chart-specific normal forms
- transition maps between analysis charts
