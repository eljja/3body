# Global Closed-Form Program

The project should not claim a finite elementary-function formula for the
generic Newtonian three-body problem. The defensible global direction is a
regularized, globally convergent series representation in the spirit of
Sundman's theorem.

**Paper status.** This document is a research-contract statement. It may be
cited to explain why a Sundman-style route is being studied, but not as a claim
that the project has implemented an effective global series solver.

**논문용 상태.** 이 문서는 연구 계약을 정의한다. Sundman식 경로를 연구하는
이유를 설명하는 근거로는 인용할 수 있지만, 유효한 전역 급수 solver 구현이
완료되었다는 주장으로 인용하면 안 된다.

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

## Korean Summary

이 문서의 핵심은 "일반 삼체 문제의 전역 초등함수 해를 얻었다"는 주장을
금지하고, 방어 가능한 분석 경로를 Sundman식 정규화 수렴급수 연구 계약으로
제한하는 것이다. 현재 API는 입력 초기조건이 이 연구 계약의 일부 gate를
통과하는지 감사하지만, 계수 점화식, 충돌 chart, truncation bound, 시간 역변환
bound가 구현되기 전까지는 완성된 전역 급수 solver가 아니다.
