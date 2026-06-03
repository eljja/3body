# LLM Handoff: Three-Body Challenge

이 문서는 다른 LLM 또는 연구 에이전트가 이 저장소를 이어받아 삼체 문제
도전을 계속하기 위한 인수인계 문서다. 목표는 과장된 "완전 해결" 선언이
아니라, 현재까지 구축된 계산/검증 계층을 정확히 이해하고 다음 연구 단계를
논문 수준으로 강화하는 것이다.

## 현재 결론

일반 뉴턴 삼체 문제의 유한 초등함수 전역 닫힌해는 이 프로젝트에서 해결된
상태가 아니다. 따라서 다음 주장은 금지한다.

- "임의의 삼체 문제를 하나의 전역 닫힌 공식으로 풀었다."
- "혼돈/근접충돌/불확실성 gate와 무관하게 항상 점 좌표를 예측한다."
- "수치 적분 결과를 엄밀한 전역 정리로 대체한다."

현재 방어 가능한 주장은 다음이다.

- 유한 양의 질량, 유한 위치/속도, 비충돌 초기조건, 유한 목표시간 `t`가
  주어지면 뉴턴 초기값 문제의 flow map `Phi_t`를 계산적으로 평가한다.
- 진단 gate가 통과되면 각 물체의 위치를
  `r_i(t) = Pi_{r_i} Phi_t(x0)`로 보고한다.
- 초기조건에 불확실성이 있거나 점 좌표 주장이 약하면 목표시간 확률법칙
  `mu_t = (Phi_t)_# mu_0`를 보고한다.
- 근접충돌, 과도한 민감도, 수렴 실패, 허용 불가능한 입력은 `unresolved`
  또는 제한된 분포 답변으로 낮춘다.

## 저장소에서 이미 구현된 것

핵심 공개 API는 `threebody_engine` 패키지에 있다.

- `answer_three_body_problem(...)`
  - 원래 질문에 대한 가장 직접적인 답변 객체를 만든다.
  - `answer_kind`는 점 위치+확률영역, 확률분포 답변, 결정론 좌표만, 미해결
    중 하나로 판정한다.
  - `body_answer_table`은 물체별 `r_i(t)`, 확률 평균, 중앙 90% 구간,
    95% 영역, 재적분 수렴 오차, 한국어/영어 해석문을 담는다.
  - `numerical_convergence_certificate`는 더 엄격한 DOP853 재적분으로
    목표 좌표 차이를 확인한다.
  - `answer_consistency_certificate`는 답변 종류, 본문 표, 분포 alias,
    수렴 인증, 출판 가능성 flag가 서로 모순되지 않는지 확인한다.
- `validate_three_body_problem_answer(...)`
  - 저장된 direct-answer JSON을 다시 검증한다.
  - 내부 consistency와 내장 target certificate를 재계산한다.
- `solve_three_body_target_positions(...)`
  - compact한 목표시간 위치/분포/기하/민감도/인증 결과를 만든다.
- `solve_random_three_body_prediction_demo(...)`
  - 재현 가능한 랜덤 삼체 입력을 생성하고 reference integration과 비교한다.
- `assess_three_body_global_closed_form_claim(...)`
  - Sundman식 정규화 수렴급수 route의 현재 계약과 미완성 항목을 분리해
    보고한다. 이것은 유한 초등함수 전역해 주장이 아니다.

관련 파일:

- `README.md`
- `docs/THREE_BODY_ANSWER_WORKFLOW.md`
- `docs/PREDICTION_METHOD.md`
- `docs/PAPER_READINESS_REVIEW.md`
- `docs/VALIDATION_GUARDRAILS.md`
- `docs/GLOBAL_CLOSED_FORM_PROGRAM.md`
- `src/threebody_engine/api.py`
- `tests/test_engine_api.py`
- `tests/test_cli.py`
- `examples/figure_eight_answer_input.json`

## 바로 실행할 재현 절차

개발 환경에서 패키지를 설치한다.

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pip install -e .[dev]
```

가장 짧은 direct-answer workflow:

```powershell
threebody predict --input examples/figure_eight_answer_input.json --answer --count 64 --samples 128 --horizon-samples 16 --position-scale 1e-7 --velocity-scale 1e-7 --output answer.json
threebody validate-answer --input answer.json --output answer-validation.json
```

테스트:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest tests\test_engine_api.py tests\test_cli.py -q
```

