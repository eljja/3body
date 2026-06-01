# Roadmap

**Paper status / 논문용 상태:** Planning document only. Milestones listed here
are engineering/research targets, not evidence unless backed by the relevant
verification command, artifact receipt, or theorem-candidate document. 이 문서는
계획 문서이며, milestone은 관련 검증 명령, artifact receipt, 정리 후보
문서가 붙기 전까지 증거가 아니다.

## Phase 1: Baseline Complete

- package structure created
- analytic two-body baseline implemented
- adaptive and structure-aware integrators implemented
- restricted/general three-body scenarios implemented
- Streamlit visualizer implemented
- test suite passing

## Phase 2: Restricted Three-Body Depth

- promote the analysis atlas from first-pass classification to validated chart assignment
- improve basin scanning performance
- add explicit L1/L2/L3 orbit experiments
- expose zero-velocity energy slicing more clearly
- add stability classification around Lagrange neighborhoods

## Phase 3: General Three-Body Robustness

- expand `hierarchical_elements` into full Jacobi coordinates and asymptotic Kepler elements
- add close-encounter regularization
- improve long-horizon drift tracking
- add more benchmark families beyond figure-eight
- add configurable softening and comparison studies

## Phase 4: Transition Laws

- expand `FeatureConditionedTransitionModel` from centroids into validated feature-conditioned transition laws
- collect chart transition events across trajectory ensembles
- build transition graphs over state-space features
- validate gateway, close-encounter, hierarchy, and escape transitions
- compare transition prediction against direct integration

## Phase 5: Compact Models

- define target regimes explicitly
- fit local reduced models from trajectory ensembles
- report validity radius and error envelopes
- compare surrogate predictions against full integration

## Phase 6: Research Tooling

- parameter sweep automation
- dataset export for structured experiments
- batch transition surveys over perturbation ensembles
- persist `ResearchPipeline` outputs as datasets for repeated comparison
- richer reporting notebooks or dashboards
- remote repository and collaboration workflow

## Phase 7: Law Validation

- split transition evidence into discovery and validation ensembles
- reject candidate laws that do not transfer across perturbation seeds
- replace interval rules with chart-specific analytic criteria where possible
- track law coverage, false positives, and missed transitions as first-class metrics

## Current Push: Paper-Facing Candidate Certificates

These items are meant to make claims auditable enough for a paper supplement.
They are not, by themselves, completed theorem proofs.

- NumPy 1.x/2.x integration compatibility is part of the reproducibility baseline.
- Jacobi escape work now includes a terminal tail-state finite-difference reserve as a bridge from open-cone scalar sensitivity toward interval-enclosed trajectories.
- Jacobi escape work now includes interval arithmetic over nonzero outgoing tail-state boxes for the outer energy, interaction remainder, radial floor, hierarchy ratio, and future-tail exchange bound.
- Jacobi escape work now includes an a posteriori interval RHS flow-tube check over the outgoing tail, using trapezoid-defect tube radii and segment-wise interval vector-field inclusion.
- Jacobi escape work now includes segment-wise interval Picard propagation over the outgoing tail, with interval Newtonian RHS Jacobian contraction checks and endpoint-tube compatibility.
- Jacobi escape work now feeds the propagated Picard endpoint enclosure radius back into the interval Jacobi margin instead of relying only on the sampled defect-tube radius.
- Jacobi escape work now crosschecks the representative Picard-certified tail across predeclared sample-count and adaptive-tolerance settings.
- Jacobi escape parameter-box work now applies the finite-difference continuum reserve to Picard-certified margins, not only scalar-inflated margins.
- Jacobi escape parameter-box work now checks the full Picard-certified 5x5x5 half-grid and reports both global and 64 local smaller-subcell finite-difference reserves.
- Close-encounter work now includes Levi-Civita regularized-time step control so near-collision sampling quality can be audited before promoting residual claims.
- Restricted gateway work now includes a linearized manifold-tube interval certificate, separating single-state neck openness from sampled tube-like transit evidence.
- Atlas benchmarks can now be exported with `threebody atlas-benchmark` so chart labels, transition rows, initial states, and reproduction commands are packaged together.
