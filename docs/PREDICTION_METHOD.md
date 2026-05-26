# Three-Body Prediction Method

This project now exposes the original practical target as an operational prediction layer.

For a general Newtonian three-body initial condition

```text
m_i > 0
r_i(0), v_i(0) in R^2 or R^3
```

the engine solves

```text
d r_i / dt = v_i
d v_i / dt = G sum_{j != i} m_j (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^(3/2)
```

and returns the positions `r_i(t)` at the requested target time. This is not a global closed-form solution claim. It is a reproducible numerical evaluation of the Newtonian flow map with conservation diagnostics.

## Deterministic Forecast

Use `threebody_engine.predict_three_body_positions(...)` or:

```powershell
threebody predict --input initial-state.json --target-time 0.5 --output prediction.json
```

Input JSON:

```json
{
  "masses": [1.0, 1.0, 1.0],
  "positions": [[0.97000436, -0.24308753], [-0.97000436, 0.24308753], [0.0, 0.0]],
  "velocities": [[0.466203685, 0.43236573], [0.466203685, 0.43236573], [-0.93240737, -0.86473146]],
  "target_time": 0.5
}
```

For probability forecasts, the same input may include `initial_state_covariance`. Its shape must match the flattened state dimension, `2 * 3 * dimension`: `12 x 12` in 2D or `18 x 18` in 3D. Empirical modes sample that covariance directly, and linearized modes propagate the same `P0` by the variational flow.

Output includes final positions, final velocities, solver metadata, and a Noether invariant drift certificate for energy, linear momentum, and angular momentum.

## One-Call Solution Bundle

Use `threebody_engine.solve_three_body_target_positions(...)` when the caller only needs the direct answer: `target_positions`, `target_position_distribution`, `target_position_table`, `center_of_mass_frame`, one row per body's target-time claim, and the core diagnostics. The table includes a relative 95% radius, `position_claim_strength`, and `recommended_readout` so callers can tell whether to publish a point coordinate, a confidence region, or only a distribution summary. The center-of-mass frame reports the same target positions relative to the mass-weighted center, which is the safer readout when inertial translation is not scientifically meaningful. Use `threebody_engine.solve_three_body_prediction_problem(...)` when the full audit bundle is needed, or:

```powershell
threebody predict --input initial-state.json --target-solution --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output target-solution.json
threebody predict --input initial-state.json --solution --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output solution.json
```

This is the most direct public API for the original project target. It returns:

- `target_positions`, `target_position_distribution`, and `target_position_table` in the compact `solve_three_body_target_positions(...)` answer.
- `prediction_summary`: a compact report-ready conclusion with a versioned schema, promoted claim type, point-position statement, probability statement, reliability/risk statements, key diagnostics, and per-body 95% confidence regions.
- `mathematical_statement`: the machine-readable mathematical problem statement: Newtonian equations, flow-map readout `r_i(t) = Pi_{r_i} Phi_t(x(0))`, probability push-forward `Law(X_t) = (Phi_t)_# Law(X_0)`, linearized covariance formula, promoted claim contract, and one row per body's target-time position claim.
- `answer.final_positions`: the three target-time positions from the deterministic flow.
- `answer.final_position_distribution`: mean, quantiles, covariance, confidence regions, and ensemble counts for the target-time position distribution.
- `answer.recommended_mode`: the promoted interpretation mode from the diagnostic report.
- `deterministic_ephemeris`: the sampled deterministic trajectory from `0` through `target_time`.
- `linearized_gaussian_ephemeris`: the sampled first-order Gaussian distribution from `0` through `target_time`.
- `distribution_ephemeris`: the sampled empirical position distribution from `0` through `target_time`.
- `ephemeris_distribution_comparison`: time-resolved mean/covariance gaps between the linearized Gaussian and empirical ephemerides, including the first break time if the linearized approximation leaves the configured gates.
- `interpretation_report`: the linearized/ensemble comparison and forecast-horizon verdict.

The bundle is intentionally not a closed-form theorem for all initial conditions. It is a reproducible computational answer: exact initial data produce a flow-map sample; uncertain initial data produce a pushed-forward empirical distribution; diagnostics say how strong the resulting claim is.

By default, the bundle uses a center-of-mass-preserving uncertainty model for both the empirical ensemble and the linearized Gaussian covariance. This keeps mass-weighted center-of-mass position and velocity fixed under initial perturbations, avoiding a comparison where the ensemble and Gaussian forecast start from different physical assumptions. When `initial_state_covariance` is supplied in the API call or input JSON, that full state covariance replaces the generated scale-based covariance in the empirical ensemble, linearized Gaussian ephemeris, forecast horizon, and interpretation report.

## Ephemeris Forecast

Use `threebody_engine.predict_three_body_ephemeris(...)` or:

```powershell
threebody predict --input initial-state.json --ephemeris --samples 256 --output ephemeris.json
```

