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

Next tests:

- Sweep intruder mass, velocity, and impact parameter.
- Measure whether the threshold scales with `(m_outer / m_inner_pair) * (r_inner / r_outer)^3`.
- Replace fixed intervals with a chart boundary model in perturbation-strength and hierarchy-ratio coordinates.
- Validate on held-out seeds and reject the law if precision or recall collapses outside the declared flyby regime.
