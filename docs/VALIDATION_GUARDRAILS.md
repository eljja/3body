# Validation Guardrails

This file defines what the project is not allowed to claim yet.

## Current Proof Level

The project has an empirical atlas and falsification harness.
It does not have a global solution of the Newtonian three-body problem.
It also does not yet have theorem-level error bounds for every chart.

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

- Periapsis phase is now measured from the trajectory, and the first `scattering_map` collapse includes periapsis distance and deflection angle. The scattering diagnostic now also reports outgoing semimajor axis, eccentricity, periapsis distance, and escape speed at infinity.
- AIC, BIC, leave-one-out, and bootstrap/OOB diagnostics exist for flyby collapse fits, but the sample count is still small.
- A true regularized collision integrator is missing, but a McGehee-style scale/shape collision diagnostic now separates hyperradius, radial velocity, shape area, anisotropy, and collision depth.
- Lagrange gateway transport now has a linearized L1/L2/L3 transit estimate based on neck openness and stable/unstable eigendirection projection. It is not yet a full invariant-manifold computation.
- Shape-space close encounter support is currently a diagnostic blow-up coordinate, not a fully regularized flow.
- Escape scattering is detected as a regime, but outgoing asymptotic Kepler-element convergence is not yet enforced.
