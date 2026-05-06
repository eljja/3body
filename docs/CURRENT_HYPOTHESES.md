# Current Hypotheses

This file records falsifiable hypotheses produced by the current analysis machinery.
These are not final laws.
They are research targets that must survive wider sweeps, tighter tolerances, and held-out validation.

## H1: Hierarchical Flyby Boundary

Scenario:

```powershell
python -m threebody.cli survey --scenario hierarchical-flyby --count 4 --validation-count 4 --periods 8 --samples 400 --stride 20
```

Observed structure:

- The chart sequence leaves and re-enters `two_body_hierarchy`.
- Transition event evidence reports `hierarchy_ratio` as the strongest local jump at the chart boundary.
- Candidate law mining selects `hierarchy_perturbation_strength` as the most discriminating feature.

Discovery-law sketch:

- `two_body_hierarchy -> periodic_orbit_neighborhood` near `hierarchy_perturbation_strength ~= 0.0039`.
- `periodic_orbit_neighborhood -> two_body_hierarchy` near `hierarchy_perturbation_strength ~= 0.0001..0.0008`.

Held-out validation in the small smoke run:

- Precision is high in this narrow benchmark.
- Recall is low, so the interval is too narrow or the sampling stride misses part of the boundary.

Interpretation:

The first useful hypothesis is not that `virial_ratio` alone causes the transition.
The more physical statement is that the inner binary ceases to be the dominant chart when the third-body tidal perturbation scale crosses a local threshold, while the visible geometric symptom is a drop in hierarchy ratio.

Refinement:

The boundary is likely hysteretic rather than a single scalar threshold.
In the current smoke run, leaving the hierarchy chart and returning to it occur at different crossing estimates in `hierarchy_perturbation_strength`.
This suggests the active chart depends on both the instantaneous perturbation scale and the direction of motion through the boundary.

Counter-pressure:

The parameter sweep shows that the crossing estimate varies across intruder mass, impact parameter, and speed.
Therefore H1 should not be stated as a universal constant threshold.
The stronger and more defensible version is: `hierarchy_perturbation_strength` is a necessary boundary coordinate, but at least one additional coordinate is needed to collapse the boundary across flyby families.

Next tests:

- Sweep intruder mass, velocity, and impact parameter.
- Measure whether the threshold scales with `(m_outer / m_inner_pair) * (r_inner / r_outer)^3`.
- Replace fixed intervals with a chart boundary model in perturbation-strength and hierarchy-ratio coordinates.
- Search for the missing collapse coordinate: impact parameter, incoming speed, angular momentum exchange, or encounter time over inner binary period.
- The next explicit candidate is encounter adiabaticity: `encounter_time / inner_binary_period`.
- Test whether `perturbation_strength / (encounter_adiabaticity^a * hierarchy_ratio^b)` reduces boundary scatter compared with raw perturbation strength.

Current collapse result:

The first power-law collapse is weak.
In the current 12-case flyby sweep, adding encounter adiabaticity and hierarchy ratio reduces low-crossing CV only slightly and barely improves high-crossing CV.
This is evidence against the three-variable boundary model being sufficient.

Next candidate:

The missing coordinate is likely not another instantaneous geometry variable.
The next model should include accumulated exchange, such as inner binary energy change, angular momentum exchange, or an impulse-like integral over the encounter.

Implemented cumulative candidates:

- relative inner binary energy exchange
- relative inner binary angular momentum exchange
- tidal impulse integral over the encounter

Current cumulative-collapse result:

Adding cumulative exchange variables substantially improves the flyby boundary collapse in the current sweep.
The low-crossing improvement rises from a few percent with instantaneous variables to roughly half of the raw scatter.
The high-crossing improvement also becomes large.

Caveat:

This is still not a final law.
The current sweep has only about ten usable boundary samples, and the cumulative model has several fitted exponents.
The next validation must use a wider held-out sweep and report whether the improvement survives.

Held-out requirement:

The cumulative model should be considered credible only if validation improvement remains positive on a shifted flyby grid that was not used to fit the exponents.

Held-out ablation result:

Instantaneous models remain weak on held-out data.
Models containing cumulative encounter terms pass the current validation threshold.
The impulse-only model already captures much of the improvement, while exchange variables are especially competitive for the high crossing.
This strengthens the interpretation that the boundary is governed by accumulated encounter effect, not just instantaneous geometry.