This returns the sampled orbit table from `0` through `target_time`: times, positions for all three bodies, velocities for all three bodies, solver metadata, and the same Noether invariant certificate used by the final-state forecast. With `--include-invariant-series`, the JSON also includes energy and momentum diagnostics at each sampled time.

The ephemeris mode is the most direct answer to "where are the bodies over the forecast interval?" The final row is the same target-time position claim produced by the deterministic forecast, but the intermediate rows make the claim inspectable and reusable for visualization or external analysis.

If the input JSON includes `target_times`, ephemeris modes return exactly those requested times instead of an evenly spaced grid. The list must be strictly monotone from the integration start toward `target_time`, stay between `0` and `target_time`, and end at `target_time`.

Deterministic ephemeris and point forecast outputs also include `close_approach_diagnostics`: the minimum sampled pair distance, the body pair and time where it occurs, scale ratios, and a `regularization_recommended` flag. This is not a finite-radius collision claim; it is a warning that the forecast passed through a close-encounter regime where regularized coordinates or stricter step control may be required.

## Interpretation Report

Use `threebody_engine.predict_three_body_interpretation_report(...)` or:

```powershell
threebody predict --input initial-state.json --report --count 128 --position-scale 1e-6 --velocity-scale 1e-6 --output report.json
```

The report runs four prediction layers:

- deterministic flow-map evaluation
- local forecast-horizon estimation from variational uncertainty growth
- linearized Gaussian covariance push-forward
- empirical ensemble push-forward

It then compares the linearized and empirical final-position distributions. The comparison records the mean-position gap, covariance Frobenius gap, covariance relative gap, and mean gap in sigma units. The forecast-horizon section reports whether the target time remains inside the requested position-tolerance envelope. The verdict recommends one of:

- `linearized-gaussian`: the variational distribution agrees with the ensemble within the configured gates and the target time remains inside the local forecast horizon.
- `empirical-ensemble`: the ensemble is resolved, but nonlinear effects are large enough that linearization should not be promoted.
- `deterministic-only`: only the nominal trajectory is resolved.
- `unresolved`: the nominal or uncertainty propagation failed the diagnostics.

This is the default scientific handoff format because it answers not only "where are the bodies?" but also "which mathematical claim is defensible for this initial condition and forecast horizon?"

## Linearized Gaussian Forecast

For small observational uncertainty, use `threebody_engine.predict_three_body_linearized_distribution(...)` or:

```powershell
threebody predict --input initial-state.json --linearized-distribution --preserve-center-of-mass --position-scale 1e-6 --velocity-scale 1e-6 --output linearized.json
```

This integrates the variational equation along the nominal trajectory. If `Phi_t` is the flow map and `P0` is the initial covariance, the returned covariance is

```text
Pt = D Phi_t(x0) P0 D Phi_t(x0)^T
```

Output includes the mean final positions, position standard deviations, the propagated state covariance, the position covariance block, per-body covariance matrices, the state-transition matrix, and diagnostics such as transition condition number and spectral radius.

The `position_confidence_regions` block converts each body's covariance into 50%, 90%, 95%, and 99% Gaussian ellipses or ellipsoids. Each region includes the center, Mahalanobis radius, semi-axis lengths, and axis directions, so the probability statement can be plotted or checked without recomputing the eigensystem.

The `linearized_diagnostics` block also reports singular-value sensitivity: maximum/minimum singular values of `D Phi_t`, the uncertainty amplification factor, and the finite-time Lyapunov exponent `log(sigma_max) / |t|`. These are local predictability diagnostics, not global chaos proofs.

This mode is the most mathematical local answer: it gives the first-order probability distribution implied by the Newtonian flow. If no explicit `initial_state_covariance` is supplied, `preserve_center_of_mass=True` constructs `P0` on the subspace where mass-weighted center-of-mass position and velocity are unchanged. It is valid while the initial uncertainty is small enough that nonlinear curvature of the flow is not dominant.

## Position Hypothesis Score

To judge whether a proposed target-time position is plausible under the local mathematical forecast, include `candidate_positions` in the input JSON and run:

```powershell
threebody predict --input initial-state.json --score-positions --preserve-center-of-mass --position-scale 1e-6 --velocity-scale 1e-6 --output position-score.json
```

This computes the same linearized Gaussian forecast, then scores the proposed three-body position with per-body and joint Mahalanobis distances, Gaussian log density, and 50/90/95/99% confidence membership. This is the direct mathematical answer to "does this claimed position at time `t` fit the predicted probability distribution?"

## Linearized Gaussian Ephemeris

For a time-resolved first-order probability distribution, use `threebody_engine.predict_three_body_linearized_ephemeris(...)` or:

```powershell
threebody predict --input initial-state.json --linearized-ephemeris --preserve-center-of-mass --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output linearized-ephemeris.json
```

This is the theoretical probability ephemeris. At every sampled time it returns the nominal mean positions, mean velocities, position standard deviations, and the flattened position covariance implied by

