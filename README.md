# ThreeBody

<p>
  <a href="#english">English</a>
  ·
  <a href="#korean-summary">한국어</a>
</p>

<a id="english"></a>

`ThreeBody` is a research project for building an analysis atlas of the two-body, restricted three-body, and general Newtonian three-body problems.

The project is built around five ideas:

- Use the two-body problem as an analytic baseline.
- Treat simulation as instrumentation, not as the final objective.
- Combine classical mechanics, perturbation theory, regularization, continuation, invariant manifolds, and data-assisted discovery.
- Decompose state space into interpretive charts and track transitions between them.
- Build compact models only inside explicitly identified charts.

**Paper-status note.** This repository is a research evidence package, not a
claim that the generic Newtonian three-body problem has been solved. Paper-facing
claims must be read through
[Paper-Readiness Review](docs/PAPER_READINESS_REVIEW.md) and
[Validation Guardrails](docs/VALIDATION_GUARDRAILS.md).

**논문용 상태 메모.** 이 저장소는 연구 증거 패키지이며, 일반 뉴턴 삼체
문제가 해결되었다는 주장이 아니다. 논문 제출용 주장은 반드시
[Paper-Readiness Review](docs/PAPER_READINESS_REVIEW.md)와
[Validation Guardrails](docs/VALIDATION_GUARDRAILS.md)의 기준으로 읽어야 한다.

## Korean Summary

<a id="korean-summary"></a>

`ThreeBody`는 이체, 제한 삼체, 일반 뉴턴 삼체 문제를 하나의 전역 공식으로
해결했다고 주장하지 않는다. 대신 상태공간을 해석 가능한 chart로 나누고,
각 chart에서 사용할 수 있는 계산/진단/정리 후보를 분리해 감사 가능한 연구
atlas를 구축한다.

현재 공개적으로 주장할 수 있는 범위는 다음과 같다.

- 유한하고 비충돌이며 진단 gate를 통과한 특정 초기조건/목표시간에 대해
  `r_i(t)` 또는 `Law(X_t)`를 계산하는 유한시간 예측 API.
- 랜덤 삼체 초기조건을 생성하고 여러 readout을 고정밀 reference integration과 비교하는 데모.
- Jacobi escape cone, hysteresis symbolic dynamics, static artifact verifier 같은 정리 후보/감사 산출물.
- Sundman식 정규화 수렴급수 연구 계약. 단, 일반 삼체 문제의 유한 초등함수 전역해는 주장하지 않는다.

논문용 claim 기준은 [Paper-Readiness Review](docs/PAPER_READINESS_REVIEW.md)와
[Validation Guardrails](docs/VALIDATION_GUARDRAILS.md)를 우선한다.

## What Is Implemented

- `systems`
  - `TwoBodySystem`
  - `RestrictedThreeBodySystem`
  - `GeneralThreeBodySystem`
- `solvers`
  - `AnalyticTwoBodySolver`
  - `AdaptiveIntegrator`
  - `StructureAwareIntegrator`
- `diagnostics`
  - `InvariantMonitor`
  - `StabilityAnalyzer`
  - `PhaseSpaceTools`
- `analysis`
  - `AnalysisAtlas`
  - `ChartClassifier`
  - `jacobi_open_escape_cone_certificate`
  - `jacobi_quadrupole_acceleration_certificate`
  - `finite_difference_jacobian`
  - local chart transition detection
- `experiments`
  - `OrbitLibrary`
  - `InitialConditionScanner`
  - `CompactModelFitter`
- `ui`
  - Streamlit application for interactive exploration
  - Static GitHub Pages visualizer generated from precomputed reference runs

## Scientific Position

The project does not treat the three-body problem as something to merely visualize.
The goal is to construct a working analysis method.
The paper-facing claim standard is defined in
[Paper-Readiness Review](docs/PAPER_READINESS_REVIEW.md): reproducibility
certificates are audit artifacts, theorem candidates remain conditional, and
the project does not claim a finite elementary closed-form solution of the
generic Newtonian three-body problem.

- The two-body problem remains the analytic reference because center-of-mass separation and relative-coordinate reduction turn it into a one-body central-force problem.
- The general three-body problem is not generically integrable by one global formula, so the project treats it as an atlas problem.
- Each region of state space should be assigned an interpretive chart: hierarchy, restricted/Lagrange, close encounter, periodic-orbit neighborhood, chaotic transport, or escape/scattering.
- A real result is a chart, a validity condition, a reduced model, and a transition rule to neighboring charts.
- The current theorem candidate is the conditional Jacobi escape cone: a hierarchy/escape regime certified by Jacobi energy split, quadrupole future-tail bound, inflated margin, self-consistent radial floor, open-cone radius, and parameter-box reserve checks.