Current held-out numbers:

- low crossing instantaneous improvement is only about `0.02`.
- high crossing instantaneous improvement is only about `0.10`.
- low crossing impulse-only improvement is about `0.54`.
- high crossing impulse-only improvement is about `0.44`.
- low crossing full cumulative improvement is about `0.55`.
- high crossing full cumulative improvement is about `0.56`.

Working interpretation:

The simplest surviving physical coordinate is the tidal impulse integral.
Energy and angular momentum exchange refine the model, especially for the high crossing, but the impulse result suggests the core mechanism is accumulated tidal forcing over the encounter.
After adding a feature-count penalty to held-out selection, the current preferred low-crossing model is usually impulse-only, while the preferred high-crossing model can shift to exchange variables.
This is a useful split: exit from hierarchy appears impulse-threshold-like, while re-entry remembers the energy/angular-momentum exchange history more strongly.

Resolution check:

The boundary-resolution smoke run indicates that the low crossing is stable across sample/stride settings.
The high crossing is more sensitive, but its numerical-setting scatter is still smaller than the cross-family scatter that the cumulative model explains.
This reduces the likelihood that the observed boundary collapse is only a sampling artifact.

Current miss pattern:

Worst held-out residuals cluster around larger intruder masses and slower incoming speeds.
The current power-law collapse therefore still under-models strong, slow encounters.
The next missing term is likely a nonlinear exchange or resonance coordinate, not just another instantaneous distance or speed feature.

## H2: Phase-Resolved Encounter Map

The existing cumulative models can still be wrong if they average over the inner binary's orbital phase.
For weak or fast encounters this may not matter much because the perturbation acts like a small impulse.
For strong, slow encounters, the intruder samples a finite arc of the binary orbit; the same mass, speed, impact parameter, and impulse can produce different exchange depending on the binary phase at closest approach.

Implemented test variables:

- `binary_phase`: initial phase of the inner circular binary.
- `phase_alignment`: positive orientation feature derived from the binary phase advanced over the encounter time.
- `phase_quadrature`: complementary phase feature, also positive for log-power fitting.
- `binary_phase_at_periapsis`: phase measured from the actual trajectory at the outer body's closest approach to the inner binary center of mass.
- `deflection_angle`: incoming-to-outgoing scattering angle of the outer body relative to the binary center of mass.
- `nonlinear_tidal_exposure`: `tidal_impulse * encounter_adiabaticity`, a first nonlinear proxy for slow strong encounters.

Falsifiable criterion:

If `--phase-sweep --heldout` reduces the worst residuals concentrated at large intruder mass and low incoming speed, then the boundary law must be stated as a phase-conditioned scattering map, not as a scalar impulse law.
If it does not, the next missing mechanism is more likely manifold topology or near-collision regularized dynamics.

First smoke result:

Initial-phase proxy terms reduce training scatter but do not reliably beat simpler impulse/exchange models on held-out selection.
After replacing the proxy with trajectory-measured periapsis phase and deflection angle, the `low_crossing_scattering_map` smoke run passes held-out validation and narrowly wins the low-crossing complexity-penalized score.
The high crossing still prefers the simpler impulse model in the current phase-heldout smoke run.
This suggests a split: hierarchy exit may need an actual scattering-map coordinate, while hierarchy re-entry is still dominated by accumulated impulse/exchange memory.

This is not yet a final law.
The scattering-map model has seven features and only a few dozen smoke samples, so it must survive larger bootstrap/OOB and leave-one-out diagnostics before being promoted.

## Guardrail Checks

The current code now exposes `threebody research-checks`.
This is not a proof suite; it is a falsification harness.

Current smoke observations:

- Classifier transitions survive small stride and threshold perturbations, but strict hierarchy settings can change transition counts. This means classifier-induced artifacts remain possible.
- Adaptive DOP853 currently shows smaller short-run energy drift than the fixed-step structure-aware Verlet smoke run, while Verlet remains the relevant symplectic baseline for long-run drift studies.
- No true regularized close-encounter integrator exists yet. Therefore close-encounter laws must not be promoted beyond provisional chart claims.
- L4/L5 geometry and the figure-eight period-return benchmark pass the current smoke tolerances.
- The current Lagrange-neck probe is still classified as `restricted_lagrange`, not `restricted_gateway`; the gateway classifier needs a stronger neck-specific test before claiming L1/L2 transport analysis.
