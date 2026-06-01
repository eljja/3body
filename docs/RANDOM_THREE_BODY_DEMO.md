# Random Three-Body Prediction Demo

The project now includes a reproducible random-case demonstration for the
original operational target:

```text
given reproducible admissible random masses, positions, velocities, and target time t,
estimate the three target positions r_i(t)
```

**Paper status.** This is a demonstration harness for finite-time prediction on
seeded non-collisional cases. It is not evidence that all random three-body
inputs are globally predictable, and it is not a closed-form theorem.

**논문용 상태.** 이 문서는 seed가 고정된 비충돌 사례에 대한 유한시간 예측
데모이다. 모든 랜덤 삼체 입력이 전역적으로 예측 가능하다는 증거가 아니며,
닫힌형 정리도 아니다.

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

This is the practical engine demonstration path. It does not solve the general
three-body problem by a new closed formula; it shows that the system can
generate a seeded admissible test case, run multiple complementary forecast
layers, and audit whether the target-time coordinates are trustworthy under the
stated tolerances.

## Korean Summary

이 데모는 seed가 고정된 비충돌 삼체 초기조건을 만들고, 목표 시각 `t`의
좌표를 여러 방식으로 계산한 뒤 고정밀 reference integration과 비교한다.
성공은 `success_tolerance`, 상대 에너지 drift, close-approach gate를 모두
통과할 때만 승격된다. 이것은 유한시간 예측 데모이며, 일반 삼체 문제의
전역 닫힌형 해를 주장하지 않는다.