## Quick Start

Install the package in editable mode:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pip install -e .[dev]
```

The distribution package is `threebody-engine`.
The research implementation remains importable as `threebody`, while the stable verification API is exposed as `threebody_engine`:

```python
from threebody_engine import (
    answer_three_body_problem,
    audit_public_static_artifact_bytes,
    audit_public_static_artifacts,
    audit_public_static_artifacts_from_url,
    build_hysteresis_markov_chain,
    compare_hysteresis_markov_to_baseline,
    compare_hysteresis_markov_to_baseline_with_uncertainty,
    certify_jacobi_escape,
    certify_jacobi_escape_report,
    integrate_reference_scenario,
    predict_three_body_distribution_ephemeris,
    predict_three_body_ephemeris,
    predict_three_body_forecast_horizon,
    predict_three_body_interpretation_report,
    predict_three_body_linearized_distribution,
    predict_three_body_linearized_ephemeris,
    predict_three_body_position_distribution,
    predict_three_body_positions,
    public_static_artifact_claim_contract,
    generate_random_three_body_case,
    run_verification_report,
    select_hysteresis_markov_order,
    solve_random_three_body_prediction_demo,
    solve_three_body_prediction_problem,
    solve_three_body_target_positions,
    score_three_body_position_hypothesis,
    tune_jacobi_picard,
    validate_three_body_target_prediction_certificate,
    validate_hysteresis_markov_chain,
    validate_public_static_artifact_receipt_contract,
    verify_public_static_artifact_bytes,
    verify_public_static_artifacts,
    verify_public_static_artifacts_from_url,
)
```

For a finite admissible Newtonian three-body initial state and a declared finite target time,
use the prediction API rather than a claimed global closed-form solution. If the trajectory
approaches a collision or fails the diagnostic gates, the correct output is a limited or
unresolved forecast, not a paper-level position claim:

```python
from threebody_engine import (
    answer_three_body_problem,
    predict_three_body_distribution_ephemeris,
    predict_three_body_ephemeris,
    predict_three_body_forecast_horizon,
    predict_three_body_interpretation_report,
    predict_three_body_linearized_distribution,
    predict_three_body_linearized_ephemeris,
    predict_three_body_position_distribution,
    predict_three_body_positions,
    solve_three_body_prediction_problem,
    solve_three_body_target_positions,
    score_three_body_position_hypothesis,
)

masses = (1.0, 1.0, 1.0)
positions = [[0.97000436, -0.24308753], [-0.97000436, 0.24308753], [0.0, 0.0]]
velocities = [[0.466203685, 0.43236573], [0.466203685, 0.43236573], [-0.93240737, -0.86473146]]

