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

- Periapsis phase is now measured from the trajectory, and the first `scattering_map` collapse includes periapsis distance and deflection angle. It is still a power-law diagnostic, not a full outgoing-element scattering map.
- AIC, BIC, leave-one-out, and bootstrap/OOB diagnostics exist for flyby collapse fits, but the sample count is still small.
- A true regularized collision integrator is missing.
- Lagrange gateway transport needs a neck-specific classifier and invariant-manifold benchmark.
- Shape-space close encounter support is currently a chart label and error-bound statement, not a McGehee-style regularized flow.
- Escape scattering is detected as a regime, but outgoing asymptotic Kepler-element convergence is not yet enforced.
