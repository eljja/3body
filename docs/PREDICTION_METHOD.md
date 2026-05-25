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

Output includes final positions, final velocities, solver metadata, and a Noether invariant drift certificate for energy, linear momentum, and angular momentum.

## Interpretation Report

Use `threebody_engine.predict_three_body_interpretation_report(...)` or:

```powershell
threebody predict --input initial-state.json --report --count 128 --position-scale 1e-6 --velocity-scale 1e-6 --output report.json
```

The report runs all three prediction layers:

- deterministic flow-map evaluation
- linearized Gaussian covariance push-forward
- empirical ensemble push-forward

It then compares the linearized and empirical final-position distributions. The comparison records the mean-position gap, covariance Frobenius gap, covariance relative gap, and mean gap in sigma units. The verdict recommends one of:

- `linearized-gaussian`: the variational distribution agrees with the ensemble within the configured gates.
- `empirical-ensemble`: the ensemble is resolved, but nonlinear effects are large enough that linearization should not be promoted.
- `deterministic-only`: only the nominal trajectory is resolved.
- `unresolved`: the nominal or uncertainty propagation failed the diagnostics.

This is the default scientific handoff format because it answers not only "where are the bodies?" but also "which mathematical claim is defensible for this initial condition and forecast horizon?"

## Linearized Gaussian Forecast

For small observational uncertainty, use `threebody_engine.predict_three_body_linearized_distribution(...)` or:

```powershell
threebody predict --input initial-state.json --linearized-distribution --position-scale 1e-6 --velocity-scale 1e-6 --output linearized.json
```

This integrates the variational equation along the nominal trajectory. If `Phi_t` is the flow map and `P0` is the initial covariance, the returned covariance is

```text
Pt = D Phi_t(x0) P0 D Phi_t(x0)^T
```

Output includes the mean final positions, position standard deviations, the propagated state covariance, the position covariance block, per-body covariance matrices, the state-transition matrix, and diagnostics such as transition condition number and spectral radius.

This mode is the most mathematical local answer: it gives the first-order probability distribution implied by the Newtonian flow. It is valid while the initial uncertainty is small enough that nonlinear curvature of the flow is not dominant.

## Ensemble Distribution Forecast

When the initial condition is uncertain, use `threebody_engine.predict_three_body_position_distribution(...)` or:

```powershell
threebody predict --input initial-state.json --distribution --count 128 --position-scale 1e-6 --velocity-scale 1e-6 --output distribution.json
```

The distribution mode samples a Gaussian perturbation ensemble around the initial state, optionally preserving center-of-mass position and velocity, integrates each member, and summarizes the final position distribution.

Output includes:

- deterministic base prediction
- successful and failed ensemble counts
- mean final positions
- median final positions
- 5% and 95% coordinate quantiles
- covariance of the flattened final position vector
- per-body position covariance matrices

## Scientific Interpretation

The deterministic API answers "where are the bodies at time `t` if the initial state is exactly known?"

The interpretation report answers "which of the available mathematical forecasts is justified by diagnostics?"

The distribution API answers "where are the bodies likely to be at time `t` if the initial state has a specified observational uncertainty?"

The atlas and symbolic-dynamics work remain necessary because long-time chaotic forecasts can become distributional even when the equations are deterministic. The prediction layer gives the concrete flow samples; the research layer explains when those samples support point forecasts, regime-local claims, or only probabilistic claims.