solution = solve_three_body_prediction_problem(
    masses,
    positions,
    velocities,
    target_time=0.5,
    count=64,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
direct_answer = answer_three_body_problem(
    masses,
    positions,
    velocities,
    target_time=0.5,
    count=64,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
target_answer = solve_three_body_target_positions(
    masses,
    positions,
    velocities,
    target_time=0.5,
    count=64,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
point_forecast = predict_three_body_positions(masses, positions, velocities, target_time=0.5)
ephemeris = predict_three_body_ephemeris(masses, positions, velocities, target_time=0.5, samples=256)
horizon = predict_three_body_forecast_horizon(
    masses,
    positions,
    velocities,
    target_time=0.5,
    position_tolerance=1.0e-3,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
report = predict_three_body_interpretation_report(
    masses,
    positions,
    velocities,
    target_time=0.5,
    count=64,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
linearized = predict_three_body_linearized_distribution(
    masses,
    positions,
    velocities,
    target_time=0.5,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
linearized_ephemeris = predict_three_body_linearized_ephemeris(
    masses,
    positions,
    velocities,
    target_time=0.5,
    samples=256,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
distribution = predict_three_body_position_distribution(
    masses,
    positions,
    velocities,
    target_time=0.5,
    count=64,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
distribution_ephemeris = predict_three_body_distribution_ephemeris(
    masses,
    positions,
    velocities,
    target_time=0.5,
    count=64,
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
position_score = score_three_body_position_hypothesis(
    masses,
    positions,
    velocities,
    target_time=0.5,
    candidate_positions=point_forecast["positions"],
    position_scale=1.0e-6,
    velocity_scale=1.0e-6,
)
```

`solve_three_body_target_positions` is the compact answer to the original question: it returns `target_positions`, `target_position_distribution`, one `body_answers` row per mass, a `target_position_table` with deterministic coordinates, probability mean/median, central 90% coordinate interval, 95% region radius, deterministic-to-mean gap, relative 95% radius, `position_claim_strength`, and `recommended_readout`, plus a `center_of_mass_frame` with mass-weighted center position/velocity and target positions relative to the center of mass. It also returns `target_pair_geometry`: pairwise distances, separation vectors, perimeter, triangle area, and conservative 90% pair-distance bounds from coordinate quantile boxes. `target_distribution_quality` reports Monte Carlo mean standard errors, relative sampling error, and a sampling strength label for the empirical probability answer. `target_sensitivity_budget` reports the target-time forecast horizon status, position tolerance, final propagated position standard deviation, uncertainty-to-tolerance ratio, amplification factor, Lyapunov exponent, and close-approach gate. `target_readout_decision` states whether the defensible answer is point positions with probability regions, a probability distribution, deterministic coordinates only, or unresolved, and records the diagnostic gates and per-body readout. `target_prediction_certificate` records the input contract, input SHA-256, result-payload SHA-256, claim, and recommended mode so the target answer can be reproduced and audited; `validate_three_body_target_prediction_certificate` checks that certificate against the returned payload. It records the deterministic flow definition, the probability push-forward definition, and the minimum diagnostics needed to judge whether the position/distribution claim is defensible. `solve_three_body_prediction_problem` is the full one-call solution bundle: it returns final positions, a deterministic ephemeris, linearized Gaussian ephemeris, time-resolved empirical distribution ephemeris, a time-resolved linearized-vs-empirical comparison, finite-time sensitivity diagnostics, a human-readable `prediction_summary`, a machine-readable `mathematical_statement`, and a verdict describing which mathematical forecast is defensible. The summary promotes the result as `target-position-and-distribution`, `distributional-target-position`, `deterministic-target-position`, or `unresolved-target-position`, then records the point-position statement, probability statement, reliability/risk statements, key metrics, and per-body 95% confidence regions. The mathematical statement records the Newtonian equations, flow-map readout `r_i(t) = Pi_{r_i} Phi_t(x(0))`, probability push-forward `Law(X_t) = (Phi_t)_# Law(X_0)`, linearized covariance formula, and per-body target-time claim rows. Its default uncertainty model preserves mass-weighted center-of-mass position and velocity, so the linearized Gaussian and empirical ensemble compare the same physical perturbation family. If the input JSON or API call supplies `initial_state_covariance`, that full state covariance is used by both the linearized and empirical probability paths. `predict_three_body_positions` returns the final positions, velocities, solver metadata, Noether invariant drift diagnostics, and close-approach diagnostics. `predict_three_body_ephemeris` returns the sampled positions and velocities from `0` through `target_time`, suitable for orbit tables, downstream visualization, and independent audit; when `target_times` is supplied, ephemeris modes use that exact nonuniform requested-time grid. Ephemeris outputs report the minimum sampled pair distance and whether a close-encounter/regularized chart should be considered before promoting the forecast. `predict_three_body_forecast_horizon` estimates how far the target-time forecast remains locally tolerance-resolved by propagating initial covariance through the variational flow. `predict_three_body_interpretation_report` runs the point, forecast-horizon, variational Gaussian, and ensemble modes together, compares the distributions, and recommends `linearized-gaussian`, `empirical-ensemble`, `deterministic-only`, or `unresolved`. `predict_three_body_linearized_distribution` computes the variational state-transition matrix and pushes an initial covariance forward by `P(t) = D Phi_t P(0) D Phi_t^T`; its diagnostics include singular-value uncertainty amplification and finite-time Lyapunov exponent. `score_three_body_position_hypothesis` scores a proposed target-time position against that Gaussian forecast using Mahalanobis distance, log density, and confidence-level membership. `predict_three_body_linearized_ephemeris` performs that same covariance push-forward at every sampled or explicitly requested time. `predict_three_body_position_distribution` samples either the supplied full initial covariance or the generated scale-based covariance, then returns empirical mean positions, quantiles, covariances, per-body 50/90/95/99% confidence regions, and the deterministic base forecast. `predict_three_body_distribution_ephemeris` applies the same ensemble idea at every sampled or explicitly requested time, returning a probability ephemeris instead of only a final-time distribution.

`answer_three_body_problem` is the direct theorem-facing wrapper for the same target. It returns `theorem_answer`, `position_answer`, `distribution_answer`, `body_answer_table`, `decision_protocol`, and `numerical_convergence_certificate` so the original objective is explicit: for admissible finite data, compute `r_i(t) = Pi_{r_i} Phi_t(x0)` when the target time is diagnostically resolved and a stricter reference integration agrees inside `position_tolerance`, or report `mu_t = (Phi_t)_# mu_0` when initial uncertainty dominates. 한국어로는 “임의의 삼체 초기조건과 목표시간이 주어졌을 때 각 좌표를 말할 수 있으면 좌표를 말하고, 혼돈/불확실성이 커지면 목표시간 확률분포를 말한다”는 계층이다. `body_answer_table`은 각 물체의 결정론적 좌표, 확률 평균, 중앙 90% 구간, 95% 영역, 재적분 오차, 권장 판독을 한 행에 모은다. 좌표 주장은 더 엄격한 재적분 검사가 통과할 때만 승격된다. 이 계층은 전역 초등 닫힌 해를 주장하지 않고, 유한시간 뉴턴 흐름과 push-forward 확률법칙으로 방어 가능한 답만 승격한다.

The same layer is available from the CLI:

```powershell
threebody predict --input initial-state.json --answer --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output answer.json
threebody predict --input initial-state.json --target-solution --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output target-solution.json
threebody predict --input initial-state.json --solution --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output solution.json
threebody predict --input initial-state.json --target-time 0.5 --output prediction.json
threebody predict --input initial-state.json --ephemeris --samples 256 --output ephemeris.json
threebody predict --input initial-state.json --horizon --position-tolerance 1e-3 --position-scale 1e-6 --velocity-scale 1e-6 --output horizon.json
threebody predict --input initial-state.json --report --count 128 --position-tolerance 1e-3 --position-scale 1e-6 --velocity-scale 1e-6 --output report.json
threebody predict --input initial-state.json --linearized-distribution --preserve-center-of-mass --position-scale 1e-6 --velocity-scale 1e-6 --output linearized.json
threebody predict --input initial-state.json --score-positions --preserve-center-of-mass --position-scale 1e-6 --velocity-scale 1e-6 --output position-score.json
threebody predict --input initial-state.json --linearized-ephemeris --preserve-center-of-mass --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output linearized-ephemeris.json
threebody predict --input initial-state.json --distribution --count 128 --position-scale 1e-6 --velocity-scale 1e-6 --output distribution.json
threebody predict --input initial-state.json --distribution-ephemeris --count 128 --samples 256 --position-scale 1e-6 --velocity-scale 1e-6 --output distribution-ephemeris.json
```

The hysteresis helpers accept `word_mode="refined"`, `"return"`, or `"poincare"`.
The default promotion path uses refined chart words; Poincare-section words, section sweeps, multi-coordinate sweeps, held-out binary-phase validation, permutation controls, section-robustness checks, and stride-perturbation checks as stricter diagnostics when a scenario has enough crossings.
Use `public_static_artifact_claim_contract()` to inspect the versioned public claim profile and verifier feature-set digest, then `verify_public_static_artifacts_from_url("https://eljja.github.io/3body/", require_commit="<sha>")` to audit the public Pages evidence bundle through the stable engine API. `validate_public_static_artifact_receipt_contract(receipt)` checks that a receipt matches the same public contract without requiring callers to compare individual digest fields by hand. Use `audit_public_static_artifacts_from_url(...)` when a paper supplement or CI job needs one JSON-ready object containing the contract, receipt, and receipt-contract validation.

Run the test suite:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest
```

Launch the visualizer:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m streamlit run src/threebody/ui/app.py
```

Build the static GitHub Pages visualizer:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.ui.static_site --output site
```

The static build includes a visual target-time prediction answer, research progress map, compact public claim audit chain, browser favicon, and machine-readable `certificate.json` and `manifest.json` artifacts for reproducible public review.

Verify a generated static evidence bundle:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --site-dir site --require-commit local --require-public-claim
```

Verify the public GitHub Pages evidence bundle directly:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/
```

Pin the public verification to a specific commit for reviews or paper supplements:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-commit <commit-sha-or-prefix>
```

Write a persistent verification receipt for CI logs, reviews, or paper supplements:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-commit <commit-sha-or-prefix> --output .runtime/research_runs/pages-verification-receipt.json
```

Apply the standard public claim profile when auditing the current Pages claim:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-commit <commit-sha-or-prefix> --require-public-claim --output .runtime/research_runs/pages-verification-receipt.json
```

`--require-public-claim` applies `public-claims-v1` and pins the running verifier's current capability-set digest in the receipt. The profile checks the active certificate profile name, the active profile digest, and the embedded canonical profile descriptor, not just the presence of a matching digest string.
The same verifier also checks artifact identity, the declared manifest hash algorithm, index discoverability links, publication-pipeline links, and the certificate's embedded verifier capability digest, so a receipt fails if `certificate.json` no longer declares the static research certificate, `manifest.json` no longer declares the static-site manifest with `hash_algorithm: sha256`, `index.html` stops linking the public certificate/manifest/favicon artifacts, the certificate stops pointing back to the published certificate and manifest filenames, or the certificate advertises a stale verifier capability set. Receipts include both the verifier's `verification_schema_features` / `verification_schema_features_sha256` and the certificate-advertised `certificate_verification_schema_features` / `certificate_verification_schema_features_sha256`, so mismatch failures are diagnosable without reopening the certificate file. Python callers can use `threebody_engine.verify_public_static_artifacts()`, `verify_public_static_artifacts_from_url()`, `verify_public_static_artifact_bytes()`, and `validate_public_static_artifact_receipt_contract()` for the same public profile and verifier capability-set pin. Lower-level callers can still pass `require_public_claim=True` to the raw verifier helpers, repeat `--require-feature <name>`, pass `--require-feature-set-sha256 <digest>`, or use `--require-current-feature-set` for targeted audits. Missing local files, fetch failures, missing direct byte inputs, invalid JSON, and malformed nested provenance/artifact sections are reported as failed receipt checks, and commit provenance only passes when both artifacts declare the same non-empty commit string.

`public-claims-v1` expands to the current publication gates, numeric lower and upper bounds, and required verifier capabilities used for the public certificate.
The certificate and receipt also include the profile's canonical SHA-256 digest so reviewers can confirm the profile name and profile definition match.

Require specific scientific promotion gates when auditing a public claim:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-commit <commit-sha-or-prefix> --require-gate picard_certified --require-gate symbolic_passes_stride_robustness --output .runtime/research_runs/pages-verification-receipt.json
```

Require numeric certificate thresholds as well:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/ --require-commit <commit-sha-or-prefix> --require-min publication_pipeline.promotion_gate_pass_count=7 --require-min promotion_gates.picard_contraction_reserve=0 --require-max metrics.picard_max_contraction=0.35
```

Use `--require-min` for quantities that must be large enough, such as pass counts or robustness fractions, and `--require-max` for quantities that must stay small, such as Picard contraction and invariant drift.

Run a transition survey:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.cli survey --scenario hierarchical-flyby --count 16 --validation-count 16 --periods 8 --samples 1200 --stride 20
```

## Documentation

- [Project Scope](docs/PROJECT_SCOPE.md)
- [Paper-Readiness Review](docs/PAPER_READINESS_REVIEW.md)
- [Science Foundation](docs/SCIENCE_FOUNDATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Research Program](docs/RESEARCH_PROGRAM.md)
- [Research Runs](docs/RESEARCH_RUNS.md)
- [Current Hypotheses](docs/CURRENT_HYPOTHESES.md)
- [Jacobi Escape Cone Theorem](docs/JACOBI_ESCAPE_CONE_THEOREM.md)
- [Theorem Candidates](docs/THEOREM_CANDIDATES.md)
- [Interpretation Method](docs/INTERPRETATION_METHOD.md)
- [Prediction Method](docs/PREDICTION_METHOD.md)
- [Random Three-Body Demo](docs/RANDOM_THREE_BODY_DEMO.md)
- [Global Closed-Form Program](docs/GLOBAL_CLOSED_FORM_PROGRAM.md)
- [Literature Comparison](docs/LITERATURE_COMPARISON.md)
- [Solution Space](docs/SOLUTION_SPACE.md)
- [Validation Guardrails](docs/VALIDATION_GUARDRAILS.md)
- [Strategic Review](docs/STRATEGIC_REVIEW.md)
- [Local Changes Audit](docs/LOCAL_CHANGES_AUDIT.md)
- [GitHub Pages Static Visualizer](docs/GITHUB_PAGES.md)
- [Roadmap](docs/ROADMAP.md)

## Suggested Workflow

1. Use the simulator to generate trusted trajectories and invariant diagnostics.
2. Classify each trajectory segment into an analysis chart.
3. Apply the chart-specific method: Kepler reduction, restricted manifolds, regularization, continuation, sections, or local linearization.
4. Record where chart transitions occur and build reduced models only inside validated chart domains.
