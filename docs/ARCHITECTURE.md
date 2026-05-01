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
- `finite_difference_jacobian`
- `local_linearization`

### `src/threebody/experiments`

Packages repeatable experiment setup.

- `OrbitLibrary`
- `InitialConditionScanner`
- `CompactModelFitter`

### `src/threebody/ui`

Contains the Streamlit interface for interactive inspection.

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
5. The UI renders trajectories, diagnostic panels, chart distributions, and transition events.
6. Compact modeling tools fit local surrogates only after a chart has been identified.

## Immediate Extension Points

- collision regularization for close encounters
- richer phase-space sampling
- manifold tracking near equilibrium points
- better compact-model validation and reporting
- chart-specific normal forms
- transition maps between analysis charts
