# Solution Space

The project should not collapse into one proposed mechanism too early.
The current flyby work is only one chart family: a tight binary perturbed by an outer body.
Below are the major solution directions that can still matter for a regime-specific three-body theory.

## What The Current Two Axes Can Miss

The current strongest axes are accumulated tidal impulse and inner-binary exchange.
They can miss at least four mechanisms:

- Phase dependence: identical encounter strength can produce different outcomes depending on the binary phase at closest approach.
- Resonant exposure: slow encounters can repeatedly sample the inner orbit rather than acting as a single kick.
- Manifold routing: escape and temporary capture can be governed by stable/unstable manifolds rather than a local threshold.
- Collision geometry: close approaches can require regularized coordinates because ordinary Euclidean features become singular or misleading.

## Candidate Solution Families

- Phase-resolved scattering map: fit transition and exchange laws conditioned on binary phase, encounter duration, and tidal impulse.
- Manifold atlas: identify chart transitions as motion between hierarchy, resonant, collision, and escape manifolds.
- Shape-sphere dynamics: remove translation, rotation, and scale where possible, then analyze the remaining triangle-shape flow.
- Regularized collision charts: use Levi-Civita, Kustaanheimo-Stiefel style ideas, or local blow-up coordinates near binary collisions.
- Normal-form neighborhoods: near Lagrange points, periodic orbits, and weakly perturbed binaries, derive local analytic approximations.
- Scattering and return maps: treat flybys as maps from incoming orbital elements to outgoing orbital elements, then compose maps.
- Symbolic dynamics: encode regime changes as grammar over chart labels and test whether transition words have stable probabilities.
- Variational stability: use tangent dynamics, finite-time Lyapunov exponents, and monodromy/Floquet data where periodic orbits exist.
- Invariant-preserving surrogates: learn only residual corrections that preserve energy, momentum, angular momentum, or Jacobi structure.

## Operational Prediction Layer

The original practical target is now exposed as a small prediction API family:

- `threebody_engine.solve_three_body_prediction_problem(...)` answers the full operational version in one call: final positions, deterministic ephemeris, linearized Gaussian ephemeris, time-resolved empirical distribution, Gaussian-vs-empirical ephemeris comparison, forecast-horizon diagnostics, recommended interpretation mode, a report-ready `prediction_summary`, and a machine-readable `mathematical_statement`. The summary promotes the result as `target-position-and-distribution`, `distributional-target-position`, `deterministic-target-position`, or `unresolved-target-position`; the mathematical statement records the Newtonian equations, flow-map readout, probability push-forward, covariance formula, and per-body target-time claim rows. Its default uncertainty model preserves center-of-mass position and velocity in both the empirical ensemble and linearized covariance; if `initial_state_covariance` is supplied, that full covariance is shared by the empirical, linearized, horizon, and report paths.
- `threebody_engine.solve_three_body_target_positions(...)` answers the same target in the compact form most callers want first: target-time positions, target-time distribution, a table-ready per-body coordinate/probability summary, center-of-mass-frame coordinates, pairwise target geometry, relative uncertainty strength, recommended readout, deterministic flow definition, probability push-forward definition, and core reliability diagnostics without the full ephemeris bundle.
- `threebody_engine.predict_three_body_positions(...)` answers: given three masses, initial positions, initial velocities, and a target time, where are the three bodies? It integrates the Newtonian equations directly and returns final positions, velocities, solver metadata, energy/momentum/angular-momentum drift diagnostics, and minimum pair-distance close-approach diagnostics.
- `threebody_engine.predict_three_body_ephemeris(...)` answers the orbit-table version: what are the sampled positions and velocities for all three bodies from `0` through the target time? It can use either an evenly spaced sample count or an explicit nonuniform `target_times` observation grid, and it reports whether the sampled path enters a close-approach regime where regularization should be considered.
- `threebody_engine.predict_three_body_interpretation_report(...)` answers the decision version: run the deterministic, variational Gaussian, and empirical ensemble forecasts together, compare the final-position distributions, and recommend which mathematical claim is defensible.
- `threebody_engine.predict_three_body_forecast_horizon(...)` answers the tolerance version: given initial uncertainty and a position error tolerance, until what sampled time does the variationally propagated uncertainty remain below tolerance?
- `threebody_engine.predict_three_body_linearized_distribution(...)` answers the local mathematical version: given an initial covariance, or position/velocity uncertainty scales, what Gaussian final-position distribution is implied by the variational flow map `P(t) = D Phi_t P(0) D Phi_t^T`? If `preserve_center_of_mass=True`, the generated covariance lives on the center-of-mass-preserving subspace. The output also gives per-body covariance confidence ellipses/ellipsoids and singular-value finite-time sensitivity diagnostics for direct position-region and predictability claims.
- `threebody_engine.score_three_body_position_hypothesis(...)` answers the hypothesis-test version: given a proposed set of three target-time positions, how plausible is that position under the linearized Gaussian forecast? It reports per-body and joint Mahalanobis distance, log density, and confidence-level membership.
- `threebody_engine.predict_three_body_linearized_ephemeris(...)` answers the time-resolved local mathematical version: what Gaussian position distribution and local uncertainty amplification are implied by the variational flow at every sampled or explicitly requested time?
- `threebody_engine.predict_three_body_position_distribution(...)` answers the uncertainty version: if the initial condition is known through either position/velocity perturbation scales or a full initial state covariance, what empirical distribution of final positions should be expected? It returns mean positions, 5/50/95 percentiles, flat covariance over the full position vector, per-body covariance matrices, and per-body confidence regions.
- `threebody_engine.predict_three_body_distribution_ephemeris(...)` answers the time-resolved uncertainty version: how does the empirical distribution of the three positions evolve at every sampled or explicitly requested time from `0` through the target time?

