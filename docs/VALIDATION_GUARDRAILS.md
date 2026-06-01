# Validation Guardrails

This file defines what the project is not allowed to claim yet.
It is authoritative for README, docs, GitHub Pages copy, and paper-facing text.

이 문서는 README, docs, GitHub Pages 문구, 논문 제출용 문장에 적용되는
최상위 claim guardrail입니다.

## Current Proof Level

The project has an empirical atlas and falsification harness.
It does not have a global solution of the Newtonian three-body problem.
It also does not yet have theorem-level error bounds for every chart.
In this repository, "certificate" means a structured audit record unless the
same paragraph explicitly states that a validated-flow proof has been completed.
한국어 기준으로도 "certificate/인증서"는 기본적으로 감사 가능한 산출물이며,
검증된 flow enclosure가 명시되지 않으면 수학적 증명을 뜻하지 않는다.
`threebody theorem-suite` runs quick development checks by default.
Paper-facing Jacobi parameter-box claims require `threebody theorem-suite --mode paper`.

Allowed claims / 허용되는 주장:

- A benchmark trajectory belongs to a chart under the current classifier.
- A proposed transition model reduced held-out scatter inside a declared benchmark family.
- A compact model is provisional unless it survives held-out sweeps, artifact checks, and invariant-drift checks.
- A finite-time target-position or probability-distribution answer is admissible only for finite input data, declared uncertainty, solver tolerances, and diagnostic gates.
- A seeded random demo is evidence for that seeded admissible harness, not for universal random-input solvability.

허용되는 주장의 한국어 기준:

- benchmark trajectory가 현재 classifier 기준으로 특정 chart에 속한다.
- 제안된 transition model이 선언된 benchmark family 내부의 held-out scatter를 줄였다.
- compact model은 held-out sweep, artifact check, invariant-drift check를 통과하기 전까지 provisional이다.
- 유한시간 목표 위치/확률분포 답변은 유한 입력자료, 선언된 불확실성, solver tolerance, diagnostic gate가 함께 있을 때만 허용된다.
- seed 고정 random demo는 그 seed와 admissible harness에 대한 증거이지 보편 random-input solvability의 증거가 아니다.

Forbidden claims / 금지되는 주장:

- General three-body closed-form solution.
- Universal transition threshold across all masses, energies, and angular momenta.
- Close-encounter law without a true regularized integrator or equivalent collision chart.
- Lagrange-neck transport law before the gateway classifier beats the generic Lagrange-neighborhood classifier.
- Exact Newtonian theorem statements based on softened or regularized numerical equations unless the softening/regularization is explicitly part of the theorem.

금지되는 주장의 한국어 기준:

- 일반 삼체 문제의 전역 닫힌형 해.
- 모든 질량, 에너지, 각운동량에 대한 보편 transition threshold.
- 진짜 regularized integrator 또는 동등한 collision chart 없는 close-encounter law.
- gateway classifier가 generic Lagrange-neighborhood classifier를 이기기 전의 Lagrange-neck transport law.
- softening/regularization이 정리의 일부로 명시되지 않은 상태에서 softened/regularized 수치 방정식 결과를 정확한 Newtonian theorem으로 표현하는 것.

## Required Checks Before Promoting A Law

- Held-out validation: report validation CV or error, not only training fit.
- Model selection: report feature count, AIC, BIC, leave-one-out error, or bootstrap/OOB error where sample count allows it.
- Classifier artifact: rerun with threshold and stride perturbations.
- Integrator artifact: compare adaptive and structure-aware integration and inspect invariant drift.
- Benchmark anchoring: pass known reference scenarios relevant to the chart.
- Scope declaration: name the regime where the model is valid and explicitly reject extrapolation outside it.

## Current Gaps

