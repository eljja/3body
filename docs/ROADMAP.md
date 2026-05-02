# Roadmap

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
