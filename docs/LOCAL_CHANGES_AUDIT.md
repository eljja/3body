# 로컬 변화에 대한 기술적/학술적 전략 감사 보고서 (Technical & Academic Strategic Audit)

본 보고서는 최근 로컬 저장소(`ThreeBody`)에서 대대적으로 이루어진 커밋 및 코드 변화들을 추적하고, 최초 프로젝트의 방향성과의 일치 여부, 상업적/학문적 가치 상승도에 대해 냉정하고 비판적인 시각으로 진단한 감사 문서입니다.
이 문서는 변경 이력을 보존하는 historical audit이며, 논문 제출용 현재 주장은
`docs/PAPER_READINESS_REVIEW.md`와 `docs/VALIDATION_GUARDRAILS.md`의 claim
taxonomy를 우선한다.

English note: this is a historical change audit. Superseded bottlenecks and
strategy assessments must be read together with the later "follow-up
implementation" section and the repository-wide paper-readiness standard.

---

## 1. 최근 로컬 변화 분석 (Commit & Run Audit)

최근 로컬 저장소에는 수학적 검증 후보와 물리학적 제약 조건을 감사하기 위한 고밀도 시스템이 커밋되었습니다.
*   **물리 보존 제약 강화:** 질량중심 환원(Center-of-mass reduction), Lagrange-Jacobi 항등식, Sundman 부등식, Noether 불변량 진단 도입.
*   **정리 후보 감사 강화:** `Jacobi Escape Cone` 정리 후보를 검증/반증하기 위한 **Picard 구간 반복(Interval Picard propagation)**, 야코비안 수축 한계(Jacobian contraction bound), 구간 흐름 튜브(Interval flow tube) 도입.
*   **regularization 심화:** Levi-Civita 근접 충돌 정규화의 잔차 및 스케일링 진단 도입. 이는 finite diagnostic이며, 완전한 충돌 정규화 정리의 증명은 아니다.

자체 검증 엔진(`threebody theorem-suite`)을 구동한 결과, 이 시스템의 구체적인 성패가 드러났습니다.

### 초기 핵심 병목 (Historical Bottlenecks)
1.  **`interval_picard_flow_propagation` 및 수축 한계 실패:**
    *   초기 감사 시점에는 Picard 반복 기반 validated-flow 후보(`jacobi_interval_picard_flow`)가 실패했습니다. 당시 수축 인자(contraction factor)가 **1.406**으로 목표치인 **0.35**를 초과하였습니다.
    *   후속 구현에서는 scaled phase-space Jacobian tuning과 resolution/tolerance crosscheck가 추가되었으므로, 이 항목은 현재 결론이 아니라 병목 이력으로 인용해야 합니다.
2.  **경계 산란 ML 모델의 붕괴 (`heldout_scattering_validation` 실패):**
    *   플라이바이(flyby) 탈출/진입 경계를 위상(phase)이나 산란각(deflection angle) 등의 물리적 특징으로 설명하려 했던 산란 맵(Scattering map) 모델들이 엄격한 Held-out 데이터 셋 검증에서 전부 탈락했습니다.
3.  **문법 모델(Grammar Model)의 성패 갈림:**
    *   경로를 단어 구조로 바꾼 'Chart-Word Grammar'가 **재진입(High re-entry) 예측에서는 무작위 대조군을 이기지 못해 실패**했으나, **이력 현상(Hysteresis width)에서는 대조군을 이기는 held-out signal**을 보였습니다. 이것은 메모리 효과와 일치하는 증거이지, 아직 일반 정리의 증명은 아닙니다.

---

## 2. 최초 방향성과의 일치 여부 평가

*   **최초 방향성:** 시뮬레이션 데이터를 뽑아서 차트(해석 공간)로 분류하고, 기계학습 등을 융합해 단순 '컴팩트 대리 모델(Compact Surrogate Model)'을 피팅하는 **데이터 엔지니어링 중심의 탐색 도구**였습니다.
*   **현재 상태:** 단순 데이터 피팅 수준에서 벗어나, 수치 궤도와 국소 해석 주장이 뉴턴 방정식, 보존량, 구간/민감도 진단과 양립하는지 감사하는 **컴퓨터 보조 검증 후보 엔진**으로 피봇했습니다.
*   **일치성 진단:** 이 피봇은 프로젝트 목표와 일치합니다. 다만 `certificate`는 논문 보조자료로 유용한 감사 단위이지, validated ODE propagation이 없는 한 자동으로 수학적 증명을 뜻하지 않습니다.

---

## 3. 상업적 / 학문적 가치 상승도 냉정 평가

### 학문적 가치 (조건부 상승)
*   **과거:** "3체 문제를 시뮬레이션하고 몇 가지 카오스 경계를 시각화했다" -> 학술적 신뢰도 낮음.
*   **현재:** "Noether, Sundman, Levi-Civita 관련 진단과 Jacobi Hamiltonian 분할을 같은 재현성 파이프라인에 묶었다"는 점은 연구 가치가 있습니다.
*   **현재 한계:** 논문 제출 수준의 정리 주장은 여전히 독립 validated ODE backend, interval parameter enclosure, 명시적 regime inequality가 필요합니다. 현재 결과는 정리 후보와 재현성 증거로 표현해야 합니다.

