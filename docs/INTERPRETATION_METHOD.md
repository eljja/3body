# Three-Body Interpretation Method

This project does not claim a universal closed-form solution.
The working claim is stricter and more useful:

> A three-body trajectory can be interpreted by decomposing it into local dynamical charts, assigning each chart a valid model family, and proving or falsifying the transition laws between charts.

## Core Algorithm

1. Integrate the trajectory with invariant monitoring.
2. Classify sampled states into an atlas of local charts.
3. Merge consecutive states with the same dominant chart into interpretation segments.
4. Attach a local model family to each segment.
5. Attach a validity statement and unresolved proof obligations to each segment.
6. Emit an interpretation certificate: `theorem_ready`, `local_interpretation_available`, `regime_status`, blockers, and the path to a proof.
7. Treat transitions between segments as the real research object.

The code entry point is `ThreeBodyInterpreter`.
The command-line entry point is:

```powershell
threebody interpret --scenario hierarchical-flyby --periods 8.0 --samples 600 --stride 20
```

## Chart Families

- `two_body_hierarchy`: osculating Kepler binary plus tidal perturbation.
- `close_encounter`: regularized collision chart.
- `escape_transport`: asymptotic scattering map.
- `restricted_lagrange`: Lagrange normal form and monodromy.
- `restricted_gateway`: zero-velocity neck and invariant-manifold transport.
- `periodic_orbit_neighborhood`: periodic orbit monodromy.
- `chaotic_transport`: Poincare return map and symbolic dynamics.
- `democratic_three_body`: reduced shape-space atlas.

## Current Research Conclusion

The latest branch-selection evidence says a single explanation is wrong.

- `high_crossing` currently selects smooth scattering features.
- `hysteresis_width` currently selects chart-word memory.

So the interpretation strategy is branch-wise:

> Different transition branches may require different coordinates, and the project must select them by held-out competition against negative controls.

## What Would Count As A Real Solution Here

Not a closed-form formula for every initial condition.
The target is a theorem suite of the following form:

1. The atlas covers a declared large regime.
2. Each chart has an explicit local error bound.
3. Transitions have branch-wise validated laws.
4. Collision and escape charts have rigorous regularized/asymptotic bounds.
5. The selected explanation beats negative controls and independent integrators.

Only after those conditions are met can this be called an accepted interpretation theory for that regime.

## Certificate Meaning

- `theorem_ready`: every active segment has a resolved local bound and no unresolved obligations remain.
- `local_interpretation_available`: every active segment has a model family and a validity statement.
- `locally_interpretable_not_theorem_ready`: the trajectory can be explained chart-by-chart, but the proof obligations still block a theorem-level claim.

This is the current honest answer to "is the three-body problem interpreted?":

> Individual trajectories can now be interpreted locally by an explicit atlas. A general theorem requires completing the certificate obligations.
