# Random Three-Body Prediction Demo

The project now includes a reproducible random-case demonstration for the
original operational target:

```text
given random masses, positions, velocities, and target time t,
estimate the three target positions r_i(t)
```

Run:

```powershell
threebody random-demo --seed 7 --target-time 0.05 --output random-demo.json
```

The demo generates a non-collisional random initial state, recenters it in the
mass-weighted center-of-mass frame, and compares several prediction readouts
against a stricter high-precision reference integration:

- direct adaptive-flow final state;
- final row of the deterministic ephemeris;
- compact target-solution deterministic readout;
- empirical ensemble mean of the pushed-forward uncertainty distribution.

The `success_report` promotes success only when:

- the direct point forecast agrees with the stricter reference within
  `success_tolerance`;
- relative energy drift stays below the configured invariant gate;
- close-approach diagnostics do not demand collision regularization.

This is the practical AI/engine demonstration path. It does not solve the
general three-body problem by a new closed formula; it shows that the system can
generate an arbitrary test case, run multiple complementary forecast layers, and
audit whether the target-time coordinates are trustworthy.
