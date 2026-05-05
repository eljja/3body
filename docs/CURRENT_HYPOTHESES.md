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

Resolution check:

The boundary-resolution smoke run indicates that the low crossing is stable across sample/stride settings.
The high crossing is more sensitive, but its numerical-setting scatter is still smaller than the cross-family scatter that the cumulative model explains.
This reduces the likelihood that the observed boundary collapse is only a sampling artifact.
- Validate on held-out seeds and reject the law if precision or recall collapses outside the declared flyby regime.