```text
P(t_k) = D Phi_{t_k}(x0) P0 D Phi_{t_k}(x0)^T
```

Use this when the initial uncertainty is small and a local Gaussian approximation is the appropriate mathematical object. Compare it with the empirical distribution ephemeris when nonlinear curvature may matter.

Like the deterministic ephemeris, this mode honors `target_times` in the input JSON, so an observation schedule can request nonuniform probability distributions at exact times.

Each row includes `linearized_sensitivity`, so sensitivity growth can be inspected over time instead of only at the final target time.

## Forecast Horizon

Use `threebody_engine.predict_three_body_forecast_horizon(...)` or:

```powershell
threebody predict --input initial-state.json --horizon --position-tolerance 1e-3 --position-scale 1e-6 --velocity-scale 1e-6 --output horizon.json
```

This mode answers the operational question that a point forecast alone cannot answer:

```text
For the declared initial uncertainty, until what time is the propagated position uncertainty still below my tolerance?
```

The engine samples the variational flow between `0` and `target_time`, propagates the initial covariance at each sample, and records `max_position_std / position_tolerance`. The forecast is `target_time_resolved=true` only when the final sampled uncertainty ratio is at most one. This does not prove global predictability; it gives a local, reproducible numerical certificate for a specific initial state, uncertainty scale, tolerance, and horizon.

Use `--preserve-center-of-mass` with standalone linearized or horizon CLI modes when the uncertainty should match the ensemble default. Use `--independent-body-uncertainty` in report or solution mode only when independent body-wise observational errors are the intended model.

## Ensemble Distribution Forecast

When the initial condition is uncertain, use `threebody_engine.predict_three_body_position_distribution(...)` or:

```powershell
threebody predict --input initial-state.json --distribution --count 128 --position-scale 1e-6 --velocity-scale 1e-6 --output distribution.json
```

The distribution mode samples a Gaussian perturbation ensemble around the initial state, optionally preserving center-of-mass position and velocity, integrates each member, and summarizes the final position distribution. If `initial_state_covariance` is supplied, the ensemble is drawn from that covariance directly; otherwise the engine builds the covariance from `position_scale`, `velocity_scale`, and the center-of-mass option.

Output includes:

- deterministic base prediction
- successful and failed ensemble counts
- mean final positions
- median final positions
- 5% and 95% coordinate quantiles
- covariance of the flattened final position vector
- per-body position covariance matrices
- per-body 50/90/95/99% covariance confidence regions

## Ensemble Distribution Ephemeris

For a probability distribution over the whole forecast interval, use `threebody_engine.predict_three_body_distribution_ephemeris(...)` or:

```powershell
threebody predict --input initial-state.json --distribution-ephemeris --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output distribution-ephemeris.json
```

This integrates the same Gaussian perturbation ensemble as the final-time distribution mode, but keeps every sampled time. The output contains the shared time grid, deterministic base ephemeris, and a `position_distribution_ephemeris` block with time-indexed mean positions, median positions, 5%/95% coordinate quantiles, flattened position covariance matrices, covariance confidence regions, and maximum body radius from the ensemble mean.

When `target_times` is supplied, every ensemble member is evaluated on that same nonuniform requested time grid.

The distribution ephemeris additionally reports `ensemble_close_approach_diagnostics`, aggregating close-approach risk across successful ensemble members.

This mode answers the strongest operational uncertainty question:

```text
At each sampled time between now and t, what is the probability distribution of the three positions?
```

## Scientific Interpretation

The deterministic API answers "where are the bodies at time `t` if the initial state is exactly known?"

The solution bundle answers "what are the target-time positions, how do they evolve, what is the probability distribution, and which claim is defensible?"

The solution summary answers "can we publish this as a point-position claim, a distributional claim, a deterministic-only calculation, or an unresolved forecast?"

The mathematical statement answers "which initial-value problem was solved, which flow-map readout defines `r_i(t)`, and which probability push-forward defines the returned distribution?"

The ephemeris API answers "where are the bodies at each sampled time between now and `t`?"

The forecast-horizon API answers "up to what time is that claim still tolerance-resolved under declared initial uncertainty?"

The interpretation report answers "which of the available mathematical forecasts is justified by diagnostics?"

The distribution API answers "where are the bodies likely to be at time `t` if the initial state has a specified observational uncertainty?"

The linearized-ephemeris API answers "what Gaussian distribution does the variational flow imply at every sampled time?"

The position-score API answers "how plausible is this proposed target-time position under the forecast distribution?"

The distribution-ephemeris API answers "how does that final probability distribution develop over the whole interval?"

The solution bundle's ephemeris comparison answers "until when does the theoretical linearized Gaussian stay consistent with the sampled empirical distribution?"

The atlas and symbolic-dynamics work remain necessary because long-time chaotic forecasts can become distributional even when the equations are deterministic. The prediction layer gives the concrete flow samples; the research layer explains when those samples support point forecasts, regime-local claims, or only probabilistic claims.