### 💼 상업적 가치 (잠재력의 변화 및 현실화 🔄)
*   **기존 관점:** 3체 문제 시뮬레이터 자체로는 돈을 벌 수 없습니다. 시장이 거의 존재하지 않습니다.
*   **새로운 관점:**
    1.  **고신뢰성 항공우주 설계 보조 툴 (Astrodynamics verification aid):** 지구-달 시스템(제한적 3체 문제)에서 라그랑주/매니폴드 궤도 설계 후보를 감사하는 보조 SDK로 발전할 수 있습니다. 다만 현재 단계는 mission-critical 보증 소프트웨어가 아니라 연구용 검증 보조 도구입니다.
    2.  **AI for Science 물리 샌드박스:** 보존량과 진단 gate가 있는 동역학 학습 환경으로 패키징할 수 있습니다. "수학적으로 완벽히 지켜지는" 환경이 아니라, drift와 실패 조건을 기록하는 reproducible benchmark로 표현해야 합니다.

---

## 4. 향후 나아가야 할 전략적 로드맵 (Action Items)

### 1단계: Picard 수축 장벽 극복 (가장 시급한 수학적 튜닝)
*   `jacobi_interval_picard_flow`를 통과시키는 것이 최우선 과제입니다.
*   **해결책:** 
    *   Picard validator의 세그먼트 단계 크기(Time step)를 더 촘촘히 쪼갭니다.
    *   구간의 팽창(Wrapping effect)을 억제하기 위해 좌표계를 정규형(Normal Form)으로 회전하거나, 고차 테일러 확장(Taylor enclosure)을 적용하여 수축 인자를 `0.35` 이하로 떨어뜨립니다.

### 2단계: 스칼라 경계식 포기 및 기호/위상 전향
*   Held-out 검증에서 처참하게 깨진 '스칼라 산란 모델(Scattering map)'에 더는 자원을 낭비하지 마십시오. 3체 카오스는 연속적인 부드러운 스칼라 함수로 피팅되지 않는 것이 정상입니다.
*   held-out signal이 확인된 **Hysteresis grammar 모델(메모리 효과 후보)**에 집중하여, 상태 전이를 연속 함수 하나로 강제하지 말고 이산적 기호 동역학(Topological Transition Words)과 마르코프 체인 후보로 분리해 검증해야 합니다.

### 3단계: B2B API 패키징 및 AI 벤치마크 런칭
*   이 검증 시스템 전체를 단독 패키지로 격리(`pip install threebody-engine`)하여, AI 연구용 오픈소스 물리 샌드박스 및 항공우주 임무 신뢰성 검증용 SDK 형태로 배포용 아키텍처를 설계하십시오.

---

## 5. 후속 구현 반영

본 감사 이후 다음 코드 조치가 반영되었습니다.

