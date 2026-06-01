# Paper-Readiness Review / 논문 제출 준비성 검토

This document is the repository-wide claim standard for the current
documentation set. It is bilingual by design: English text is intended for
paper-facing readers, and Korean text records the same decisions for project
continuity.

본 문서는 현재 저장소 문서 전체에 적용되는 주장 강도 기준입니다. 영어
문장은 논문/외부 리뷰 독자를 기준으로 하고, 한국어 문장은 동일한 판단을
프로젝트 관리 맥락에서 보존합니다.

## Claim Taxonomy / 주장 단계

| Level | English standard | 한국어 기준 |
| --- | --- | --- |
| Operational numerical result | A reproducible finite-time computation with stated solver tolerances, invariant drift, and close-approach diagnostics. | 허용오차, 보존량 drift, 근접조우 진단이 함께 제시된 유한시간 수치 결과입니다. |
| Reproducibility certificate | A machine-readable audit record: hashes, inputs, gates, and verification receipts. It is not automatically a mathematical proof. | 입력, 해시, gate, 검증 receipt를 기록한 기계판독 감사 자료입니다. 이것만으로 수학적 증명은 아닙니다. |
| Theorem candidate | A precise conditional statement with implemented checks and unresolved proof obligations. | 구현된 검사와 남은 증명 의무가 함께 있는 조건부 정리 후보입니다. |
| Computer-assisted proof claim | Allowed only after interval ODE propagation or an independently validated backend encloses the relevant flow and parameter region. | 관련 흐름과 매개변수 영역이 구간 ODE 또는 독립 검증 백엔드로 포획된 뒤에만 허용됩니다. |
| Forbidden global claim | No document may claim a finite elementary closed-form solution of the generic Newtonian three-body problem. | 어떤 문서도 일반 뉴턴 삼체 문제의 유한 초등함수 전역해를 주장할 수 없습니다. |

## Logical Consistency Rules / 논리 일관성 규칙

Every document in this repository must satisfy the following rules before being
used in a paper submission:

- "arbitrary", "general", or "random" initial data must be qualified by finite
  data, non-collision/admissibility, target-time horizon, and diagnostic gates;
- exact Newtonian statements must not silently use softened or regularized
  numerical equations;
- a certificate is an audit artifact unless the same paragraph states the
  validated-flow proof backend and enclosed parameter region;
- a public GitHub Pages artifact is visual evidence plus a machine-readable
  receipt, not a live solver and not an independent proof;
- theorem-candidate language must include open proof obligations.

논문 제출에 사용되는 저장소 문서는 모두 다음 규칙을 만족해야 합니다.

- "임의", "일반", "랜덤" 초기조건은 유한 데이터, 비충돌/admissibility,
  목표시간 horizon, diagnostic gate와 함께 제한해서 써야 합니다.
- 정확한 Newtonian 명제는 softened/regularized 수치 방정식을 암묵적으로
  사용하면 안 됩니다.
- 같은 문단에서 validated-flow proof backend와 포획된 parameter region을
  명시하지 않으면 certificate는 감사 산출물입니다.
- 공개 GitHub Pages 산출물은 시각 증거와 기계판독 receipt이지 live solver나
  독립 증명이 아닙니다.
- theorem-candidate 문장은 남은 proof obligation을 포함해야 합니다.

## Repository-Wide Conclusions / 전체 결론

1. The project has a defensible operational solver layer for finite-time
   target positions and pushed-forward probability distributions.
2. The project has reproducible theorem-candidate and static-site audit
   artifacts, but these artifacts are not yet a complete proof of a general
   three-body theorem.
3. The strongest mathematical direction remains a local, conditional Jacobi
   escape-cone certificate plus an atlas/symbolic-dynamics program.
4. The global closed-form route must remain scoped to a Sundman-style
   regularized convergent-series research contract, not an elementary formula.

1. 본 프로젝트는 특정 초기조건과 특정 시간에 대한 위치 및 확률분포를
   재현 가능하게 계산하는 운영 계층을 갖추었습니다.
2. 정리 후보와 정적 사이트 감사 산출물은 재현 가능하지만, 그 자체가 일반
   삼체 문제의 완전한 증명은 아닙니다.
3. 가장 강한 수학적 방향은 조건부 Jacobi escape-cone certificate와
   atlas/symbolic-dynamics 프로그램입니다.
