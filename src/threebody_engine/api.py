from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

from threebody.analysis import (
    AnalysisAtlas,
    ChartWordMarkovChain,
    ChartWordMarkovBaselineComparison,
    ChartWordMarkovBootstrapComparison,
    ChartWordMarkovValidation,
    ChartWordMarkovOrderSelection,
    bootstrap_markov_baseline_comparison,
    JacobiIntervalPicardFlowCertificate,
    JacobiPicardTuningCertificate,
    compare_markov_chain_to_independent_baseline,
    jacobi_interval_picard_flow_certificate,
    jacobi_picard_tuning_certificate,
    markov_chain_from_words,
    permutation_control_markov_validation,
    poincare_markov_section_robustness,
    poincare_coordinate_sweep_from_reports,
    poincare_section_sweep_from_reports,
    poincare_section_word_from_reports,
    refined_chart_word_from_reports,
    return_map_word_from_reports,
    select_markov_order,
    validate_markov_chain,
)
from threebody.cli import (
    PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE,
    STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES,
    static_artifact_receipt_payload_sha256,
    static_artifact_requirement_profile_descriptor,
    static_artifact_requirement_profile_sha256,
    static_artifact_verification_features_sha256,
    verify_static_artifact_bytes,
    verify_static_artifacts,
    verify_static_artifacts_from_url,
)
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.types import Scenario, TrajectoryResult

ReferenceScenario = Literal["figure-eight", "hierarchical-flyby", "restricted-l4", "restricted-l5"]
WordMode = Literal["refined", "return", "poincare"]


