# Validation Guardrails

This file defines what the project is not allowed to claim yet.

## Current Proof Level

The project has an empirical atlas and falsification harness.
It does not have a global solution of the Newtonian three-body problem.
It also does not yet have theorem-level error bounds for every chart.
`threebody theorem-suite` runs quick development checks by default.
Paper-facing Jacobi parameter-box claims require `threebody theorem-suite --mode paper`.

Allowed claims:

- A benchmark trajectory belongs to a chart under the current classifier.
- A proposed transition model reduced held-out scatter inside a declared benchmark family.
- A compact model is provisional unless it survives held-out sweeps, artifact checks, and invariant-drift checks.

Forbidden claims:

- General three-body closed-form solution.
- Universal transition threshold across all masses, energies, and angular momenta.
- Close-encounter law without a true regularized integrator or equivalent collision chart.
- Lagrange-neck transport law before the gateway classifier beats the generic Lagrange-neighborhood classifier.

## Required Checks Before Promoting A Law

- Held-out validation: report validation CV or error, not only training fit.
- Model selection: report feature count, AIC, BIC, leave-one-out error, or bootstrap/OOB error where sample count allows it.
- Classifier artifact: rerun with threshold and stride perturbations.
- Integrator artifact: compare adaptive and structure-aware integration and inspect invariant drift.
- Benchmark anchoring: pass known reference scenarios relevant to the chart.
- Scope declaration: name the regime where the model is valid and explicitly reject extrapolation outside it.

## Current Gaps

- `ReducedThreeBodyState` now centralizes shape-scale-invariant coordinates, but the main classifier still partly uses older feature objects. Migration should be gradual and tested against existing chart labels.
- Periapsis phase is now measured from the trajectory, and the first `scattering_map` collapse includes periapsis distance and deflection angle. The scattering diagnostic now also reports outgoing semimajor axis, eccentricity, periapsis distance, and escape speed at infinity.
- The stricter `theorem-suite` currently does not reproduce the low-crossing scattering-map win from the smaller smoke run. This blocks any breakthrough claim based on that model.
- The current `theorem-suite` partially supports `low_crossing_impulse`, but the high-crossing best model does not yet pass the paper threshold. A two-sided hierarchy-boundary theorem is not justified.
- Hysteresis-width collapse also fails in the theorem harness, so re-entry should not be forced into a scalar boundary model. The current admissible target is a chart-sequence/return-map branch model, and it must be reported separately from scalar boundary collapse.
- Branch models must report their predeclared feature protocol, discovery leave-one-out accuracy, baseline accuracy, and held-out validation accuracy. Do not select branch features by held-out validation score.
- Branch promotion requires both a positive discovery leave-one-out signal and a wider held-out phase sweep; held-out accuracy alone is not sufficient.
- Branch promotion also requires classifier-threshold and stride perturbation robustness. A branch law that only works for one atlas setting remains an artifact candidate.
- Binary grammar branch validation uses a lower score threshold than scalar boundary collapse because it is a quantile-branch classifier, not a continuous boundary fit. The current threshold is `0.18` after complexity penalty.
- Branch claims must report positive-margin certified accuracy and certified fraction. Accuracy without decision margin is not enough for theorem promotion.
- Branch margin certificates must also survive classifier-threshold and stride perturbations.
- Branch laws must beat negative controls computed on the same held-out split: feature-only nearest-neighbor classification and deterministically permuted chart-word classification.
- If only one branch beats these controls, the theorem candidate must split by branch instead of promoting a unified grammar law.
- The theorem suite must report which explanation wins per branch. A feature-selected branch and a grammar-selected branch are not the same theorem.
- `Chart-Word Grammar` now separates the coarse alphabet from a refined physical alphabet. Refined word diversity survives the current held-out flyby harness, but this is still a symbolic proxy. It cannot be promoted until classifier perturbations and a genuine Poincare/return-map construction agree with the refined words.
- AIC, BIC, leave-one-out, and bootstrap/OOB diagnostics exist for flyby collapse fits, but the sample count is still small.
- A true regularized collision integrator is missing, but a McGehee-style scale/shape collision diagnostic now separates hyperradius, radial velocity, shape area, anisotropy, and collision depth.
- Lagrange gateway transport now has a linearized L1/L2/L3 transit estimate based on neck openness and stable/unstable eigendirection projection. It is not yet a full invariant-manifold computation.
- Shape-space close encounter support is currently a diagnostic blow-up coordinate, not a fully regularized flow.
- Escape scattering is detected as a regime, but outgoing asymptotic Kepler-element convergence is not yet enforced.
- Jacobi escape now has a local interval-arithmetic tail-state certificate, an a posteriori interval RHS flow-tube check, and segment-wise Picard propagation of interval start boxes with an interval Newtonian RHS Jacobian contraction bound. This is stronger than scalar margin inflation and finite-difference terminal reserve, but it is not yet an independent CAPD-grade proof. Claims must say "segment-wise interval Picard certified over the sampled Jacobi tail" unless interval parameters and the full initial-value problem are propagated by a production validated integrator.
- Jacobi Picard claims must state whether the final margin uses the sampled defect-tube radius or the propagated endpoint enclosure radius. Paper-facing rows must use the propagated endpoint radius.
- Jacobi representative-tail claims must also report the Picard resolution/tolerance crosscheck. Passing one adaptive-integrator output is not enough to argue that the local cone is independent of solver settings.
- Jacobi parameter-box claims may cite the continuum-style reserve only as a finite-difference reserve over Picard-certified margins. They must not call it a rigorous interval-parameter derivative bound until mass, velocity, phase, and tail-state derivatives are interval-enclosed.
- Jacobi parameter-box promotion must include the parameter-cell midpoint, face-center, and edge-center checks. Passing only the grid nodes is no longer sufficient for paper-facing claims.
- Jacobi parameter-box promotion must also report the 5x5x5 half-grid reserve. The original 3x3x3 reserve is no longer sufficient on its own.
- Jacobi paper-mode promotion must report the 64 local half-grid subcell reserves. A single global half-grid reserve is no longer sufficient on its own.
