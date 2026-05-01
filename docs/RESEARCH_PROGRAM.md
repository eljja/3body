# Research Program

## Thesis

The three-body problem should be attacked as an atlas construction problem.

There may be no single global closed-form solution for the general Newtonian three-body problem, but that does not mean the system is only numerically observable.
Different regions of state space are analyzable by different tools.
The project goal is to identify those regions, apply the right local method, and model the transitions between them.

## Core Object: Analysis Atlas

An analysis atlas consists of:

- a set of charts,
- a classifier that decides which chart applies to a state,
- chart-specific coordinates and reduced variables,
- invariants or approximate invariants inside each chart,
- transition rules between charts,
- and error bounds or empirical validity tests.

## Initial Charts

### Two-Body Hierarchy

Applies when two bodies form a tight pair and the third body is far away.
Use Jacobi coordinates, Kepler elements, secular perturbation theory, and energy exchange diagnostics.

### Democratic Three-Body

Applies when all pair distances are comparable.
No pair dominates, so the analysis should focus on symmetry, shape space, virial structure, and local linearization.

### Close Encounter

Applies near collision or near-collision.
Use regularized coordinates before drawing conclusions from raw numerical trajectories.

### Restricted Lagrange

Applies near Lagrange point neighborhoods in the restricted problem.
Use local normal forms, zero-velocity geometry, Floquet analysis, and invariant manifolds.

### Restricted Gateway

Applies near L1/L2/L3 neck regions.
Use transport channels and manifold-guided transition analysis.

### Periodic-Orbit Neighborhood

Applies near known periodic or choreographic families.
Use continuation, monodromy matrices, Floquet multipliers, and stability islands.

### Chaotic Transport

Applies when no stable local reduction dominates.
Use Poincare sections, return maps, Lyapunov diagnostics, symbolic dynamics, and transport statistics.

### Escape Transport

Applies when scattering or escape dominates.
Use asymptotic Kepler elements, energy partition, and scattering maps.

## Proposed New Method

The working method is `Invariant-Transport Atlas`:

1. Integrate with invariant monitoring.
2. Convert each state into chart features.
3. Classify the active chart.
4. Apply the chart-specific model.
5. Detect chart transitions.
6. Fit local compact models only within chart-valid segments.
7. Build a graph of chart transitions across many trajectories.

The current codebase now contains the first version of that graph object through `TransitionGraph`.
It is deliberately empirical: transitions are counted first, then promoted into candidate laws only after enough trajectories have been sampled.

The next layer is `FeatureConditionedTransitionModel`.
It stores feature prototypes for observed transitions and predicts likely next charts from the current feature vector.
This is not meant to be a final theory.
It is the first falsifiable mechanism for asking whether a transition such as hierarchy to chaotic transport to escape has a repeatable condition.

The long-term claim should be measured by coverage:

- how much of state space is assigned to useful charts,
- how accurately each chart predicts local evolution,
- and how well transition rules predict movement between charts.

## What The GUI Is For

The GUI is not the product.
It is an instrument for seeing:

- the orbit,
- invariant drift,
- active chart distribution,
- transition events,
- and failures of the current classification.

When the GUI shows a trajectory, the important question is not only where the bodies are.
The important question is which theory is currently explaining them.
