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

The shared state object is now `ReducedThreeBodyState`.
It removes the center-of-mass perspective and exposes the quantities that every chart should agree on:
energy, angular momentum, virial ratio, hyperradius, radial velocity, normalized shape area, anisotropy, nearest-pair distance, hierarchy ratio, perturbation strength, collision depth, escape depth, and a provisional regime hint.
This is the bridge from raw trajectory plotting to a real shape-scale atlas.

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
The current implementation exposes a McGehee-style diagnostic, not a full regularized flow:
it separates hyperradius, radial velocity, normalized triangle area, anisotropy, and collision depth.
Any law in this chart remains provisional until a regularized stepper or equivalent blow-up dynamics is implemented.

### Restricted Lagrange

Applies near Lagrange point neighborhoods in the restricted problem.
Use local normal forms, zero-velocity geometry, Floquet analysis, and invariant manifolds.

### Restricted Gateway

Applies near L1/L2/L3 neck regions.
Use transport channels and manifold-guided transition analysis.
The current implementation adds a linearized `gateway_transit_estimate` around the nearest collinear point.
It checks neck openness through Jacobi margin and projects the state onto stable/unstable eigendirections.
This is a first transit indicator, not yet a full invariant-manifold computation.

### Periodic-Orbit Neighborhood

Applies near known periodic or choreographic families.
Use continuation, monodromy matrices, Floquet multipliers, and stability islands.

### Chaotic Transport

Applies when no stable local reduction dominates.
Use Poincare sections, return maps, Lyapunov diagnostics, symbolic dynamics, and transport statistics.

### Escape Transport

Applies when scattering or escape dominates.
Use asymptotic Kepler elements, energy partition, and scattering maps.
The current scattering map now records outgoing semimajor axis, eccentricity, periapsis distance, and escape speed at infinity.
The next requirement is convergence of those outgoing elements over longer integrations.

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

The first chart-specific analyzer is `hierarchical_elements`.
When a two-body hierarchy is detected, it extracts the inner binary, its Kepler-like elements, the outer perturber, and a perturbation-strength estimate.
This turns the hierarchy chart from a label into a concrete analysis model.
Those hierarchy variables are now part of the general transition feature vector: nearest-pair specific energy, eccentricity, semimajor axis, outer specific energy, and third-body perturbation strength.
In the hierarchical flyby benchmark, the first mined law moves from a generic virial-ratio rule to a more interpretable perturbation-strength threshold.

The general three-body feature vector now includes scale-separated shape-space coordinates: normalized triangle area, hyperradius, and side-length anisotropy.
This matters because democratic motion, close approaches, hierarchy formation, and escape are not only energy events; they are also changes in triangle geometry.

`ReducedThreeBodyState` is the next consolidation step.
Future classifiers and compact models should depend on this reduced state first, then attach chart-specific refinements such as Kepler elements, McGehee collision diagnostics, Lagrange gateway projections, or scattering outgoing elements.

`TransitionSurvey` is the batch loop for this program.
It runs the atlas over multiple trajectories and returns chart reports, an empirical transition graph, and a feature-conditioned transition model.

`ResearchPipeline` closes the first full loop:

1. perturb a base scenario,
2. integrate each member,
3. classify trajectory segments into charts,
4. build transition evidence,
5. mine simple candidate laws.

This is the first version of the research machine.
It does not solve the three-body problem by itself, but it creates the mechanism for turning many controlled perturbations into falsifiable transition hypotheses.
The `ResearchRunResult.summary()` method exposes the output as chart distributions, transition rows, and candidate laws so runs can be compared over time.

The command-line survey runner writes those summaries to JSON artifacts under `.runtime/research_runs/`.
That gives the project a reproducible evidence trail: every proposed transition rule can be traced back to a concrete perturbation ensemble and rerun with tighter tolerances or larger samples.

`TransitionLawValidator` is the next guardrail.
Candidate laws discovered on one ensemble can now be tested on a held-out ensemble, producing precision and recall instead of relying on visual plausibility.

Current working hypotheses are recorded in `docs/CURRENT_HYPOTHESES.md`.
Only hypotheses with explicit scenario scope, candidate boundary variables, and validation metrics should be promoted into that file.

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
