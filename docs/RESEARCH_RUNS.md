# Research Runs

This project treats each numerical experiment as a research artifact, not just a rendered orbit.

**Paper status / 논문용 상태:** Commands in this file define reproducible runs.
They do not by themselves prove the associated hypotheses; paper use requires
the recorded commit, parameters, diagnostics, and guardrail interpretation.
이 문서의 명령은 재현 가능한 실행을 정의하지만, 그 자체로 가설을 증명하지
않는다. 논문에는 commit, parameter, diagnostics, guardrail 해석을 함께
제시해야 한다.

The command-line survey runner executes a perturbation ensemble, integrates each member, classifies the trajectory through the analysis atlas, builds the empirical transition graph, and exports candidate transition laws.

```powershell
threebody survey --scenario figure-eight --count 16 --periods 0.5 --samples 1200 --stride 20
```

For transition-law discovery, start with the hierarchical flyby benchmark because it is designed to leave and re-enter a binary hierarchy chart:

```powershell
threebody survey --scenario hierarchical-flyby --count 16 --validation-count 16 --periods 8 --samples 1200 --stride 20
```

The expected first-order law in this benchmark should involve `hierarchy_perturbation_strength`.
If the miner selects only generic features such as `virial_ratio`, the hierarchy chart is missing relevant Kepler/Jacobi features.

To test whether this boundary survives parameter changes:

```powershell
threebody flyby-sweep --duration 8 --samples 600 --stride 20
```

The sweep varies intruder mass, impact parameter, and incoming speed, then reports transition counts and hysteresis crossing estimates per case.
The aggregate crossing coefficient of variation is deliberately reported; a large CV means the current coordinate is useful but not yet a universal scalar threshold.
The sweep also reports `collapse_fits`, which fit a power-law boundary collapse of the form:

```text
perturbation_strength ~= C * encounter_adiabaticity^a * hierarchy_ratio^b
```

The important metric is `improvement = 1 - collapsed_cv / raw_cv`.
Positive improvement means the added coordinates reduce scatter in the boundary coordinate.
Small or near-zero improvement is a negative result: it means the proposed collapse variables are not enough and the boundary model needs another physical coordinate.

The cumulative collapse variants add:

- `relative_inner_energy_exchange`
- `relative_angular_momentum_exchange`
- `tidal_impulse = integral hierarchy_perturbation_strength dt`

These are encounter-level variables, not instantaneous boundary coordinates.
When cumulative fits improve much more than instantaneous fits, the interpretation should be that hierarchy breakdown is controlled by accumulated exchange over the encounter, not only by the local tidal strength at a sampled transition point.

To test overfitting, run a separate held-out flyby grid:

```powershell
threebody flyby-sweep --heldout --duration 8 --samples 600 --stride 20
```

This fits collapse exponents on the discovery grid and reports `collapse_validations` on a shifted validation grid.
The `best_validation_models` field selects the best held-out model separately for low and high crossings.
Models with `passes_validation = true` currently require validation improvement above `0.25`.
Best-model selection uses `complexity_penalized_validation_score = validation_improvement - 0.03 * feature_count` so that a larger feature set must earn its extra complexity on held-out data.
The `worst_validation_residuals` field lists the held-out cases with the largest log prediction error per model, which is the first place to look for missing physics.
If residuals cluster in a parameter region, that region should become the next benchmark family.

To test whether the model is phase-blind, add inner-binary phase variation:

```powershell
threebody flyby-sweep --heldout --phase-sweep --duration 8 --samples 600 --stride 20
```

This adds discovery phases `0` and `pi/2`, then validates against held-out phases `pi/4` and `3pi/4`.
The phase-conditioned collapse variants include `phase_alignment`, `phase_quadrature`, and `nonlinear_tidal_exposure`.
If these reduce held-out residuals in strong, slow flybys, the missing coordinate is not only accumulated impulse; it is the phase-resolved scattering map of the inner binary during the encounter.

To check whether a boundary is a resolution artifact:

```powershell
threebody boundary-resolution --duration 8
```

This reruns the same benchmark across sample counts and classification strides, then reports crossing CV across those numerical settings.

To run the broader research guardrails:

```powershell
threebody research-checks
```

This writes classifier-artifact sensitivity rows, adaptive-vs-structure-aware integrator comparison, known benchmark checks, regime probes, and a figure-eight stability probe.
The integrator comparison deliberately reports `regularized_available = false` until a real collision-regularized stepper exists.
Any close-encounter compact model is provisional while that flag is false.

To run the quick theorem candidate harness during development:

```powershell
threebody theorem-suite
```

To run the full paper-facing theorem candidate harness, including the Picard-certified 5x5x5 Jacobi parameter half-grid:

```powershell
threebody theorem-suite --mode paper
```

Both modes emit theorem candidates, proof obligations, and benchmark rows.
Only `--mode paper` is sufficient for paper-facing Jacobi parameter-box claims.
No row in this suite should be interpreted as a proof; it is a reproducibility and overclaim-prevention artifact.
The Jacobi representative-tail rows include a Picard resolution/tolerance crosscheck; paper claims should report both `jacobi_picard_resolution_crosscheck` and `jacobi_picard_resolution_margin_spread`.
They should also report `jacobi_picard_interval_jacobian_contraction`, which records the maximum Picard contraction computed from the interval Newtonian RHS Jacobian row-sum bound.
For the scattering conjecture, the suite reports both `low_crossing_scattering_map_score` and `low_crossing_scattering_map_selection`.
A positive score without selection means the feature family may contain signal, but it has not beaten simpler competing explanations.

The Jacobi escape rows now include `jacobi_terminal_tail_interval_reserve`.
This is not a replacement for interval-enclosed integration.
It is a finite-difference reserve over terminal tail-state perturbations, intended to make the next proof obligation explicit: replace sampled terminal-state sensitivity with a rigorous interval trajectory enclosure.

To export a reusable atlas benchmark artifact:

```powershell
threebody atlas-benchmark --scenario figure-eight --scenario hierarchical-flyby --scenario restricted-l4 --samples 240 --stride 20
```

The artifact records initial states, chart distributions, transition rows, and reproduction commands.
Use `--include-trajectories` when the sampled state arrays themselves should be included.

To split the run into discovery and validation ensembles:

```powershell
threebody survey --scenario figure-eight --count 16 --validation-count 16 --periods 0.5 --samples 1200 --stride 20
```

If the package is not installed as a command yet, run the module directly from the repository:

```powershell
python -m threebody.cli survey --scenario figure-eight --count 16 --periods 0.5 --samples 1200 --stride 20
```

The default output path is `.runtime/research_runs/<timestamp>-<scenario>.json`. The `.runtime` directory is intentionally ignored by Git because these files are generated evidence. Promote stable findings into `docs/` only after they survive repeated runs.

Each JSON artifact contains:

- `metadata`: scenario, integration span, sample count, and survey parameters.
- `summary.chart_distribution`: time-share of each interpretive chart for each ensemble member.
- `summary.transitions`: empirical chart-to-chart transition counts and probabilities.
- `summary.transition_events`: strongest feature change observed at each chart transition.
- `summary.transition_boundaries`: before/after/crossing estimates for the current boundary coordinate.
- `summary.hysteresis_loops`: paired low/high crossing estimates when both chart-transition directions are observed.
- `summary.candidate_laws`: simple feature intervals that currently distinguish observed transitions.
- `summary.law_validation`: precision/recall rows when `--validation-count` is used.

The candidate laws are not yet the final theory. They are hypotheses for the next loop: rerun under wider perturbations, validate against held-out trajectories, then replace weak interval rules with chart-specific analytic models.
