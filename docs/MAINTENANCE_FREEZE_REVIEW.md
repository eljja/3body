# Maintenance Freeze Review

이 문서는 한동안 적극 개발을 멈추고 유지보수 모드로 들어가기 위한 마지막
점검 기록이다. 결론부터 말하면, 현재 구성은 "삼체 문제의 전역 닫힌해"가
아니라 "유한시간 삼체 위치/분포 해석 엔진"으로는 충분하다.

## 결론

현재 엔진은 다음 목표에 충분하다.

- 유한 양질량, 유한 위치/속도, 비충돌 초기조건, 유한 목표시간 `t`가 주어졌을
  때 `r_i(t)`를 계산한다.
- 점 좌표 주장이 불안정하거나 초기 불확실성이 선언되면
  `Law(X_t) = (Phi_t)_# Law(X_0)` 형태의 목표시간 분포를 반환한다.
- 입력이 부적절하거나 근접충돌/수렴/예측 horizon gate가 실패하면
  `unresolved` 또는 제한된 답변으로 낮춘다.
- JSON certificate와 validator로 저장된 답변과 공개 Pages 산출물을 다시 감사할
  수 있다.

현재 엔진은 다음 목표에는 충분하지 않다.

- 일반 뉴턴 삼체 문제의 유한 초등함수 전역 닫힌해.
- 임의의 충돌 통과를 포함하는 완전 regularized 전역 flow.
- 혼돈 horizon을 넘어선 무조건 장기 점 예측.
- 독립 검증기관 수준의 mission-critical 항공우주 보증.

## 마지막으로 고정된 핵심 구성

- `answer_three_body_problem(...)`
  - 원래 질문에 대한 직접 답변 계층.
  - 위치 답변, 분포 답변, 입력 허용성, 수렴 인증, defect bound, validated
    interval flow enclosure, publishability flag를 한 객체에 묶는다.
- `validate_three_body_problem_answer(...)`
  - 저장된 direct-answer JSON을 재검증한다.
- `solve_three_body_target_positions(...)`
  - 외부 사용자가 가장 먼저 읽기 좋은 compact target-time answer.
- `predict_three_body_a_posteriori_defect_bound(...)`
  - 연속 defect와 Gronwall류 전파 오차 경계를 제공한다.
- `predict_three_body_validated_flow_enclosure(...)`
  - interval box, Picard self-inclusion, Lipschitz contraction 기반의 validated
    flow enclosure certificate를 제공한다.
- `solve_random_three_body_prediction_demo(...)`
  - 임의 비충돌 seed 사례를 기준 적분과 비교하는 smoke demo.
- `verify_public_static_artifacts_from_url(...)`
  - 공개 GitHub Pages evidence bundle을 URL에서 직접 감사한다.
- `three_body_maintenance_readiness_report(...)`
  - 이 문서의 유지보수 결론을 기계 판독 가능한 JSON으로 반환한다.

## 유지보수 모드에서 돌릴 명령

```powershell
threebody maintenance-readiness --output maintenance-readiness.json
threebody predict --input examples/figure_eight_answer_input.json --answer --count 64 --samples 128 --horizon-samples 16 --position-scale 1e-7 --velocity-scale 1e-7 --output answer.json
threebody validate-answer --input answer.json --output answer-validation.json
threebody random-demo --seed 7 --target-time 0.05 --count 16 --samples 64 --reference-samples 128 --output random-demo.json
threebody verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-public-claim --output pages-verification-receipt.json
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest tests\test_engine_api.py tests\test_cli.py tests\test_static_site.py -q
```

## 유지보수 정책

허용되는 변경:

- schema 호환성을 유지하는 버그 수정.
- claim boundary를 더 명확히 하는 문서 수정.
- 테스트 강화와 artifact verifier 유지보수.
- 과학적 주장을 바꾸지 않는 dependency/workflow 보수.

피해야 할 변경:

- 논문 준비성 검토 없이 새 theorem claim을 추가하는 것.
- schema version을 올리지 않고 안정 JSON field를 바꾸는 것.
- ThreeBody 공개 페이지에 관련 없는 수학 workbench를 다시 추가하는 것.
- 예제를 통과시키기 위해 diagnostic gate를 약화하는 것.

## 다음 연구자가 다시 시작할 때

다음 연구 단계는 새 UI나 새 claim보다 아래 순서가 낫다.

1. 독립 interval/Taylor-model ODE backend와 현재 validated flow enclosure 비교.
2. Levi-Civita 또는 KS류 근접충돌 regularized chart 구현.
3. Gaussian/empirical 요약을 넘어선 validated probability-law propagation.
4. Sundman식 수렴급수의 coefficient recurrence와 truncation certificate.
5. near-collision, hierarchical, exchange, scattering 사례를 포함한 benchmark atlas 확대.

## 한 줄 요약

유지보수 기준으로는 충분하다. 단, 이 프로젝트의 공개 주장은 계속
"유한시간 위치 또는 분포 해석"이어야 하며, "일반 삼체 문제의 전역 닫힌해
해결"로 바뀌면 안 된다.
