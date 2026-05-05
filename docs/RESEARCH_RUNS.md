# Research Runs

This project treats each numerical experiment as a research artifact, not just a rendered orbit.

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
