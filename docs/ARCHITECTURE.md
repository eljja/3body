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
4. The UI renders trajectories and diagnostic panels.
5. Compact modeling tools fit local surrogates from generated data.

## Immediate Extension Points

- collision regularization for close encounters
- richer phase-space sampling
- manifold tracking near equilibrium points
- better compact-model validation and reporting
