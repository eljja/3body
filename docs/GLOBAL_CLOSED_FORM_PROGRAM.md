# Global Closed-Form Program

The project should not claim a finite elementary-function formula for the
generic Newtonian three-body problem. The defensible global direction is a
regularized, globally convergent series representation in the spirit of
Sundman's theorem.

This distinction matters:

- practical answer: compute `r_i(t)` and `Law(X_t)` with the existing prediction
  API and diagnostics;
- analytic route: represent the flow in a regularized time variable as a
  convergent series;
- non-claim: a compact elementary expression that solves every generic
  three-body initial state.

## Implemented Contract

The public API now exposes:

```python
from threebody_engine import (
    assess_three_body_global_closed_form_claim,
    global_closed_form_solution_contract,
)
```

`global_closed_form_solution_contract()` returns the research contract:

```text
x(tau) = sum_{k >= 0} a_k tau^k
r_i(t) = Pi_{r_i} Phi_t(x(0))
```

The contract promotes only a `sundman-style-regularized-convergent-series`
route. It explicitly does not promote a
`finite-elementary-function-global-formula`.

`assess_three_body_global_closed_form_claim(...)` checks a supplied initial
state against the currently implemented admissibility gates:

- three finite positive masses;
- finite 2D or 3D positions and velocities;
- no initial binary collision;
- nonzero angular momentum, used as the current gate for the promoted
  Sundman-style branch;
- no promotion of triple-collision branches until regularized collision charts
  exist in the engine.

The returned certificate includes pair-distance diagnostics, angular momentum,
center-of-mass diagnostics, readiness checks, and the remaining proof work.

CLI usage:

```powershell
threebody closed-form --input initial-state.json --output closed-form.json
```

## What Remains

The project still needs real proof machinery before it can claim an effective
global series solver:

- coefficient recurrences in regularized coordinates;
- binary-collision and triple-collision chart transitions;
- interval truncation bounds for finite partial sums;
- inverse time-map recovery bounds;
- comparison against the existing adaptive-flow API on benchmark intervals.

Until those are implemented, the closed-form route is a precise research
contract and admissibility certificate, not a completed global formula.