결과를 읽을 때는 먼저 다음 필드를 확인한다.

- `answer_summary`
- `answer_kind`
- `body_answer_table`
- `input_admissibility`
- `numerical_convergence_certificate`
- `answer_consistency_certificate`
- `publishability`

## 수학적 해석 계약

입력 상태는 다음 형태다.

```text
m_i > 0
r_i(0), v_i(0) in R^2 or R^3
min_{i != j} |r_i(0)-r_j(0)| > 0
target_time < infinity
```

뉴턴 방정식:

```text
d r_i / dt = v_i
d v_i / dt = G sum_{j != i} m_j (r_j - r_i) / |r_j - r_i|^3
```

결정론적 답변:

```text
x(t) = Phi_t(x0)
r_i(t) = Pi_{r_i} Phi_t(x0)
```

확률 답변:

```text
X_0 ~ mu_0
X_t = Phi_t(X_0)
mu_t = Law(X_t) = (Phi_t)_# mu_0
```

선형화된 공분산 근사:

```text
P_t ~= D Phi_t(x0) P_0 D Phi_t(x0)^T
```

이 계약은 "삼체 문제를 닫힌 공식으로 전역 해결"했다는 뜻이 아니다. 정확한
표현은 "허용 가능한 초기값과 유한 목표시간에 대해 flow map의 점/분포
판독을 검증된 절차로 계산한다"이다.

## 다음 LLM이 우선 연구해야 할 일

1. 엄밀 오차 경계
   - 현재 수렴 인증은 재적분 비교 중심이다.
   - 다음 단계는 interval arithmetic, Taylor model, a posteriori ODE
     defect bound를 붙여 좌표 오차 상계를 수학적으로 더 강하게 만드는 것이다.

2. 근접충돌 regularization
   - Levi-Civita, Kustaanheimo-Stiefel, McGehee류 좌표계를 검토한다.
   - near-collision 입력을 단순히 막는 것에서, regularized chart로 넘겨
     제한된 예측을 회복하는 방향이 필요하다.

3. 확률법칙 전파 강화
   - Monte Carlo와 선형화만으로는 chaotic tail을 충분히 설명하기 어렵다.
   - polynomial chaos, unscented transform, validated particle ensemble,
     rare-event splitting, Wasserstein/total-variation distance 진단을 비교한다.

4. Sundman식 전역 수렴급수 route
   - 계수 recurrence, 시간변환 역함수, truncation error, 충돌 chart 연결을
     구현해야 한다.
   - 이 route는 "유한 초등함수 공식"이 아니라 "정규화된 무한 수렴급수와
     계산 가능한 절단 오차"로 주장해야 한다.

5. benchmark atlas
   - figure-eight, hierarchical triple, restricted/L4, exchange, scattering,
     escape, near-collision seed를 고정한다.
   - 각 seed마다 point claim, distribution claim, unresolved decision의
     원인을 문서화한다.

6. 논문 수준 서술
   - 모든 theorem/corollary는 assumption, diagnostic gate, solver tolerance,
     exact Newtonian 여부, softening 여부, 실패 조건을 같이 써야 한다.
   - "AI가 삼체를 풀었다" 대신 "AI가 검증 가능한 계산-증명 workflow와
     실패 감지 체계를 확장했다"로 표현한다.

## 다음 LLM에게 줄 한글 프롬프트

아래 프롬프트를 그대로 붙여 넣어 사용할 수 있다.

