# Theorem Candidates

These are not proven theorems.
They are the current smallest claims that could become publishable if their proof obligations are completed.

## Candidate 1: Reduced Shape-Scattering Atlas Conjecture

Claim:

For planar Newtonian three-body trajectories away from unresolved collision singularities, a finite atlas built from reduced shape-scale coordinates, hierarchy charts, collision diagnostics, Lagrange gateway linearization, and scattering maps can assign each sampled state a local explanatory regime with explicit validity controls.

Why this might be new:

The project is not trying to add one more special orbit.
It tries to unify local analytic regimes into a reproducible, falsifiable atlas centered on `ReducedThreeBodyState`.

Current proof status:

- `ReducedThreeBodyState` exists.
- Hierarchy, collision, gateway, escape, and scattering diagnostics exist.
- Held-out and artifact guardrails exist.
- No theorem-level covering proof exists.

Open proof obligations:

- Prove that the reduced coordinates separate the declared chart regimes under explicit inequalities.
- Prove local error bounds for each chart.
- Replace collision diagnostics with actual regularized flow.
- Replace gateway linearization with invariant-manifold transit certificates.

## Candidate 2: Hierarchy Exit Scattering Coordinate Conjecture

Claim:

For the declared hierarchical flyby family, low hierarchy-exit boundary collapse is improved by trajectory-measured periapsis phase, periapsis distance, and deflection angle compared with instantaneous geometry alone.

Current evidence:

- `flyby-sweep --heldout --phase-sweep` selected `low_crossing_scattering_map` in one smoke benchmark.
- `theorem-suite` did not reproduce that selection under its stricter paper harness, so the conjecture is currently not stable enough to promote.
- The model uses held-out masses, impact parameters, speeds, and binary phases.
- The model still has too many features for a theorem-level claim.

Open proof obligations:

- Run larger sweeps and publish bootstrap/OOB confidence intervals.
- Identify why scattering-map selection changes with sample count and validation grid.
- Separate two questions: whether the scattering model has positive held-out score, and whether it beats simpler impulse/exchange models.
- Derive perturbative bounds linking tidal impulse and measured scattering coordinates.
- Test against independent implementations and stricter integrator comparisons.

## Candidate 3: Impulse-Exchange Hierarchy Boundary Conjecture

Claim:

For the declared hierarchical flyby family, hierarchy exit and re-entry boundaries are better treated as accumulated encounter effects than as instantaneous geometric thresholds.

Why this candidate replaced the first scattering-map push:

The stricter theorem harness rejected the low-crossing scattering map.
That means the more defensible current target is not "phase/scattering wins", but "instantaneous threshold is insufficient and accumulated impulse/exchange variables are the surviving explanatory class."

Open proof obligations:

- Current theorem-suite status: low boundary is partial with `low_crossing_impulse`; high boundary is still failing under the current threshold.
- The suite now also tests `hysteresis_width` as a memory/re-entry target, but that target also fails in the current theorem harness.
- This suggests high/re-entry is not a scalar boundary-collapse problem yet; it likely needs a transition-word or return-map model.
- Prove or numerically dominate instantaneous-only models over larger held-out grids.
- Derive a perturbative bound connecting tidal impulse and inner-binary action variation.
- Separate low-boundary exit behavior from high-boundary re-entry memory.
- Test whether the selected model changes under longer integrations, smaller tolerances, and independent implementation.

## Candidate 4: Chart-Word Grammar Conjecture

Claim:

When scalar boundary collapse fails, the re-entry structure of a three-body trajectory may still be described by stable words over the chart alphabet and their transition grammar.

Why this is a different mathematical object:

The object is not a scalar threshold or a fitted physical feature.
It is a compressed word over an alphabet of dynamical charts.
The current diagnostics include transition entropy, reversal defect, primitive period, grammar rank, refined physical bins, and an extremum-based return-word proxy.

Current proof status for this candidate:

- Coarse chart words are stable but too low-diversity to trust.
- Refined physical chart words now pass the current held-out diversity check.
- Extremum-based return words now pass the current partial stability and diversity checks.
- High re-entry and hysteresis are now tested as grammar/phase branch classification problems, not scalar boundary-collapse problems.
- This is still not a theorem because no grammar invariant bound has been proved.

Open proof obligations:

- Show held-out word stability across flyby grids.
- Rule out the trivial explanation that the classifier alphabet is too coarse and every flyby compresses to the same word.
- Require held-out word diversity, not only nearest-neighbor word similarity.
- Define admissible grammar transformations for noisy chart classification.
- Upgrade the current extremum-based return-word proxy into a genuine Poincare/return-map construction.
- Prove that a grammar invariant predicts re-entry better than scalar high-crossing thresholds.
- Replace the current binary branch classifier with a multi-branch return-map partition and prove its error bound.

## Reproducibility

Run:

```powershell
threebody theorem-suite
```

The suite reports which obligations are partial, failing, or open.