def public_static_artifact_claim_contract() -> dict[str, object]:
    """Return the JSON-ready public Pages claim profile and verifier feature contract."""

    profile = PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE
    verification_schema_features = list(STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    return {
        "contract_schema_version": 1,
        "profile": profile,
        "profile_sha256": static_artifact_requirement_profile_sha256(profile),
        "profile_descriptor": static_artifact_requirement_profile_descriptor(profile),
        "verification_schema_features": verification_schema_features,
        "verification_schema_features_sha256": static_artifact_verification_features_sha256(
            verification_schema_features
        ),
    }


def validate_public_static_artifact_receipt_contract(
    receipt: Mapping[str, object],
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Check whether a verifier receipt satisfies the stable public Pages claim contract."""

    contract = contract or public_static_artifact_claim_contract()
    profile = contract.get("profile")
    profile_sha256 = contract.get("profile_sha256")
    feature_set_sha256 = contract.get("verification_schema_features_sha256")
    required_profile_hashes = _mapping_field(receipt, "required_profile_hashes")
    receipt_payload_sha256 = receipt.get("receipt_payload_sha256")
    checks = {
        "receipt_verified": receipt.get("verified") is True,
        "receipt_payload_sha256_present": isinstance(receipt_payload_sha256, str) and len(receipt_payload_sha256) == 64,
        "receipt_payload_sha256_matches": receipt_payload_sha256 == static_artifact_receipt_payload_sha256(receipt),
        "required_profile_declared": profile in _sequence_field(receipt, "required_profiles"),
        "required_profile_hash_matches": required_profile_hashes.get(profile) == profile_sha256,
        "required_feature_set_sha256_matches": receipt.get("required_feature_set_sha256") == feature_set_sha256,
        "receipt_feature_set_sha256_matches": receipt.get("verification_schema_features_sha256") == feature_set_sha256,
        "certificate_feature_set_sha256_matches": receipt.get("certificate_verification_schema_features_sha256")
        == feature_set_sha256,
        "profile_hash_check_passed": _mapping_field(receipt, "checks").get("required_profile_hashes") is True,
        "feature_set_check_passed": _mapping_field(receipt, "checks").get("required_feature_set_sha256") is True,
    }
    return {
        "contract_schema_version": contract.get("contract_schema_version"),
        "profile": profile,
        "profile_sha256": profile_sha256,
        "verification_schema_features_sha256": feature_set_sha256,
        "receipt_payload_sha256": receipt_payload_sha256,
        "verified": all(checks.values()),
        "checks": checks,
    }


def verify_public_static_artifacts(
    site_dir: str | Path,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Verify a generated static evidence directory against the public claim profile."""

    return verify_static_artifacts(
        Path(site_dir),
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=True,
    )


def audit_public_static_artifacts(
    site_dir: str | Path,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Return a self-contained public Pages audit report for a generated static directory."""

    receipt = verify_public_static_artifacts(
        site_dir,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
    )
    return _public_static_artifact_audit_report(receipt)


def verify_public_static_artifacts_from_url(
    base_url: str,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Verify a public static evidence bundle URL against the public claim profile."""

    return verify_static_artifacts_from_url(
        base_url,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=True,
    )


def audit_public_static_artifacts_from_url(
    base_url: str,
    *,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Return a self-contained public Pages audit report for a public static URL."""

    receipt = verify_public_static_artifacts_from_url(
        base_url,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
    )
    return _public_static_artifact_audit_report(receipt)


def verify_public_static_artifact_bytes(
    artifacts: dict[str, bytes],
    *,
    source: str = "direct-bytes",
    artifact_errors: dict[str, str | None] | None = None,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Verify in-memory static evidence artifacts against the public claim profile."""

    return verify_static_artifact_bytes(
        artifacts,
        source=source,
        artifact_errors=artifact_errors,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=True,
    )


def audit_public_static_artifact_bytes(
    artifacts: dict[str, bytes],
    *,
    source: str = "direct-bytes",
    artifact_errors: dict[str, str | None] | None = None,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
) -> dict[str, object]:
    """Return a self-contained public Pages audit report for in-memory static artifacts."""

    receipt = verify_public_static_artifact_bytes(
        artifacts,
        source=source,
        artifact_errors=artifact_errors,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
    )
    return _public_static_artifact_audit_report(receipt)


def _public_static_artifact_audit_report(receipt: Mapping[str, object]) -> dict[str, object]:
    contract = public_static_artifact_claim_contract()
    receipt_contract_validation = validate_public_static_artifact_receipt_contract(receipt, contract)
    return {
        "audit_schema_version": 1,
        "verified": receipt.get("verified") is True and receipt_contract_validation["verified"] is True,
        "contract": contract,
        "receipt": dict(receipt),
        "receipt_contract_validation": receipt_contract_validation,
    }


def _mapping_field(payload: Mapping[str, object], key: str) -> Mapping[object, object]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _sequence_field(payload: Mapping[str, object], key: str) -> tuple[object, ...]:
    value = payload.get(key)
    if isinstance(value, str) or not isinstance(value, Sequence):
        return ()
    return tuple(value)


def integrate_reference_scenario(
    scenario: ReferenceScenario = "hierarchical-flyby",
    *,
    periods: float = 0.25,
    samples: int = 240,
    rtol: float = 1.0e-9,
    atol: float = 1.0e-11,
) -> tuple[Scenario, TrajectoryResult]:
    """Integrate a built-in benchmark scenario through the engine API."""

    library = OrbitLibrary()
    reference = _reference_scenario(library, scenario, periods=periods, samples=samples)
    trajectory = AdaptiveIntegrator(rtol=rtol, atol=atol).integrate(
        reference.system,
        reference.t_span,
        reference.initial_state,
        t_eval=reference.t_eval,
    )
    return reference, trajectory


def certify_jacobi_escape(
    trajectory: TrajectoryResult,
    scenario: Scenario,
    *,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> JacobiIntervalPicardFlowCertificate:
    """Run the Picard-certified Jacobi escape certificate for a solved trajectory."""

    return jacobi_interval_picard_flow_certificate(
        scenario.system,
        trajectory,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )


def tune_jacobi_picard(
    trajectory: TrajectoryResult,
    scenario: Scenario,
    *,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> JacobiPicardTuningCertificate:
    """Auto-select Picard settings for a solved trajectory."""

    return jacobi_picard_tuning_certificate(
        scenario.system,
        trajectory,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )


def certify_jacobi_escape_report(
    trajectory: TrajectoryResult,
    scenario: Scenario,
    *,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
) -> dict[str, object]:
    """Return a JSON-ready Picard tuning and escape certificate report."""

    tuning = tune_jacobi_picard(
        trajectory,
        scenario,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )
    certificate = certify_jacobi_escape(
        trajectory,
        scenario,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )
    return {
        "scenario": scenario.name,
        "picard_tuning": tuning.as_dict(),
        "jacobi_escape_certificate": certificate.as_dict(),
    }


def build_hysteresis_markov_chain(
    scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
) -> ChartWordMarkovChain:
    """Build a symbolic Markov model from refined, return-map, or Poincare-section chart words."""

    atlas = AnalysisAtlas()
    words = []
    for scenario_name in scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return markov_chain_from_words(tuple(words))


def validate_hysteresis_markov_chain(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
) -> tuple[ChartWordMarkovChain, ChartWordMarkovValidation]:
    """Fit and validate a hysteresis symbolic Markov model."""

    chain = build_hysteresis_markov_chain(
        train_scenarios,
        periods=periods,
        samples=samples,
        stride=stride,
        coordinate=coordinate,
        word_mode=word_mode,
    )
    atlas = AnalysisAtlas()
    heldout_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        heldout_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return chain, validate_markov_chain(chain, tuple(heldout_words))


def compare_hysteresis_markov_to_baseline(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
) -> tuple[ChartWordMarkovChain, ChartWordMarkovBaselineComparison]:
    """Fit hysteresis Markov dynamics and compare against an independent baseline."""

    atlas = AnalysisAtlas()
    training_words = []
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        training_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    chain = markov_chain_from_words(tuple(training_words))
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return chain, compare_markov_chain_to_independent_baseline(
        chain,
        tuple(training_words),
        tuple(validation_words),
    )


def compare_hysteresis_markov_to_baseline_with_uncertainty(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
    resamples: int = 512,
    confidence_level: float = 0.95,
    random_seed: int = 0,
) -> tuple[ChartWordMarkovChain, ChartWordMarkovBootstrapComparison]:
    """Fit hysteresis Markov dynamics and bootstrap its baseline gain."""

    atlas = AnalysisAtlas()
    training_words = []
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        training_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    chain = markov_chain_from_words(tuple(training_words))
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return chain, bootstrap_markov_baseline_comparison(
        chain,
        tuple(training_words),
        tuple(validation_words),
        resamples=resamples,
        confidence_level=confidence_level,
        random_seed=random_seed,
    )


def select_hysteresis_markov_order(
    train_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    validation_scenarios: tuple[ReferenceScenario, ...] = ("hierarchical-flyby",),
    *,
    periods: float = 8.0,
    samples: int = 240,
    stride: int = 20,
    coordinate: str = "hierarchy_perturbation_strength",
    word_mode: WordMode = "refined",
    max_order: int = 2,
    criterion: str = "bic",
) -> ChartWordMarkovOrderSelection:
    """Select independent, first-order, or higher-order hysteresis memory depth."""

    atlas = AnalysisAtlas()
    training_words = []
    for scenario_name in train_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        training_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    validation_words = []
    for scenario_name in validation_scenarios:
        scenario, trajectory = integrate_reference_scenario(
            scenario_name,
            periods=periods,
            samples=samples,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=stride)
        validation_words.append(_hysteresis_word_from_reports(reports, coordinate=coordinate, word_mode=word_mode))
    return select_markov_order(
        tuple(training_words),
        tuple(validation_words),
        max_order=max_order,
        criterion=criterion,
    )


def run_verification_report(
    *,
    scenario: ReferenceScenario = "hierarchical-flyby",
    periods: float = 8.0,
    samples: int = 500,
    stride: int = 20,
    inner_pair: tuple[int, int] = (0, 1),
    target_contraction: float = 0.35,
    word_mode: WordMode = "refined",
) -> dict[str, object]:
    """Return a JSON-ready end-to-end engine verification report."""

    reference, trajectory = integrate_reference_scenario(
        scenario,
        periods=periods,
        samples=samples,
    )
    jacobi_report = certify_jacobi_escape_report(
        trajectory,
        reference,
        inner_pair=inner_pair,
        target_contraction=target_contraction,
    )
    atlas = AnalysisAtlas()
    reports = atlas.analyze_trajectory(reference.system, trajectory, stride=stride)
    heldout_training_runs = _heldout_phase_training_runs(
        scenario,
        periods=periods,
        samples=samples,
    )
    heldout_training_reports = tuple(
        atlas.analyze_trajectory(system, phase_trajectory, stride=stride)
        for system, phase_trajectory in heldout_training_runs
    )
    if heldout_training_reports:
        training_words = tuple(
            _hysteresis_word_from_reports(report_set, coordinate="hierarchy_perturbation_strength", word_mode=word_mode)
            for report_set in heldout_training_reports
        )
        validation_words = (
            _hysteresis_word_from_reports(reports, coordinate="hierarchy_perturbation_strength", word_mode=word_mode),
        )
        chain = markov_chain_from_words(training_words)
        bootstrap_comparison = bootstrap_markov_baseline_comparison(
            chain,
            training_words,
            validation_words,
            resamples=512,
            random_seed=0,
        )
        order_selection = select_markov_order(training_words, validation_words, max_order=2)
        validation_mode = "heldout_binary_phase"
    else:
        chain, bootstrap_comparison = compare_hysteresis_markov_to_baseline_with_uncertainty(
            (scenario,),
            (scenario,),
            periods=periods,
            samples=samples,
            stride=stride,
            word_mode=word_mode,
        )
        order_selection = select_hysteresis_markov_order(
            (scenario,),
            (scenario,),
            periods=periods,
            samples=samples,
            stride=stride,
            word_mode=word_mode,
        )
        validation_mode = "self_reference"
    poincare_sweep = poincare_section_sweep_from_reports(
        reports,
        coordinate="hierarchy_perturbation_strength",
    )
    section_source_reports = heldout_training_reports[0] if heldout_training_reports else reports
    poincare_coordinate_sweep = poincare_coordinate_sweep_from_reports(section_source_reports)
    poincare_training_words = tuple(
        _poincare_word_from_sweep(report_set, poincare_coordinate_sweep)
        for report_set in (heldout_training_reports or (reports,))
    )
    poincare_validation_words = (_poincare_word_from_sweep(reports, poincare_coordinate_sweep),)
    poincare_chain = markov_chain_from_words(poincare_training_words)
    poincare_bootstrap = bootstrap_markov_baseline_comparison(
        poincare_chain,
        poincare_training_words,
        poincare_validation_words,
        resamples=512,
        random_seed=17,
    )
    poincare_order_selection = select_markov_order(poincare_training_words, poincare_validation_words, max_order=2)
    poincare_permutation_control = permutation_control_markov_validation(
        poincare_chain,
        poincare_validation_words,
        permutations=512,
        random_seed=29,
    )
    poincare_section_robustness = poincare_markov_section_robustness(
        heldout_training_reports or (tuple(reports),),
        poincare_coordinate_sweep.best,
        validation_report_sets=(tuple(reports),) if heldout_training_reports else None,
        resamples=128,
        permutations=128,
        random_seed=37,
        minimum_pass_count=1,
        minimum_pass_fraction=0.1,
    )
    symbolic_stride_robustness = _symbolic_stride_robustness(
        atlas,
        validation_run=(reference.system, trajectory),
        training_runs=heldout_training_runs,
        stride_values=_stride_probe_values(stride),
        word_mode=word_mode,
    )
    comparison = bootstrap_comparison.comparison
    return {
        "metadata": {
            "report_schema_version": 2,
            "engine": "threebody-engine",
            "scenario": reference.name,
            "source_scenario": scenario,
            "periods": periods,
            "samples": samples,
            "stride": stride,
            "target_contraction": target_contraction,
            "word_mode": word_mode,
            "random_seeds": {
                "hysteresis_bootstrap": 11,
                "poincare_bootstrap": 29,
                "poincare_permutation_control": 37,
                "symbolic_stride_robustness": 43,
            },
        },
        "jacobi": jacobi_report,
        "hysteresis_markov": {
            "chain": chain.as_dict(),
            "baseline_comparison": comparison.as_dict(),
            "bootstrap_comparison": bootstrap_comparison.as_dict(),
            "order_selection": order_selection.as_dict(),
            "validation_mode": validation_mode,
            "poincare_section_sweep": poincare_sweep.as_dict(),
            "poincare_coordinate_sweep": poincare_coordinate_sweep.as_dict(),
            "poincare_markov": {
                "training_word_lengths": [word.length for word in poincare_training_words],
                "validation_word_lengths": [word.length for word in poincare_validation_words],
                "validation_mode": validation_mode,
                "chain": poincare_chain.as_dict(),
                "bootstrap_comparison": poincare_bootstrap.as_dict(),
                "order_selection": poincare_order_selection.as_dict(),
                "permutation_control": poincare_permutation_control.as_dict(),
                "section_robustness": poincare_section_robustness.as_dict(),
                "stride_robustness": symbolic_stride_robustness,
            },
        },
        "promotion_gates": {
            "picard_certified": bool(jacobi_report["picard_tuning"]["certified"]),
            "picard_contraction_reserve": jacobi_report["picard_tuning"]["contraction_reserve"],
            "hysteresis_beats_independent_baseline": comparison.beats_baseline,
            "hysteresis_significant_baseline_win": bootstrap_comparison.significant_baseline_win,
            "hysteresis_log_likelihood_gain": comparison.log_likelihood_gain,
            "hysteresis_log_likelihood_gain_ci": list(bootstrap_comparison.log_likelihood_gain_ci),
            "hysteresis_selected_markov_order": order_selection.selected_order,
            "hysteresis_memory_order_selected": order_selection.memory_selected,
            "poincare_has_sufficient_section": poincare_sweep.has_sufficient_section,
            "poincare_best_crossing_count": poincare_sweep.best.crossing_count,
            "poincare_coordinate_has_sufficient_section": poincare_coordinate_sweep.has_sufficient_section,
            "poincare_best_coordinate": poincare_coordinate_sweep.best.coordinate,
            "poincare_best_coordinate_crossing_count": poincare_coordinate_sweep.best.best.crossing_count,
            "poincare_markov_significant_baseline_win": poincare_bootstrap.significant_baseline_win,
            "poincare_markov_log_likelihood_gain_ci": list(poincare_bootstrap.log_likelihood_gain_ci),
            "poincare_selected_markov_order": poincare_order_selection.selected_order,
            "poincare_memory_order_selected": poincare_order_selection.memory_selected,
            "poincare_heldout_phase_validation": bool(heldout_training_reports),
            "poincare_passes_permutation_control": poincare_permutation_control.passes_permutation_control,
            "poincare_permutation_control_gap": poincare_permutation_control.actual_minus_control,
            "poincare_section_robust_pass_count": poincare_section_robustness.pass_count,
            "poincare_section_robust_pass_fraction": poincare_section_robustness.pass_fraction,
            "poincare_passes_section_robustness": poincare_section_robustness.passes_robustness,
            "symbolic_stride_robust_pass_count": symbolic_stride_robustness["pass_count"],
            "symbolic_stride_robust_pass_fraction": symbolic_stride_robustness["pass_fraction"],
            "symbolic_passes_stride_robustness": symbolic_stride_robustness["passes_stride_robustness"],
        },
    }


def _hysteresis_word_from_reports(
    reports: tuple[object, ...],
    *,
    coordinate: str,
    word_mode: WordMode,
):
    if word_mode == "refined":
        return refined_chart_word_from_reports(reports)
    if word_mode == "return":
        return return_map_word_from_reports(reports, coordinate=coordinate)
    if word_mode == "poincare":
        return poincare_section_word_from_reports(reports, coordinate=coordinate)
    raise ValueError("word_mode must be 'refined', 'return', or 'poincare'.")


def _heldout_phase_training_runs(
    scenario: ReferenceScenario,
    *,
    periods: float,
    samples: int,
) -> tuple[tuple[object, TrajectoryResult], ...]:
    if scenario != "hierarchical-flyby":
        return ()
    library = OrbitLibrary()
    integrator = AdaptiveIntegrator()
    runs = []
    for binary_phase in (0.5 * math.pi, math.pi):
        phase_scenario = library.general_hierarchical_flyby(
            binary_phase=binary_phase,
            intruder_velocity=(0.8, 1.6),
            duration=periods,
            samples=samples,
        )
        phase_trajectory = integrator.integrate(
            phase_scenario.system,
            phase_scenario.t_span,
            phase_scenario.initial_state,
            t_eval=phase_scenario.t_eval,
        )
        runs.append((phase_scenario.system, phase_trajectory))
    return tuple(runs)


def _stride_probe_values(base_stride: int) -> tuple[int, ...]:
    base = max(int(base_stride), 1)
    return tuple(sorted({max(1, int(round(0.8 * base))), base, max(1, int(round(1.5 * base)))}))


def _symbolic_stride_robustness(
    atlas: AnalysisAtlas,
    *,
    validation_run: tuple[object, TrajectoryResult],
    training_runs: tuple[tuple[object, TrajectoryResult], ...],
    stride_values: tuple[int, ...],
    word_mode: WordMode,
) -> dict[str, object]:
    if not training_runs:
        return {
            "stride_values": [int(stride) for stride in stride_values],
            "evaluated_count": 0,
            "pass_count": 0,
            "pass_fraction": 0.0,
            "minimum_pass_fraction": 1.0,
            "passes_stride_robustness": False,
            "candidates": [],
        }
    rows = []
    for index, stride in enumerate(stride_values):
        validation_reports = atlas.analyze_trajectory(validation_run[0], validation_run[1], stride=stride)
        training_reports = tuple(
            atlas.analyze_trajectory(system, trajectory, stride=stride)
            for system, trajectory in training_runs
        )
        training_words = tuple(
            _hysteresis_word_from_reports(
                report_set,
                coordinate="hierarchy_perturbation_strength",
                word_mode=word_mode,
            )
            for report_set in training_reports
        )
        validation_word = _hysteresis_word_from_reports(
            validation_reports,
            coordinate="hierarchy_perturbation_strength",
            word_mode=word_mode,
        )
        chain = markov_chain_from_words(training_words)
        bootstrap = bootstrap_markov_baseline_comparison(
            chain,
            training_words,
            (validation_word,),
            resamples=64,
            random_seed=101 + index,
        )
        order_selection = select_markov_order(training_words, (validation_word,), max_order=2)
        coordinate_sweep = poincare_coordinate_sweep_from_reports(training_reports[0])
        poincare_training_words = tuple(_poincare_word_from_sweep(report_set, coordinate_sweep) for report_set in training_reports)
        poincare_validation_words = (_poincare_word_from_sweep(validation_reports, coordinate_sweep),)
        poincare_chain = markov_chain_from_words(poincare_training_words)
        poincare_bootstrap = bootstrap_markov_baseline_comparison(
            poincare_chain,
            poincare_training_words,
            poincare_validation_words,
            resamples=64,
            random_seed=151 + index,
        )
        poincare_order = select_markov_order(poincare_training_words, poincare_validation_words, max_order=2)
        permutation = permutation_control_markov_validation(
            poincare_chain,
            poincare_validation_words,
            permutations=64,
            random_seed=181 + index,
        )
        section_robustness = poincare_markov_section_robustness(
            training_reports,
            coordinate_sweep.best,
            validation_report_sets=(validation_reports,),
            resamples=32,
            permutations=32,
            random_seed=211 + index,
            minimum_pass_count=1,
            minimum_pass_fraction=0.1,
        )
        passes = bool(
            bootstrap.significant_baseline_win
            and order_selection.memory_selected
            and coordinate_sweep.has_sufficient_section
            and poincare_bootstrap.significant_baseline_win
            and poincare_order.memory_selected
            and permutation.passes_permutation_control
            and section_robustness.passes_robustness
        )
        rows.append(
            {
                "stride": int(stride),
                "hysteresis_significant_baseline_win": bootstrap.significant_baseline_win,
                "hysteresis_memory_order_selected": order_selection.memory_selected,
                "poincare_best_coordinate": coordinate_sweep.best.coordinate,
                "poincare_best_crossing_count": coordinate_sweep.best.best.crossing_count,
                "poincare_training_word_lengths": [word.length for word in poincare_training_words],
                "poincare_validation_word_length": poincare_validation_words[0].length,
                "poincare_markov_significant_baseline_win": poincare_bootstrap.significant_baseline_win,
                "poincare_memory_order_selected": poincare_order.memory_selected,
                "poincare_passes_permutation_control": permutation.passes_permutation_control,
                "poincare_passes_section_robustness": section_robustness.passes_robustness,
                "passes": passes,
            }
        )
    pass_count = sum(1 for row in rows if row["passes"])
    evaluated_count = len(rows)
    pass_fraction = float(pass_count / evaluated_count) if evaluated_count else 0.0
    return {
        "stride_values": [int(stride) for stride in stride_values],
        "evaluated_count": evaluated_count,
        "pass_count": pass_count,
        "pass_fraction": pass_fraction,
        "minimum_pass_fraction": 1.0,
        "passes_stride_robustness": bool(evaluated_count > 0 and pass_fraction >= 1.0),
        "candidates": rows,
    }


def _poincare_word_from_sweep(reports: tuple[object, ...], sweep: object):
    return poincare_section_word_from_reports(
        reports,
        coordinate=sweep.best.coordinate,
        section_value=sweep.best.best.section_value,
        direction=sweep.best.direction,
    )


def _reference_scenario(
    library: OrbitLibrary,
    scenario: ReferenceScenario,
    *,
    periods: float,
    samples: int,
) -> Scenario:
    if scenario == "figure-eight":
        return library.general_figure_eight(periods=periods, samples=samples)
    if scenario == "hierarchical-flyby":
        return library.general_hierarchical_flyby(
            intruder_velocity=(0.8, 1.6),
            duration=periods,
            samples=samples,
        )
    if scenario == "restricted-l4":
        return library.restricted_l4(periods=periods, samples=samples)
    if scenario == "restricted-l5":
        return library.restricted_l5(periods=periods, samples=samples)
    raise ValueError(f"Unknown reference scenario: {scenario}")