This is deliberately not advertised as a global closed-form solution for the generic three-body problem. The mathematical statement is narrower and defensible: the engine computes a reproducible flow map sample, and when initial data are uncertain it pushes that uncertainty through the same flow to estimate the final-position distribution. The atlas, symbolic dynamics, and theorem-candidate work then describe where such forecasts are stable, where they are regime-local, and where only probabilistic claims are scientifically honest.

## Near-Term Research Priority

The immediate priority is no longer the phase-resolved scalar scattering map.
The stricter held-out branch tests make the safer research pivot a symbolic dynamics model centered on hysteresis memory.
Scattering diagnostics remain useful as physical measurements, but they should not be promoted as the primary smooth predictor until they beat impulse, grammar, and negative-control competitors.
The required evidence is a held-out phase sweep:

```powershell
threebody flyby-sweep --heldout --phase-sweep --duration 8 --samples 600 --stride 20
```

If phase-conditioned models win, the compact model should be a local scattering map:

```text
boundary ~= F(tidal_impulse, exchange, encounter_adiabaticity, hierarchy_ratio, binary_phase_at_encounter)
```

If they fail, the project should pivot to manifold routing and regularized close-encounter coordinates for the same residual cases.

The current implementation measures `binary_phase_at_periapsis` from the trajectory rather than relying only on initial phase.
That is necessary but not sufficient.
A real scattering map must predict outgoing energy, angular momentum, deflection angle, and chart transition probability jointly, not just reuse phase as another multiplicative power-law feature.

For the hysteresis branch, the compact model should instead be a Markov model over return-map chart words.
The public API entry point is `threebody_engine.build_hysteresis_markov_chain`, which builds a first-order symbolic transition matrix, stationary distribution, absorbing-state report, and entropy rate from atlas return words.
Use `threebody_engine.validate_hysteresis_markov_chain` for held-out symbolic validation; it reports transition coverage, unseen transitions, mean log likelihood, perplexity, and deterministic next-symbol accuracy.
Use `threebody_engine.compare_hysteresis_markov_to_baseline` before promoting a grammar claim; it requires the state-conditioned transition model to beat an independent next-symbol frequency baseline, not merely fit its own training words.
Use `threebody_engine.run_verification_report` for an end-to-end API artifact that bundles Picard tuning, Jacobi escape certification, hysteresis Markov baseline comparison, and promotion gates into one JSON-ready dictionary.
The first smoke result is encouraging only for low-crossing boundary collapse; high-crossing selection still prefers a simpler impulse model after complexity penalty.

Current atlas additions:

- Close/triple collision: `mcgehee_collision_diagnostic` separates hyperradius, radial velocity, normalized shape area, anisotropy, and collision depth.
- Escape/flyby scattering: `periapsis_scattering_map` now reports outgoing semimajor axis, eccentricity, periapsis distance, and escape speed at infinity.
- Lagrange gateway: `gateway_transit_estimate` tests whether the local neck is open and projects the state onto stable/unstable eigendirections around the nearest collinear point.