*   **Picard 수축 튜닝:** `jacobi_interval_picard_flow_certificate`는 수축 판정에 scaled phase-space Jacobian bound를 사용합니다. 대표 fast outgoing flyby 인증에서 관측 수축 인자는 목표 `0.35` 아래로 내려갑니다.
*   **Picard 자동 튜닝:** `jacobi_picard_tuning_certificate`가 추가되어 scaled/unscaled 수축 bound와 substep cap 후보를 시도하고, 가장 먼저 통과한 인증 구성을 JSON-ready attempt log와 함께 반환합니다. Certificate는 수축 여유(`contraction_reserve`)와 비용 지표(`mean_substeps_per_segment`, `certification_efficiency`)도 보고합니다.
*   **기호 동역학 피봇:** `ChartWordMarkovChain`, `markov_chain_from_words`, `hysteresis_markov_chain_from_reports`가 추가되어 hysteresis-memory chart word를 Markov chain으로 분석할 수 있습니다. `ChartWordMarkovValidation`은 held-out log likelihood, perplexity, unseen transition count, deterministic accuracy를 보고합니다. `ChartWordMarkovBaselineComparison`은 Markov memory가 독립 next-symbol 빈도 baseline을 실제로 이기는지 검사합니다.
*   **기호 모델 불확실성 게이트:** `ChartWordMarkovBootstrapComparison`과 `bootstrap_markov_baseline_comparison`이 추가되어 held-out transition resampling으로 Markov log-likelihood gain과 perplexity ratio의 bootstrap interval을 계산합니다. 이제 promotion gate는 단순히 baseline을 이겼는지가 아니라 bootstrap lower bound가 양수인지까지 노출합니다.
*   **Markov 차수 선택 게이트:** `select_markov_order`와 `select_hysteresis_markov_order`가 추가되어 0차 독립 모델, 1차 Markov, 2차 memory 모델을 held-out likelihood와 AIC/BIC로 비교합니다. Pages promotion gate는 이제 memory 효과가 단순 baseline뿐 아니라 선택 기준에서도 지지되는지 노출합니다.
*   **Poincare section 진단 추가:** `poincare_section_word_from_reports`, `poincare_section_sweep_from_reports`, `poincare_coordinate_sweep_from_reports`, `word_mode="poincare"`가 추가되어 명시적 단면 통과 사건으로 chart word를 만들 수 있습니다. 대표 Pages 시나리오에서는 고정 hierarchy-perturbation section의 crossing count가 `2`로 부족하지만, 다중 좌표 sweep은 `normalized_area` 단면에서 충분한 crossings를 찾고 해당 Poincare word의 Markov memory가 독립 baseline을 bootstrap interval로 이기는지까지 검증합니다.
*   **Poincare permutation 음성 대조군:** `ChartWordMarkovPermutationControl`과 `permutation_control_markov_validation`이 추가되어 held-out chart word의 symbol multiset은 보존하되 순서만 섞은 음성 대조군을 생성합니다. Pages/API의 Poincare memory gate는 이제 baseline bootstrap, BIC memory selection, permutation-control upper interval 초과를 모두 통과해야 PASS가 됩니다.
*   **Poincare 단면 선택 안정성:** `PoincareMarkovSectionRobustness`와 `poincare_markov_section_robustness`가 추가되어 best coordinate의 여러 section quantile 후보를 반복 평가합니다. Pages는 단일 best section의 우연한 통과가 아니라 nearby sections의 pass count/fraction을 별도 gate로 표시합니다.
*   **Held-out phase 검증 분리:** Pages와 `run_verification_report`의 symbolic Markov/Poincare 검증은 이제 대표 phase word를 학습과 검증에 동시에 쓰지 않습니다. `pi/2`, `pi` binary phases에서 학습하고 phase `0` trajectory를 held-out validation으로 사용해 baseline, Markov order, permutation, section-robustness gate를 평가합니다.
*   **Stride perturbation 안정성:** Pages와 API 리포트는 기준 atlas stride 주변의 local perturbation을 재분석해 hysteresis/Poincare memory gate가 유지되는지 `stride_robustness`로 공개합니다. 이 게이트는 sampling stride 하나에만 의존하는 symbolic artifact를 promotion에서 걸러내기 위한 것입니다.
*   **Build provenance:** 정적 GitHub Pages 산출물은 commit/run/runtime metadata를 함께 포함하므로 공개 figure와 certificate JSON을 정확한 증거 bundle로 역추적할 수 있습니다.
*   **Machine-readable certificate:** GitHub Pages 빌드는 HTML 내부 `<pre>`뿐 아니라 `certificate.json`도 배포해 외부 연구자와 자동화가 promotion gate, atlas snapshot, provenance를 직접 검증할 수 있게 했습니다.
*   **Artifact integrity manifest:** Pages 빌드는 `manifest.json`에 `index.html`과 `certificate.json`의 SHA-256 digest와 byte size를 기록해 공개 증거 bundle의 파일 무결성을 독립적으로 점검할 수 있게 했습니다.
*   **Public favicon artifact:** GitHub Pages 빌드는 이제 3체 궤도/삼각형 모티프의 `favicon.svg`를 생성하고 HTML head에 등록합니다. 이 아이콘도 `manifest.json`에 SHA-256/byte size로 포함되어 공개 bundle의 일부로 검증됩니다.
*   **Evidence publication pipeline:** GitHub Pages 첫 화면에는 Python engine 계산, promotion gate 통과, `certificate.json` 공개, `manifest.json` 무결성 검증으로 이어지는 공개 연구 증거 흐름이 시각적으로 추가되었습니다.
*   **Public verification ladder:** GitHub Pages 첫 화면에는 numerical evidence, Picard certification, symbolic dynamics, robustness gates, public artifacts, claim-level receipt로 이어지는 시각적 감사 ladder가 추가되었습니다. 지금까지의 변화가 단순 UI 업데이트가 아니라 공개 claim 검증 체계로 진화했음을 한 화면에서 보여줍니다.
*   **Static artifact verifier:** `python -m threebody.cli verify-static-artifacts --site-dir site` 명령이 추가되어 `manifest.json`의 SHA-256/byte-size 기록과 `certificate.json` provenance 일관성을 로컬 또는 내려받은 Pages bundle에서 재검증할 수 있습니다.
*   **Public URL artifact verifier:** 같은 검증기는 이제 `--base-url https://eljja.github.io/3body/`를 받아 공개 GitHub Pages에서 `index.html`, `certificate.json`, `manifest.json`을 직접 내려받아 동일한 SHA-256/byte-size/provenance 검사를 수행합니다. 외부 연구자가 저장소를 clone하지 않고도 현재 공개 증거 bundle을 감사할 수 있습니다.
*   **Commit-pinned publication verifier:** `--require-commit <sha-or-prefix>` 옵션이 추가되어 논문/리뷰/외부 감사에서 인용한 특정 commit의 증거 bundle인지 강제할 수 있습니다. Pages가 새로 배포되어도 인용된 산출물과 현재 공개 산출물이 어긋나면 검증이 실패합니다.
*   **Verification receipt artifact:** `verify-static-artifacts --output <path>`가 추가되어 검증 schema, UTC 검증 시각, verifier 이름, source, required commit, 실제 commit, 모든 check 결과를 JSON receipt로 저장할 수 있습니다. CI와 외부 감사에서 검증 결과를 보존 가능한 연구 산출물로 남길 수 있습니다.
*   **Claim-level promotion gate verifier:** `--require-gate <promotion_gate_name>` 옵션이 반복 가능하게 추가되어 공개 certificate의 특정 과학적 promotion gate가 `true`일 때만 검증 receipt가 통과합니다. 예를 들어 Picard 인증, Poincare permutation control, stride robustness를 citation-level 조건으로 강제할 수 있습니다.
*   **Quantitative certificate threshold verifier:** `--require-min <dotted.path>=<number>` 옵션이 반복 가능하게 추가되어 공개 certificate의 정량 scalar가 지정한 하한을 만족할 때만 검증 receipt가 통과합니다. 예를 들어 public gate pass count, Picard contraction reserve, section/stride robustness fraction을 citation-level 수치 조건으로 고정할 수 있습니다.
*   **Quantitative upper-bound verifier:** `--require-max <dotted.path>=<number>` 옵션이 반복 가능하게 추가되어 공개 certificate의 정량 scalar가 지정한 상한 이하일 때만 검증 receipt가 통과합니다. Picard maximum contraction, energy drift, Jacobi drift처럼 작아야 의미가 있는 수치 조건을 논문/리뷰용 감사 receipt에 직접 고정할 수 있습니다.
*   **Versioned public claim profile:** `--require-profile public-claims-v1` 옵션이 추가되어 공개 Pages claim에 필요한 gate/min/max 조건 묶음을 하나의 버전 고정 프로파일로 적용할 수 있습니다. Receipt는 `required_profiles`와 프로파일이 확장한 조건 목록을 함께 저장하므로, 외부 연구자나 리뷰어가 긴 검증 명령을 손으로 재구성하지 않아도 동일한 claim set을 감사할 수 있습니다.
*   **Claim profile digest:** `public-claims-v1` 프로파일의 canonical descriptor에 SHA-256 digest가 추가되어 certificate와 verification receipt 양쪽에 기록됩니다. 이제 공개 claim은 파일 무결성뿐 아니라 "어떤 조건 묶음을 검증했는가" 자체도 해시로 고정할 수 있습니다.
*   **Active claim profile enforcement:** `--require-profile public-claims-v1` 검증은 이제 certificate에 올바른 profile digest가 첨부되어 있는지만 보지 않습니다. `publication_pipeline.verification_profile`이 요청한 active profile인지, active digest가 canonical digest와 일치하는지, `verification_profiles`에 내장된 descriptor 내용이 canonical descriptor와 정확히 같은지까지 검사합니다. 따라서 certificate가 올바른 digest 문자열만 붙이고 실제 claim profile을 바꾸거나 descriptor 조건을 축소하는 경우 검증이 실패합니다.
*   **Artifact identity and pipeline-link enforcement:** 정적 artifact verifier는 이제 manifest/certificate의 SHA-256과 크기뿐 아니라 artifact identity와 publication pipeline link도 검사합니다. `manifest.json`은 ThreeBody static-site manifest여야 하고, `certificate.json`은 static research certificate여야 하며, certificate 내부 pipeline은 `threebody.ui.static_site`, `certificate.json`, `manifest.json`을 일관되게 가리켜야 합니다.
*   **Index artifact discoverability enforcement:** 정적 artifact verifier는 이제 `index.html`이 `certificate.json`, `manifest.json`, `favicon.svg`를 실제 링크하는지도 검사합니다. 공개 페이지가 파일 무결성은 맞지만 외부 연구자가 증거 산출물을 웹에서 발견할 수 없는 상태로 배포되는 것을 막습니다.
*   **Verification schema feature list:** verifier receipt는 이제 `verification_schema_features`를 포함합니다. 외부 감사 도구는 schema version 숫자만 추정하지 않고 artifact availability, JSON parse error reporting, active profile descriptor, index discoverability 같은 검증 능력이 포함된 receipt인지 기계적으로 요구할 수 있습니다.
*   **Required verifier feature gates:** `verify-static-artifacts`는 이제 `--require-feature <name>`을 반복해서 받을 수 있습니다. 요청한 verifier capability가 현재 receipt의 `verification_schema_features`에 없으면 `required_features=false`와 `required_feature_results`를 남기고 실패하므로, 외부 감사 자동화가 필요한 검증 능력을 명령 단계에서 고정할 수 있습니다.
*   **Public profile feature requirements:** `public-claims-v1`은 이제 gate/min/max 조건뿐 아니라 공개 claim 검증에 필요한 verifier capability 목록도 포함합니다. 따라서 `--require-profile public-claims-v1`만으로 artifact availability, JSON parse reporting, index discoverability, active profile descriptor 같은 감사 능력까지 profile digest로 고정됩니다.
*   **Frozen public profile feature set:** `public-claims-v1`의 required verifier capability 목록은 live verifier feature list를 직접 참조하지 않고 별도 tuple로 고정됩니다. 앞으로 verifier가 optional capability를 추가해도 v1 profile digest가 암묵적으로 바뀌지 않으며, profile 변경은 명시적 연구 감사 이벤트가 됩니다.
*   **Advertised-feature based gating:** `required_feature_results`는 이제 내부 상수가 아니라 receipt가 실제 광고하는 `verification_schema_features` 목록을 기준으로 계산됩니다. 따라서 감사 receipt 안에서 "요구한 capability"와 "광고된 capability"의 관계가 직접 닫혀 있습니다.
*   **Verifier feature-set digest:** verifier receipt는 이제 `verification_schema_features_sha256`도 포함합니다. 외부 감사자는 긴 capability 배열 전체를 매번 비교하지 않고도 현재 receipt가 같은 verifier capability set과 순서를 광고하는지 짧은 SHA-256 값으로 고정할 수 있습니다.
*   **Required feature-set digest gate:** `verify-static-artifacts`는 이제 `--require-feature-set-sha256 <digest>`를 받아 receipt의 `verification_schema_features_sha256`이 기대값과 다르면 `required_feature_set_sha256=false`로 실패합니다. 논문, CI, 리뷰 명령이 verifier capability set 전체를 한 값으로 pin할 수 있습니다.
*   **Current verifier feature-set pin:** `verify-static-artifacts --require-current-feature-set`은 실행 중인 verifier의 canonical feature-set digest를 `required_feature_set_sha256`에 자동으로 기록합니다. 공개 감사 명령이 긴 digest를 손으로 복사하지 않아도 receipt에 현재 verifier capability set pin을 남길 수 있습니다.
*   **Public claim shortcut:** `verify-static-artifacts --require-public-claim`은 `public-claims-v1` 프로파일과 현재 verifier feature-set pin을 함께 적용합니다. 공개 Pages claim 감사에서 profile 요구와 capability-set pin 중 하나를 빠뜨리는 명령 실수를 줄입니다.
*   **Public claim API shortcut:** `verify_static_artifacts()`, `verify_static_artifacts_from_url()`, `verify_static_artifact_bytes()`도 이제 `require_public_claim=True`를 받습니다. CLI를 거치지 않는 notebook, CI wrapper, 외부 연구 자동화도 같은 public profile과 verifier capability-set pin을 한 옵션으로 적용할 수 있습니다.
*   **Stable engine public verifier API:** `threebody_engine.verify_public_static_artifacts()`, `verify_public_static_artifacts_from_url()`, `verify_public_static_artifact_bytes()`가 추가되었습니다. 외부 연구자가 내부 `threebody.cli` 모듈을 직접 의존하지 않고도 공개 Pages evidence bundle을 안정 API 표면에서 검증할 수 있습니다.
*   **Stable public claim contract API:** `threebody_engine.public_static_artifact_claim_contract()`는 공개 claim profile, profile digest, canonical descriptor, verifier feature list, verifier feature-set digest를 JSON-ready dict로 반환합니다. 외부 CI나 논문 보조 코드가 검증 실행 전에도 어떤 claim contract를 요구하는지 안정 API로 기록할 수 있습니다.
*   **Stable receipt-contract validator:** `threebody_engine.validate_public_static_artifact_receipt_contract()`는 verifier receipt가 공개 profile, profile digest, required feature-set digest, receipt-advertised feature-set digest, certificate-advertised feature-set digest와 일치하는지 JSON-ready check map으로 판정합니다. 외부 감사 자동화가 receipt 필드를 직접 흩어서 비교하지 않아도 됩니다.
*   **Stable public audit report API:** `threebody_engine.audit_public_static_artifacts()`, `audit_public_static_artifacts_from_url()`, `audit_public_static_artifact_bytes()`는 contract, verifier receipt, receipt-contract validation을 한 JSON-ready 객체로 묶습니다. 논문 보조자료나 CI artifact가 공개 claim 검증의 입력 계약과 실행 결과를 한 파일로 보존할 수 있습니다.
*   **Platform-stable static artifact bytes:** 정적 site writer는 이제 `index.html`, `certificate.json`, `manifest.json`, `favicon.svg`, `.nojekyll`을 LF 줄바꿈으로 고정해 씁니다. Windows에서 수동 배포하거나 Git이 line ending을 정규화해도 manifest SHA-256이 GitHub Pages가 실제로 서빙하는 바이트와 어긋나지 않도록 했습니다.
*   **Published branch line-ending guard:** 생성된 `site/.gitattributes`가 `* text eol=lf`를 선언합니다. `site` 디렉터리를 별도 `gh-pages` git repository로 초기화하거나 수동 복사해 배포해도, 생성된 public artifact의 byte-level hash 의미론이 유지됩니다.
*   **Published branch policy verification:** `.gitattributes`도 이제 `manifest.json`에 SHA-256/byte size로 포함되고, static artifact verifier는 내용이 정확히 `* text eol=lf`인지 검사합니다. 따라서 공개 claim 검증은 HTML/JSON/SVG 무결성뿐 아니라 배포 브랜치의 줄바꿈 정책까지 같은 receipt 안에서 보증합니다.
*   **Timestamp-independent receipt fingerprint:** verification receipt는 이제 `receipt_payload_sha256`을 포함합니다. 이 digest는 `verified_at_utc`와 digest 필드 자체를 제외한 canonical JSON에 대해 계산되므로, 서로 다른 시각에 같은 공개 claim을 검증한 독립 실행들이 같은 payload fingerprint를 공유할 수 있습니다.
*   **Timestamp-independent audit report fingerprint:** stable engine audit report는 이제 `audit_payload_sha256`을 포함합니다. contract, receipt, receipt-contract validation을 묶은 전체 audit object가 `verified_at_utc` 차이를 제외하고 같은지 비교할 수 있어, 논문 보조자료와 CI artifact의 인용 단위를 receipt 한 조각이 아니라 audit bundle 전체로 올릴 수 있습니다.
*   **Reduced-state report bridge:** 일반 3체 `AnalysisReport`는 이제 기존 chart feature 객체와 함께 `ReducedThreeBodyState` snapshot을 보존합니다. classifier 라벨을 한 번에 바꾸지 않고도 downstream grammar/transition 모델이 hyperradius, shape area, anisotropy, hierarchy strength 같은 공통 shape-scale 좌표를 직접 참조할 수 있습니다.
*   **Current change ledger on Pages:** GitHub Pages는 이제 `Current change ledger` 섹션과 `certificate.json.recent_change_ledger`를 함께 생성합니다. reduced-state bridge, `.gitattributes` 정책 검증, receipt/audit fingerprint, stable public API contract가 화면과 machine-readable certificate에서 같은 순서로 보입니다.
*   **Operational three-body prediction API:** `threebody_engine.predict_three_body_positions`와 `predict_three_body_position_distribution`이 추가되었습니다. 첫 함수는 유한하고 비충돌이며 진단 gate를 통과한 일반 뉴턴 삼체 초기조건에서 `t` 시각 위치/속도와 Noether invariant drift 진단을 반환하고, 둘째 함수는 선언된 초기 위치/속도 불확실성을 ensemble로 전파해 최종 위치 평균, 분위수, 공분산을 산출합니다.
*   **Random three-body prediction demo:** `threebody_engine.generate_random_three_body_case`, `solve_random_three_body_prediction_demo`, `threebody random-demo`가 추가되었습니다. 이 경로는 seed가 고정된 비충돌 일반 삼체 초기조건을 생성하고 adaptive final state, deterministic ephemeris final row, compact target solver, empirical mean readout을 고정밀 reference integration과 비교해 point error, energy drift, close-approach gate를 통과해야만 success를 승격합니다.
*   **Global closed-form research contract:** `threebody_engine.global_closed_form_solution_contract`와 `assess_three_body_global_closed_form_claim`이 추가되었습니다. 이 경로는 유한 초등함수 전역해를 주장하지 않고, Sundman-style regularized convergent series route를 현재 방어 가능한 닫힌 표현 후보로 분리합니다. 입력 초기조건에 대해 초기 binary collision gate, nonzero angular momentum gate, pair-distance/center-of-mass 진단, 남은 proof obligation을 JSON certificate로 반환합니다.
*   **One-call prediction solution bundle:** `threebody_engine.solve_three_body_prediction_problem`와 `threebody predict --solution`이 추가되었습니다. 결정론적 ephemeris, empirical distribution ephemeris, 최종 위치/최종 위치분포 요약, forecast-horizon 및 해석 verdict를 하나의 JSON answer bundle로 반환합니다.
*   **Time-resolved distribution comparison:** one-call solution bundle은 이제 `ephemeris_distribution_comparison`을 포함합니다. linearized Gaussian ephemeris와 empirical distribution ephemeris를 각 샘플 시각별 평균 gap, sigma 단위 gap, 공분산 Frobenius/relative gap으로 비교하고 선형화 근사가 gate를 벗어나는 첫 시각을 보고합니다.
*   **Center-of-mass matched uncertainty model:** one-call solution/report는 이제 empirical ensemble과 linearized Gaussian covariance가 같은 중심질량 보존 초기 불확실성 가정에서 출발합니다. standalone linearized/horizon CLI에는 `--preserve-center-of-mass`와 `--independent-body-uncertainty` 선택지를 추가해 비교 전제를 명시할 수 있습니다.
*   **Full covariance probability forecasts:** empirical distribution/distribution-ephemeris, one-call solution, report, CLI가 이제 입력 JSON/API의 `initial_state_covariance`를 공유합니다. 따라서 2D `12x12` 또는 3D `18x18` 전체 상태 공분산을 ensemble sampling, variational Gaussian, forecast horizon에 같은 `P0`로 전파할 수 있습니다.
*   **Position confidence regions:** linearized Gaussian, empirical distribution, distribution ephemeris, one-call final distribution이 이제 각 물체별 50/90/95/99% 위치 confidence ellipse/ellipsoid를 반환합니다. 평균과 공분산을 다시 고유분해하지 않아도 반축 길이, 방향, Mahalanobis radius로 확률적 위치 영역을 바로 그릴 수 있습니다.
*   **Position hypothesis scoring:** `threebody_engine.score_three_body_position_hypothesis`와 `threebody predict --score-positions`가 추가되었습니다. `candidate_positions`를 linearized Gaussian 예측분포에 대해 물체별/전체 Mahalanobis 거리, Gaussian log-density, 50/90/95/99% confidence membership으로 채점해 특정 t 시각 위치 주장 자체를 판정할 수 있습니다.
*   **Explicit requested-time ephemerides:** deterministic, linearized Gaussian, empirical distribution ephemeris와 `threebody predict` CLI가 입력 JSON의 `target_times`를 지원합니다. 균등 `samples` 대신 관측/분석에 필요한 비균등 시각 목록에서 위치와 확률분포를 정확히 반환합니다.
*   **Aligned requested-time solution ephemerides:** `threebody_engine.solve_three_body_prediction_problem`는 이제 `target_times`가 주어질 때 결정론적 ephemeris, 선형화 Gaussian ephemeris, 경험분포 ephemeris, 그리고 Gaussian-vs-empirical 비교가 모두 같은 비균등 관측 시간축을 사용합니다. 비교 객체는 `times`, `time_grid_aligned`, `maximum_time_mismatch`를 포함해 외부 notebook/감사자가 시간축 불일치 없이 위치와 확률분포를 비교했는지 확인할 수 있습니다.
*   **Close-approach prediction diagnostics:** deterministic point/ephemeris, one-call solution, empirical distribution ephemeris가 최소 sampled pair distance, 발생 시각/쌍, characteristic scale 대비 비율, softening 대비 비율, regularization 권고 여부를 반환합니다. 주어진 admissible 삼체 예측이 근접충돌 특이성 근처를 통과했는지 공개적으로 감사할 수 있습니다.
*   **Finite-time sensitivity diagnostics:** linearized Gaussian distribution/ephemeris와 forecast horizon이 `D Phi_t`의 최대/최소 singular value, uncertainty amplification factor, finite-time Lyapunov exponent를 반환합니다. one-call solution도 최종 민감도 지표를 answer에 포함해 점 예측/확률 예측의 국소 예측 가능성을 함께 보고합니다.
*   **Report-ready prediction summary:** one-call solution은 이제 `prediction_summary`를 포함합니다. 이 요약은 `target-position-and-distribution`, `distributional-target-position`, `deterministic-target-position`, `unresolved-target-position` 중 하나의 claim으로 결과를 승격하고, 결정론적 최종 위치, 확률분포 평균/중앙값, 95% confidence region, 신뢰성/위험 문장, 핵심 민감도/근접접근 지표를 한 번에 제공합니다.
*   **Machine-readable mathematical prediction statement:** one-call solution은 이제 `mathematical_statement`를 포함합니다. 일반 뉴턴 삼체 초기값 문제의 방정식, `x(t)=Phi_t(x(0))` flow-map, `r_i(t)=Pi_{r_i} Phi_t(x(0))` 위치 readout, `Law(X_t)=(Phi_t)_# Law(X_0)` 확률 push-forward, `P_t=D Phi_t P_0 D Phi_t^T` 선형화 공분산 공식, 물체별 target-time claim row를 같은 JSON 안에 고정합니다.
*   **Compact target-position solution API:** `threebody_engine.solve_three_body_target_positions`가 추가되었습니다. full solution bundle을 직접 읽지 않아도 `target_positions`, `target_position_distribution`, 물체별 answer row, 결정론적 flow 정의, 확률 push-forward 정의, 핵심 신뢰성 진단만 반환해 “주어진 admissible 삼체가 t 이후 어디에 있는가”라는 원래 질문에 가장 짧은 JSON 답을 제공합니다.
*   **Table-ready target-position answer:** compact target solution은 이제 `target_position_table`을 포함합니다. 각 물체별 결정론적 좌표, 확률 평균/중앙값, 중앙 90% 좌표 구간, 95% confidence region 최대 반축, 결정론적 좌표와 평균 사이 거리를 한 행으로 정리해 논문 표나 웹 시각화에 바로 사용할 수 있습니다.
*   **Per-body position readout strength:** `target_position_table`은 이제 characteristic position scale 대비 95% 반경인 `relative_95_radius`, `position_claim_strength`, `recommended_readout`을 포함합니다. 따라서 각 물체별로 점 좌표를 같이 보고해도 되는지, confidence region을 중심으로 써야 하는지, 분포 요약만 써야 하는지 자동 판정할 수 있습니다.
*   **Center-of-mass target frame:** compact target solution은 이제 `center_of_mass_frame`을 포함합니다. 목표 시각 중심질량 위치/속도, 중심질량 변위, 세 물체의 중심질량 기준 상대좌표, 확률 평균의 중심질량 기준 좌표를 제공해 관성 좌표계 평행이동에 덜 의존하는 삼체 형상 해석이 가능합니다.
*   **Target pair geometry:** compact target solution은 이제 `target_pair_geometry`를 포함합니다. 목표 시각 세 쌍의 거리/분리벡터, deterministic perimeter/triangle area, 확률 평균 기준 perimeter/area, coordinate quantile box에서 유도한 보수적 90% pair-distance bounds를 제공해 좌표뿐 아니라 삼체 형상 자체를 바로 해석할 수 있습니다.
*   **Target distribution sampling quality:** compact target solution은 이제 `target_distribution_quality`를 포함합니다. empirical probability answer의 물체별 평균 표준오차, 최대 평균 표준오차, characteristic scale 대비 상대 표준오차, `well-sampled`/`usable`/`sampling-noisy` 등급을 제공해 분포 평균을 과신하지 않도록 합니다.
*   **Target sensitivity budget:** compact target solution은 이제 `target_sensitivity_budget`을 포함합니다. 목표 시각의 forecast-horizon 통과 여부, 위치 허용오차, 변분 전파된 최종 위치 표준편차, tolerance ratio, uncertainty amplification, finite-time Lyapunov exponent, close-approach gate를 한 블록에서 보여줍니다.
*   **Target readout decision:** compact target solution은 이제 `target_readout_decision`을 포함합니다. 같은 입력에 대해 `r_i(t)` 점좌표를 보고할지, push-forward 확률분포를 보고할지, deterministic-only로 제한할지, unresolved로 남길지를 diagnostic gate와 per-body readout으로 명시합니다.
*   **GitHub Pages target-answer visual:** static site 첫 화면은 이제 원래 문제의 답인 `r_i(t)` 또는 `Law(X_t)`를 중심으로 재구성되었습니다. target-time geometry, sensitivity budget, readout decision, certificate digest를 한 화면에 묶고 `certificate.json`에도 `target_prediction_answer` 요약을 포함합니다.
*   **GitHub Pages content-switching navigation:** static site는 이제 왼쪽 fixed navigation rail로 우측 research content workspace를 같은 페이지 안에서 교체합니다. ThreeBody, 닫힌형 경로, 방법론적으로 관련 있는 Collatz 패널과 GitHub repository 버튼을 제공하며 메뉴/패널 정의는 `threebody.ui.static_content`에 분리했습니다. Riemann, Goldbach, twin-prime 패널은 현재 삼체 증거 bundle의 핵심 범위가 아니므로 공개 ThreeBody 페이지에서 제거했습니다.
*   **Target prediction reproducibility certificate:** one-call solution은 `prediction_input_contract`와 `prediction_input_sha256`을 포함하고, compact target solution은 `target_prediction_certificate`를 포함합니다. 질량/초기 위치/속도/목표 시간/solver/uncertainty 설정과 결과 payload를 SHA-256으로 고정해 외부 연구자가 같은 target answer를 재현 감사할 수 있습니다.
*   **Target prediction certificate validator:** `threebody_engine.validate_three_body_target_prediction_certificate`가 추가되었습니다. compact target solution의 입력 계약 digest, 결과 payload digest, payload key set, claim/recommended mode/schema/type 일치 여부를 JSON-ready validation report로 검증하고 결과 변조를 감지합니다.
*   **Compact target-position CLI:** `threebody predict --target-solution`이 추가되었습니다. JSON 입력 파일만으로 compact target-position answer를 파일로 저장할 수 있어, full ephemeris bundle이 필요 없는 외부 사용자도 즉시 `r_i(t)`와 target-time probability distribution을 받을 수 있습니다.
*   **Deterministic three-body ephemeris:** `threebody_engine.predict_three_body_ephemeris`와 `threebody predict --ephemeris`가 추가되었습니다. 유한하고 비충돌인 일반 뉴턴 삼체 초기조건에서 `0..t` 샘플 시간별 세 물체 위치/속도 표를 반환하고, 선택적으로 energy/momentum invariant series를 함께 내보냅니다.
*   **Empirical distribution ephemeris:** `threebody_engine.predict_three_body_distribution_ephemeris`와 `threebody predict --distribution-ephemeris`가 추가되었습니다. 초기조건 Gaussian ensemble을 전체 시간 grid에 대해 전파하고 각 샘플 시각의 세 물체 위치 평균, 분위수, flatten 공분산, 평균으로부터의 최대 반경을 반환합니다.
*   **Variational Gaussian prediction:** `threebody_engine.predict_three_body_linearized_distribution`과 `threebody predict --linearized-distribution`이 추가되었습니다. 초기 공분산 `P0` 또는 위치/속도 scale을 상태전이행렬 `D Phi_t`로 전파해 `P(t)=D Phi_t P0 D Phi_t^T` 형태의 국소 Gaussian 위치분포를 반환합니다.
*   **Linearized Gaussian ephemeris:** `threebody_engine.predict_three_body_linearized_ephemeris`와 `threebody predict --linearized-ephemeris`가 추가되었습니다. 변분 flow trace를 따라 모든 샘플 시각에서 `P(t_k)=D Phi_{t_k} P0 D Phi_{t_k}^T`를 계산해 시간별 Gaussian 위치 공분산과 표준편차를 반환합니다.
*   **Unified prediction interpretation report:** `threebody_engine.predict_three_body_interpretation_report`와 `threebody predict --report`가 추가되었습니다. 결정론적 flow, variational Gaussian, empirical ensemble을 함께 실행하고 평균 위치 gap, 공분산 Frobenius gap, sigma 단위 gap을 비교해 `linearized-gaussian`, `empirical-ensemble`, `deterministic-only`, `unresolved` 중 권장 해석 모드를 반환합니다.
*   **Tolerance-resolved forecast horizon:** `threebody_engine.predict_three_body_forecast_horizon`와 `threebody predict --horizon`이 추가되었습니다. 초기 공분산을 여러 중간 시각의 변분 flow로 전파하고 `max_position_std / position_tolerance`를 기록해 목표 시각이 선언한 위치 오차 허용치 안에 남아 있는지 판정합니다. 통합 prediction report도 이제 이 forecast horizon을 포함합니다.
*   **Prediction CLI and method note:** `threebody predict --input initial-state.json` 명령이 추가되어 같은 예측 계층을 JSON 입출력으로 실행할 수 있습니다. `docs/PREDICTION_METHOD.md`는 결정론적 flow-map 평가와 초기조건 불확실성의 push-forward 분포라는 수학적 해석을 명시합니다.
*   **Certificate verifier-capability self-check:** 공개 certificate가 싣는 `verification_schema_features`와 `verification_schema_features_sha256`도 verifier receipt의 canonical feature list/digest와 일치해야 합니다. 따라서 certificate를 다시 해시해 manifest를 맞춰도, certificate가 오래되었거나 축소된 verifier capability set을 광고하면 `certificate_verification_schema_features*` 체크가 실패합니다.
*   **Certificate verifier-capability diagnostics:** verifier receipt는 certificate가 실제로 광고한 `certificate_verification_schema_features`와 `certificate_verification_schema_features_sha256`도 보존합니다. self-check가 실패할 때 외부 감사자는 certificate 파일을 다시 열지 않고도 verifier canonical set과 certificate-advertised set의 차이를 추적할 수 있습니다.
*   **Manifest hash-algorithm enforcement:** 정적 artifact verifier는 이제 `manifest.json`이 `hash_algorithm: sha256`을 선언하는지도 검사합니다. 파일 digest와 byte size가 우연히 맞더라도 manifest가 다른 알고리즘을 선언하면 공개 증거 bundle 검증은 실패하므로 외부 감사자가 같은 무결성 의미론을 재현할 수 있습니다.
*   **Malformed artifact hardening:** verifier는 이제 invalid JSON, `build_provenance`나 `artifacts` 같은 중첩 JSON 필드의 형식 오류를 예외로 중단하지 않고 receipt의 개별 check 실패와 parse error로 보고합니다. 또한 certificate와 manifest의 commit provenance는 양쪽 모두 비어 있지 않은 문자열이고 서로 같을 때만 통과합니다.
*   **Missing artifact hardening:** verifier는 이제 `index.html`, `certificate.json`, `favicon.svg`, `manifest.json` 중 일부가 로컬에서 없거나 공개 URL에서 fetch 실패해도 예외로 중단하지 않고 `*_available=false`, hash/size 실패, `artifact_errors`를 포함한 receipt를 생성합니다.
*   **Direct bytes verifier parity:** `verify_static_artifact_bytes()`를 직접 호출하는 자동화도 필수 artifact key가 빠진 경우 `*_available=false`와 `artifact_errors`를 남기도록 맞췄습니다. CLI, URL verifier, direct bytes verifier가 같은 실패 모델을 공유합니다.
*   **Direct API boundary hardening:** `verify_static_artifact_bytes()`는 이제 dict가 아닌 `artifact_errors`나 bytes가 아닌 artifact payload를 받아도 예외로 중단하지 않습니다. 대신 해당 artifact를 unavailable/hash-failed로 표시하고 receipt에 타입 오류를 남겨 notebook, 외부 에이전트, CI wrapper가 같은 실패 형식을 소비할 수 있게 했습니다.
*   **Published claim seal:** GitHub Pages에 공개 claim seal 섹션이 추가되어 commit-pinned build, scientific gate profile, bounded numerical drift, active canonical profile digest를 하나의 시각적 감사 체인으로 보여줍니다. 같은 내용은 `certificate.json`의 `public_change_summary`에도 기록되어 화면과 기계 판독 산출물이 일치합니다.
*   **Public page de-duplication:** GitHub Pages 본문에서 중복되던 evidence pipeline, verification ladder, raw certificate dump를 제거하고, 핵심 검증 체인을 `Public claim audit chain` 하나로 압축했습니다. 전체 JSON 증거는 화면을 비대하게 만들지 않고 `certificate.json` 링크와 verifier receipt로 유지됩니다.
*   **Engine API 분리:** 배포명은 `threebody-engine`으로 조정되었고, 안정 API 표면은 `threebody_engine` 패키지에 추가되었습니다. 주요 entry point는 `integrate_reference_scenario`, `certify_jacobi_escape`, `certify_jacobi_escape_report`, `tune_jacobi_picard`, `build_hysteresis_markov_chain`, `validate_hysteresis_markov_chain`, `compare_hysteresis_markov_to_baseline`, `compare_hysteresis_markov_to_baseline_with_uncertainty`, `select_hysteresis_markov_order`, `run_verification_report`입니다.
