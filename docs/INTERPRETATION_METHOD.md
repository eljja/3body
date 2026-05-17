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

The representative certificate suite is:

```powershell
threebody interpretation-suite
```

It currently runs hierarchical flyby, restricted L4, synthetic escape scattering, and close-encounter probes through the same certificate pipeline. The intended role is a coverage dashboard: it reports which chart types are locally interpretable, which numerical obligations are resolved, and which blockers still prevent theorem-level promotion.

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

General three-body certificates now include a center-of-mass reduction guardrail where applicable. The translational quotient frame must keep center position, center velocity, and total linear momentum below tolerance before periodic/Floquet/choreography claims are interpreted.

General three-body trajectories also include a Lagrange-Jacobi identity guardrail where applicable: the sampled trajectory must satisfy `I'' = 4E + 2U` in the center-of-mass frame. This checks the global scale/virial structure imposed by the Newtonian `1/r` potential.

General three-body trajectories also include Sundman's inequality guardrail where applicable: sampled states must satisfy `|L|^2 <= 2 I T` in the center-of-mass frame. This constrains the physically admissible region of reduced scale-angular-momentum space.

Hierarchy segments now include a numerical action-drift certificate: the inner Kepler action and angular momentum drift are compared against a tidal perturbation budget. This resolves a numerical certification task, but it does not replace the remaining analytic proof obligation.

Hierarchy segments also include a resonance-detuning certificate: the median inner/outer frequency ratio is compared with small-denominator rational resonances. This numerically separates near-resonant and nonresonant intervals, but the stability of that split still needs a proof.

Periodic-neighborhood segments now include a finite-difference flow-map monodromy certificate: spectral radius, condition number, endpoint error, closure ratio, and a shadowing-radius proxy. For declared periodic candidates, the research checks also include a variational monodromy certificate by integrating `dPhi/dt = J(t) Phi`. The figure-eight benchmark now checks sampled Hamiltonian Jacobian structure `A^T Omega + Omega A ~= 0`, orbit closure, volume preservation through `det(Phi)`, mass-weighted symplectic preservation `Phi^T Omega Phi ~= Omega`, reciprocal Floquet-multiplier pairing, the `T/3` choreography body-permutation symmetry, a linear-stability proxy, and a Jacobian-step convergence guardrail. This is a theorem candidate certificate, not yet an interval-arithmetic proof.

Escape segments now include an asymptotic convergence certificate: outgoing two-body energy, tail energy drift, radius growth, deflection drift, and escape speed at infinity. A finite trajectory is only promoted to escape support when the outgoing tail is energetically positive and numerically convergent.

Close-encounter segments now include a collision-regularization certificate: minimum pair distance, hyperradius, collision depth, observed collision type, inward speed, whether regularized coordinates are required, whether a planar Levi-Civita binary chart reconstructs the inertial relative coordinate over the interval, whether a perturbation-aware regularized-time RHS is defined, and whether local inertial-equivalence residuals are controlled. Predeclared integrated grids now validate both the regularized RHS residual and the reconstructed inertial acceleration residual, including a near-collision scaling grid down to binary separation `0.008`. The current normalized residual slope is nonnegative, and the third-body perturbation obeys both measured and Lipschitz tidal certificates of the form `perturbation/Kepler <= C r^3` on the declared grid. This is still a finite certificate, not an analytic limiting theorem.

Restricted Lagrange and gateway segments now include a CR3BP certificate: nearest Lagrange point, Jacobi drift, Lagrange-neighborhood distance range, Routh stability for triangular points, and neck/transit diagnostics for collinear gateways.

This is the current honest answer to "is the three-body problem interpreted?":

> Individual trajectories can now be interpreted locally by an explicit atlas. A general theorem requires completing the certificate obligations.

The `InterpretationSuite` result is the current regression target for that statement. It should stay at full local-interpretation coverage while the unresolved blocker count decreases over time.