```text
너는 D:\Code\ThreeBody 저장소를 이어받는 연구/코딩 LLM이다. 목표는 일반
뉴턴 삼체 문제에 대해 과장 없는 방식으로 다음을 개선하는 것이다.

1. 주어진 유한 양질량, 유한 위치/속도, 비충돌 초기조건, 유한 목표시간 t에
   대해 각 위치 r_i(t)를 방어 가능하게 계산한다.
2. 점 좌표 주장이 불안정하거나 초기조건에 불확실성이 있으면
   Law(X_t) = (Phi_t)_# Law(X_0) 형태의 확률분포 답변을 만든다.
3. 진단 gate가 실패하면 unresolved 또는 제한된 답변으로 낮춘다.

절대 "일반 삼체 문제의 유한 초등함수 전역 닫힌해를 완성했다"고 주장하지
마라. 이 저장소의 방어 가능한 claim은 finite-time, diagnostic-gated
Newtonian flow-map evaluation과 push-forward probability law다.

먼저 다음 파일을 읽어라.
- README.md
- docs/LLM_HANDOFF_THREE_BODY_CHALLENGE.md
- docs/THREE_BODY_ANSWER_WORKFLOW.md
- docs/PREDICTION_METHOD.md
- docs/PAPER_READINESS_REVIEW.md
- docs/VALIDATION_GUARDRAILS.md
- src/threebody_engine/api.py
- tests/test_engine_api.py
- tests/test_cli.py

그 다음 아래 중 하나를 실제로 개선하라.
- interval arithmetic 또는 a posteriori defect bound를 이용한 더 엄밀한
  target-position error certificate
- near-collision regularized chart
- probability-law propagation 개선
- Sundman식 수렴급수 route의 coefficient/truncation certificate
- benchmark atlas와 paper-ready theorem statement 정리

수정 후에는 테스트를 추가하거나 갱신하고 다음 명령을 실행하라.
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest tests\test_engine_api.py tests\test_cli.py -q

최종 보고에는 다음을 포함하라.
- 바꾼 파일
- 수학적 claim의 정확한 범위
- 실패하거나 unresolved로 남겨야 하는 조건
- 실행한 테스트와 결과
- 다음 연구자가 이어갈 가장 중요한 미완성 항목
```

## English Prompt For Another LLM

```text
You are taking over the D:\Code\ThreeBody repository as a research/coding LLM.
Your goal is to improve a defensible three-body prediction engine, not to make
an exaggerated closed-form claim.

The current defensible target is:
1. For finite positive masses, finite initial positions/velocities, no initial
   collision, and a finite target time t, compute body positions r_i(t) when the
   diagnostic gates permit a point-position claim.
2. When uncertainty or instability dominates, report the pushed-forward law
   Law(X_t) = (Phi_t)_# Law(X_0).
3. When admissibility, convergence, near-collision, or horizon gates fail,
   return unresolved or a limited distribution claim.

Do not claim that the generic Newtonian three-body problem has a finite
elementary global closed-form solution. The current claim is finite-time,
diagnostic-gated Newtonian flow-map evaluation plus probability push-forward.

Read these files first:
- README.md
- docs/LLM_HANDOFF_THREE_BODY_CHALLENGE.md
- docs/THREE_BODY_ANSWER_WORKFLOW.md
- docs/PREDICTION_METHOD.md
- docs/PAPER_READINESS_REVIEW.md
- docs/VALIDATION_GUARDRAILS.md
- src/threebody_engine/api.py
- tests/test_engine_api.py
- tests/test_cli.py

Then implement one concrete improvement:
- a rigorous target-position error certificate using interval arithmetic or
  a posteriori ODE defect bounds;
- a regularized near-collision chart;
- improved probability-law propagation;
- a Sundman-style convergent-series coefficient/truncation certificate;
- a benchmark atlas and paper-ready theorem statements.

After the change, add or update tests and run:
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest tests\test_engine_api.py tests\test_cli.py -q

Your final report must include:
- changed files;
- exact mathematical scope of the claim;
- conditions that still force unresolved output;
- tests run and results;
- the most important unfinished item for the next researcher.
```

## 인수인계 판정 기준

다음 조건을 만족하면 다음 LLM의 작업은 이 프로젝트에 실제로 기여한 것으로
볼 수 있다.

- 새로운 주장이 `PAPER_READINESS_REVIEW`와 `VALIDATION_GUARDRAILS`의
  기준을 넘는다.
- 실패 조건이 숨겨지지 않고 JSON certificate 또는 문서에 남는다.
- API 결과와 CLI 결과가 같은 의미를 가진다.
- 테스트가 최소한 happy path와 failure/unresolved path를 모두 다룬다.
- README 또는 관련 docs에 한국어/영어로 claim boundary가 업데이트된다.

## 짧은 요약

이 프로젝트는 "삼체 문제를 완전히 풀었다"가 아니라 "삼체 문제의 원래
실용 질문을 정직한 계산-검증 문제로 바꾸고, 가능한 경우 좌표를, 불안정한
경우 확률법칙을, 실패한 경우 미해결 판정을 반환하는 엔진"이다. 다음 연구는
좌표 자체보다 좌표 주장의 오차, 실패 조건, 확률분포, regularization을 더
엄밀하게 만드는 쪽으로 가야 한다.
