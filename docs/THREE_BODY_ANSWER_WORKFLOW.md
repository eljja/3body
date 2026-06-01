# Direct Three-Body Answer Workflow

This is the shortest reproducible workflow for the original project question:
given three masses, initial positions, initial velocities, and a finite target
time, report target coordinates `r_i(t)` when defensible or the target
probability law `Law(X_t)` when uncertainty dominates.

## Run

```powershell
threebody predict --input examples/figure_eight_answer_input.json --answer --count 64 --samples 128 --horizon-samples 16 --position-scale 1e-7 --velocity-scale 1e-7 --output answer.json
threebody validate-answer --input answer.json --output answer-validation.json
```

The first command creates a `three-body-problem-answer` JSON object. The second
command recomputes the direct-answer consistency checks and validates the
embedded target prediction certificate.

## Read First

Start with these fields:

- `answer_summary`: Korean/English human-readable conclusion.
- `answer_kind`: whether to read point positions, a probability distribution,
  deterministic-only positions, or unresolved.
- `body_answer_table`: one row per body, including deterministic coordinates,
  probability mean, central 90% interval, 95% region, and numerical convergence
  delta.
- `position_answer`: direct `r_i(t) = Pi_{r_i} Phi_t(x0)` answer.
- `distribution_answer`: direct `mu_t = (Phi_t)_# mu_0` answer.
- `input_admissibility`: whether the initial-value problem is admissible.
- `numerical_convergence_certificate`: stricter reintegration check for point
  coordinates.
- `answer_consistency_certificate`: internal consistency check for the answer.

## Korean Summary

이 워크플로는 “주어진 삼체가 시간 `t` 이후 어디에 있는가?”라는 질문에 대한
가장 짧은 재현 절차다. 입력이 유한한 양의 질량, 유한 위치/속도, 비충돌
초기조건 gate를 통과하면 `answer_summary`와 `body_answer_table`에서 바로
좌표와 확률 영역을 읽는다. 혼돈 또는 초기 불확실성이 커져 점 좌표 주장이
부적절하면 `distribution_answer`의 `Law(X_t)`를 읽는다. 입력 자체가
허용되지 않으면 `answer_status`는 `unresolved`가 되고, 이유는
`input_admissibility.blocking_reasons_ko`에 기록된다.

## Scientific Limit

This is a finite-time, diagnostic-gated answer. It does not claim a finite
elementary global closed form for the generic three-body problem. The
mathematical object is the Newtonian flow map `Phi_t` and, for uncertain initial
states, the push-forward law `(Phi_t)_# mu_0`.