- `AnalysisReport` now carries `ReducedThreeBodyState` snapshots for general three-body classifier outputs, so downstream models can read the shared shape-scale coordinates without recomputing them. The main classifier scoring still partly uses older feature objects, so any scoring migration must remain gradual and tested against existing chart labels.
- Periapsis phase is now measured from the trajectory, and the first `scattering_map` collapse includes periapsis distance and deflection angle. The scattering diagnostic now also reports outgoing semimajor axis, eccentricity, periapsis distance, and escape speed at infinity.
- The stricter `theorem-suite` currently does not reproduce the low-crossing scattering-map win from the smaller smoke run. This blocks any promoted novelty claim based on that model.
- The current `theorem-suite` partially supports `low_crossing_impulse`, but the high-crossing best model does not yet pass the paper threshold. A two-sided hierarchy-boundary theorem is not justified.
- Hysteresis-width collapse also fails in the theorem harness, so re-entry should not be forced into a scalar boundary model. The current admissible target is a chart-sequence/return-map branch model, and it must be reported separately from scalar boundary collapse.
- Branch models must report their predeclared feature protocol, discovery leave-one-out accuracy, baseline accuracy, and held-out validation accuracy. Do not select branch features by held-out validation score.
- Branch promotion requires both a positive discovery leave-one-out signal and a wider held-out phase sweep; held-out accuracy alone is not sufficient.
- Branch promotion also requires classifier-threshold and stride perturbation robustness. A branch law that only works for one atlas setting remains an artifact candidate.
- Binary grammar branch validation uses a lower score threshold than scalar boundary collapse because it is a quantile-branch classifier, not a continuous boundary fit. The current threshold is `0.18` after complexity penalty.
- Branch claims must report positive-margin certified accuracy and certified fraction. Accuracy without decision margin is not enough for theorem promotion.
- Branch margin certificates must also survive classifier-threshold and stride perturbations.
- Branch laws must beat negative controls computed on the same held-out split: feature-only nearest-neighbor classification and deterministically permuted chart-word classification.
- If only one branch beats these controls, the theorem candidate must split by branch instead of promoting a unified grammar law.
- The theorem suite must report which explanation wins per branch. A feature-selected branch and a grammar-selected branch are not the same theorem.
- `Chart-Word Grammar` now separates the coarse alphabet from a refined physical alphabet. Refined word diversity survives the current held-out flyby harness, but this is still a symbolic proxy. It cannot be promoted until classifier perturbations and a genuine Poincare/return-map construction agree with the refined words.
- AIC, BIC, leave-one-out, and bootstrap/OOB diagnostics exist for flyby collapse fits, but the sample count is still small.
- A true regularized collision integrator is missing, but a McGehee-style scale/shape collision diagnostic now separates hyperradius, radial velocity, shape area, anisotropy, and collision depth.
- Lagrange gateway transport now has a linearized L1/L2/L3 transit estimate based on neck openness and stable/unstable eigendirection projection. It is not yet a full invariant-manifold computation.
- Shape-space close encounter support is currently a diagnostic blow-up coordinate, not a fully regularized flow.
- Escape scattering is detected as a regime, but outgoing asymptotic Kepler-element convergence is not yet enforced.
- Jacobi escape now has a local interval-arithmetic tail-state certificate, an a posteriori interval RHS flow-tube check, and segment-wise Picard propagation of interval start boxes with an interval Newtonian RHS Jacobian contraction bound. This is stronger than scalar margin inflation and finite-difference terminal reserve, but it is not yet an independent CAPD-grade proof. Claims must say "segment-wise interval Picard certified over the sampled Jacobi tail" unless interval parameters and the full initial-value problem are propagated by a production validated integrator.
- Jacobi Picard claims must state whether the final margin uses the sampled defect-tube radius or the propagated endpoint enclosure radius. Paper-facing rows must use the propagated endpoint radius.
- Jacobi representative-tail claims must also report the Picard resolution/tolerance crosscheck. Passing one adaptive-integrator output is not enough to argue that the local cone is independent of solver settings.
- Jacobi parameter-box claims may cite the continuum-style reserve only as a finite-difference reserve over Picard-certified margins. They must not call it a rigorous interval-parameter derivative bound until mass, velocity, phase, and tail-state derivatives are interval-enclosed.
- Jacobi parameter-box promotion must include the parameter-cell midpoint, face-center, and edge-center checks. Passing only the grid nodes is no longer sufficient for paper-facing claims.
- Jacobi parameter-box promotion must also report the 5x5x5 half-grid reserve. The original 3x3x3 reserve is no longer sufficient on its own.
- Jacobi paper-mode promotion must report the 64 local half-grid subcell reserves. A single global half-grid reserve is no longer sufficient on its own.