4. 전역 닫힌형 경로는 Sundman식 정규화 수렴급수 연구 계약으로만 유지해야
   하며, 초등함수 전역 공식으로 표현하면 안 됩니다.

## Document Audit Table / 문서별 감사표

| Document | Paper-facing status | Required interpretation |
| --- | --- | --- |
| `README.md` | usable after claim-standard link and admissibility wording | Entry point; do not cite as a proof document. |
| `docs/PROJECT_SCOPE.md` | consistent | Defines boundaries and non-claims. |
| `docs/SCIENCE_FOUNDATION.md` | consistent | Background only; no novelty claim. |
| `docs/ARCHITECTURE.md` | consistent | Software architecture and verification flow. |
| `docs/DEVELOPMENT.md` | consistent | Developer procedure, not scientific evidence. |
| `docs/RESEARCH_PROGRAM.md` | consistent | Research program and atlas thesis. |
| `docs/RESEARCH_RUNS.md` | consistent | Reproducibility commands; suite rows are not proofs. |
| `docs/CURRENT_HYPOTHESES.md` | scoped | Falsifiable hypotheses; not final laws. |
| `docs/THEOREM_CANDIDATES.md` | scoped | Theorem candidates with open obligations. |
| `docs/JACOBI_ESCAPE_CONE_THEOREM.md` | scoped | Conditional theorem note; still needs validated ODE backend. |
| `docs/INTERPRETATION_METHOD.md` | scoped | Local interpretation certificates, not global theory. |
| `docs/PREDICTION_METHOD.md` | consistent after Newtonian/softening distinction | Operational finite-time prediction method for admissible finite data. |
| `docs/RANDOM_THREE_BODY_DEMO.md` | consistent after seeded-admissible wording | Demonstration harness, not a proof of global solvability. |
| `docs/GLOBAL_CLOSED_FORM_PROGRAM.md` | consistent | Sundman-style contract; explicitly not an elementary formula. |
| `docs/LITERATURE_COMPARISON.md` | consistent | Overclaim-prevention comparison. |
| `docs/SOLUTION_SPACE.md` | consistent after finite-admissible API wording | Alternative research directions and operational APIs. |
| `docs/VALIDATION_GUARDRAILS.md` | authoritative | Main anti-overclaim policy. |
| `docs/STRATEGIC_REVIEW.md` | advisory | Strategy memo; commercial/journal claims are conditional. |
| `docs/LOCAL_CHANGES_AUDIT.md` | historical | Change log; superseded entries require current follow-up context. |
| `docs/GITHUB_PAGES.md` | consistent | Public evidence-bundle generation and verifier use. |
| `docs/ROADMAP.md` | planning | Milestones; not evidence by itself. |

## Citation Guidance / 인용 지침

For a paper or external technical report, cite only claims that include:

- the exact command or API entry point;
- solver tolerances and sample counts where relevant;
- invariant drift or diagnostic gates;
- the commit SHA or artifact receipt;
- the specific regime or initial-condition family;
- open proof obligations when the result is theorem-shaped.

논문이나 외부 기술 보고서에는 다음 요소가 있는 주장만 인용해야 합니다.

- 정확한 명령 또는 API entry point;
- 필요한 경우 solver tolerance와 sample count;
- 보존량 drift 또는 diagnostic gate;
- commit SHA 또는 artifact receipt;
- 특정 regime 또는 초기조건 family;
- 정리 후보일 경우 남은 proof obligation.

## Rejected Phrasing / 금지 표현

Avoid these unless the missing proof obligations are actually completed:

- "the general three-body problem is solved";
- "global closed-form solution";
- "certificate proves the theorem" without a validated-flow proof;
- "universal transition law" across all masses, energies, and angular momenta;
- journal-ranking claims as evidence of correctness.

다음 표현은 필요한 증명 의무가 실제로 완료되기 전까지 금지합니다.

- "일반 삼체 문제가 해결되었다";
- "전역 닫힌형 해를 얻었다";
- 검증된 흐름 포획 없이 "certificate가 정리를 증명한다";
- 모든 질량, 에너지, 각운동량에 대한 "보편 전이 법칙";
- 저널 등급 자체를 올바름의 근거로 삼는 표현.
