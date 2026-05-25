from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

import numpy as np
from scipy.integrate import solve_ivp

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
    finite_difference_jacobian,
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
from threebody.diagnostics import noether_invariant_drift_certificate
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.systems import GeneralThreeBodySystem
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


def public_static_artifact_audit_report_payload_sha256(audit_report: Mapping[str, object]) -> str:
    """Return a timestamp-independent canonical SHA-256 for a public Pages audit report."""

    payload = _audit_report_digest_payload(audit_report)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


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
    report = {
        "audit_schema_version": 1,
        "verified": receipt.get("verified") is True and receipt_contract_validation["verified"] is True,
        "contract": contract,
        "receipt": dict(receipt),
        "receipt_contract_validation": receipt_contract_validation,
    }
    report["audit_payload_sha256"] = public_static_artifact_audit_report_payload_sha256(report)
    return report


def _audit_report_digest_payload(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _audit_report_digest_payload(item)
            for key, item in value.items()
            if key not in {"audit_payload_sha256", "verified_at_utc"}
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_audit_report_digest_payload(item) for item in value]
    return value


def _mapping_field(payload: Mapping[str, object], key: str) -> Mapping[object, object]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _sequence_field(payload: Mapping[str, object], key: str) -> tuple[object, ...]:
    value = payload.get(key)
    if isinstance(value, str) or not isinstance(value, Sequence):
        return ()
    return tuple(value)


def predict_three_body_positions(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
) -> dict[str, object]:
    """Predict the three body positions at ``target_time`` by high-precision integration.

    This is the practical answer to the generic three-body prediction problem:
    for arbitrary masses and initial state, the engine returns a controlled
    numerical forecast plus conservation diagnostics rather than claiming a
    global closed-form solution.
    """

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    sample_count = _validated_sample_count(samples)
    t_eval = _prediction_times(target_time, sample_count)
    if target_time == 0.0:
        trajectory = TrajectoryResult(
            t=np.array([0.0], dtype=float),
            y=np.asarray([initial_state], dtype=float),
            success=True,
            message="target_time is zero; returned the initial state.",
            metadata={"method": "identity", "nfev": 0, "njev": 0, "nlu": 0},
        )
    else:
        trajectory = AdaptiveIntegrator(rtol=rtol, atol=atol, max_step=max_step).integrate(
            system,
            (0.0, target_time),
            initial_state,
            t_eval=t_eval,
        )
    final_state = trajectory.y[-1] if len(trajectory.y) else np.full(system.state_dim, np.nan)
    final_positions, final_velocities = system.split_state(final_state)
    invariant_certificate = noether_invariant_drift_certificate(system, trajectory).as_dict()
    return {
        "prediction_schema_version": 1,
        "prediction_type": "deterministic-position",
        "method": "adaptive-DOP853",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": trajectory.success,
        "message": trajectory.message,
        "positions": final_positions.tolist(),
        "velocities": final_velocities.tolist(),
        "final_state": final_state.tolist(),
        "sample_count": int(len(trajectory.t)),
        "solver": dict(trajectory.metadata),
        "invariant_certificate": invariant_certificate,
    }


def predict_three_body_position_distribution(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int = 64,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    seed: int = 0,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    preserve_center_of_mass: bool = True,
    include_sample_positions: bool = False,
) -> dict[str, object]:
    """Return an empirical final-position distribution from perturbed initial states."""

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    count = _validated_positive_int(count, "count")
    sample_count = _validated_sample_count(samples)
    position_scale = _nonnegative_float(position_scale, "position_scale")
    velocity_scale = _nonnegative_float(velocity_scale, "velocity_scale")
    rng = np.random.default_rng(seed)
    initial_states = _perturbed_initial_states(
        system,
        initial_state,
        count=count,
        rng=rng,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        preserve_center_of_mass=preserve_center_of_mass,
    )
    t_eval = _prediction_times(target_time, sample_count)
    integrator = AdaptiveIntegrator(rtol=rtol, atol=atol, max_step=max_step)
    successful_positions: list[np.ndarray] = []
    sample_rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for index, state in enumerate(initial_states):
        if target_time == 0.0:
            trajectory = TrajectoryResult(
                t=np.array([0.0], dtype=float),
                y=np.asarray([state], dtype=float),
                success=True,
                message="target_time is zero; returned the initial state.",
                metadata={"method": "identity", "nfev": 0, "njev": 0, "nlu": 0},
            )
        else:
            trajectory = integrator.integrate(system, (0.0, target_time), state, t_eval=t_eval)
        if not trajectory.success or len(trajectory.y) == 0:
            failures.append({"index": index, "message": trajectory.message})
            continue
        final_positions, final_velocities = system.split_state(trajectory.y[-1])
        successful_positions.append(final_positions)
        if include_sample_positions:
            sample_rows.append(
                {
                    "index": index,
                    "positions": final_positions.tolist(),
                    "velocities": final_velocities.tolist(),
                }
            )
    summary = _position_distribution_summary(successful_positions, system.dimension)
    base_prediction = predict_three_body_positions(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    result: dict[str, object] = {
        "prediction_schema_version": 1,
        "prediction_type": "empirical-position-distribution",
        "method": "adaptive-DOP853-ensemble",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "count": count,
            "seed": int(seed),
            "position_scale": position_scale,
            "velocity_scale": velocity_scale,
            "preserve_center_of_mass": preserve_center_of_mass,
        },
        "success_count": len(successful_positions),
        "failure_count": len(failures),
        "failures": failures,
        "base_prediction": base_prediction,
        "position_distribution": summary,
    }
    if include_sample_positions:
        result["sample_predictions"] = sample_rows
    return result


def predict_three_body_linearized_distribution(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    initial_state_covariance: Sequence[Sequence[float]] | None = None,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    jacobian_step: float = 1.0e-6,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
) -> dict[str, object]:
    """Push an initial Gaussian uncertainty through the linearized three-body flow.

    If ``x(t) = Phi_t(x0)`` and ``P0`` is the initial covariance, this returns
    the first-order Gaussian approximation ``Pt = DPhi_t P0 DPhi_t^T``.
    """

    system, initial_state = _general_prediction_system(
        masses,
        positions,
        velocities,
        gravitational_constant=gravitational_constant,
        softening=softening,
    )
    target_time = _finite_float(target_time, "target_time")
    jacobian_step = _positive_float(jacobian_step, "jacobian_step")
    covariance0 = _initial_state_covariance(
        initial_state.size,
        system.dimension,
        initial_state_covariance=initial_state_covariance,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
    )
    flow = _linearized_flow_map(
        system,
        initial_state,
        target_time,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
    )
    transition = flow["transition_matrix"]
    covariance_t = _symmetrize_covariance(transition @ covariance0 @ transition.T)
    position_width = system.body_count * system.dimension
    position_covariance = covariance_t[:position_width, :position_width]
    body_covariances = [
        position_covariance[
            body_index * system.dimension : (body_index + 1) * system.dimension,
            body_index * system.dimension : (body_index + 1) * system.dimension,
        ]
        for body_index in range(system.body_count)
    ]
    final_positions, final_velocities = system.split_state(flow["final_state"])
    std_positions = np.sqrt(np.maximum(np.diag(position_covariance), 0.0)).reshape(
        system.body_count,
        system.dimension,
    )
    covariance_eigenvalues = np.linalg.eigvalsh(covariance_t)
    return {
        "prediction_schema_version": 1,
        "prediction_type": "linearized-gaussian-position-distribution",
        "method": "variational-flow-covariance-pushforward",
        "target_time": target_time,
        "dimension": system.dimension,
        "masses": [float(mass) for mass in system.masses],
        "gravitational_constant": float(system.gravitational_constant),
        "softening": float(system.softening),
        "success": bool(flow["success"]),
        "message": str(flow["message"]),
        "mean_positions": final_positions.tolist(),
        "mean_velocities": final_velocities.tolist(),
        "std_positions": std_positions.tolist(),
        "initial_state_covariance": covariance0.tolist(),
        "final_state_covariance": covariance_t.tolist(),
        "position_covariance": position_covariance.tolist(),
        "body_position_covariances": [covariance.tolist() for covariance in body_covariances],
        "state_transition_matrix": transition.tolist(),
        "linearized_diagnostics": {
            "jacobian_step": jacobian_step,
            "transition_condition_number": float(np.linalg.cond(transition)),
            "transition_spectral_radius": float(max(abs(np.linalg.eigvals(transition)))),
            "minimum_covariance_eigenvalue": float(np.min(covariance_eigenvalues)),
            "maximum_position_std": float(np.max(std_positions)),
        },
        "interpretation": (
            "First-order Gaussian push-forward: valid while neglected nonlinear terms stay small relative "
            "to the propagated covariance scale."
        ),
    }


def predict_three_body_interpretation_report(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    target_time: float,
    *,
    count: int = 64,
    position_scale: float = 1.0e-6,
    velocity_scale: float = 1.0e-6,
    seed: int = 0,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
    samples: int = 256,
    rtol: float = 1.0e-10,
    atol: float = 1.0e-12,
    max_step: float = math.inf,
    jacobian_step: float = 1.0e-6,
    linearized_covariance_relative_tolerance: float = 0.75,
) -> dict[str, object]:
    """Return a point/linearized/ensemble prediction report with a mode recommendation."""

    deterministic = predict_three_body_positions(
        masses,
        positions,
        velocities,
        target_time,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    linearized = predict_three_body_linearized_distribution(
        masses,
        positions,
        velocities,
        target_time,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        gravitational_constant=gravitational_constant,
        softening=softening,
        jacobian_step=jacobian_step,
        rtol=rtol,
        atol=atol,
    )
    empirical = predict_three_body_position_distribution(
        masses,
        positions,
        velocities,
        target_time,
        count=count,
        position_scale=position_scale,
        velocity_scale=velocity_scale,
        seed=seed,
        gravitational_constant=gravitational_constant,
        softening=softening,
        samples=samples,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    comparison = _prediction_distribution_comparison(linearized, empirical)
    verdict = _prediction_report_verdict(
        deterministic,
        linearized,
        empirical,
        comparison,
        linearized_covariance_relative_tolerance=linearized_covariance_relative_tolerance,
    )
    return {
        "prediction_schema_version": 1,
        "prediction_type": "three-body-interpretation-report",
        "target_time": float(target_time),
        "uncertainty_model": {
            "type": "gaussian_initial_state",
            "count": int(count),
            "seed": int(seed),
            "position_scale": float(position_scale),
            "velocity_scale": float(velocity_scale),
        },
        "deterministic": deterministic,
        "linearized_gaussian": linearized,
        "empirical_distribution": empirical,
        "comparison": comparison,
        "verdict": verdict,
    }


def _general_prediction_system(
    masses: Sequence[float],
    positions: Sequence[Sequence[float]],
    velocities: Sequence[Sequence[float]],
    *,
    gravitational_constant: float,
    softening: float,
) -> tuple[GeneralThreeBodySystem, np.ndarray]:
    masses_array = np.asarray(masses, dtype=float)
    positions_array = np.asarray(positions, dtype=float)
    velocities_array = np.asarray(velocities, dtype=float)
    if masses_array.shape != (3,):
        raise ValueError("masses must contain exactly three values.")
    if np.any(~np.isfinite(masses_array)) or np.any(masses_array <= 0.0):
        raise ValueError("masses must be finite positive values.")
    if positions_array.ndim != 2 or positions_array.shape[0] != 3 or positions_array.shape[1] not in (2, 3):
        raise ValueError("positions must have shape (3, 2) or (3, 3).")
    if velocities_array.shape != positions_array.shape:
        raise ValueError("velocities must have the same shape as positions.")
    if np.any(~np.isfinite(positions_array)) or np.any(~np.isfinite(velocities_array)):
        raise ValueError("positions and velocities must contain only finite values.")
    gravitational_constant = _positive_float(gravitational_constant, "gravitational_constant")
    softening = _nonnegative_float(softening, "softening")
    system = GeneralThreeBodySystem(
        masses=tuple(float(mass) for mass in masses_array),
        gravitational_constant=gravitational_constant,
        dimension=int(positions_array.shape[1]),
        softening=softening,
    )
    return system, system.flatten_state(positions_array, velocities_array)


def _finite_float(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _positive_float(value: float, name: str) -> float:
    value = _finite_float(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return value


def _nonnegative_float(value: float, name: str) -> float:
    value = _finite_float(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return value


def _validated_positive_int(value: int, name: str) -> int:
    value = int(value)
    if value < 1:
        raise ValueError(f"{name} must be >= 1.")
    return value


def _validated_sample_count(samples: int) -> int:
    samples = int(samples)
    if samples < 2:
        raise ValueError("samples must be >= 2.")
    return samples


def _prediction_times(target_time: float, samples: int) -> np.ndarray:
    if target_time == 0.0:
        return np.array([0.0], dtype=float)
    return np.linspace(0.0, target_time, samples)


def _perturbed_initial_states(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    *,
    count: int,
    rng: np.random.Generator,
    position_scale: float,
    velocity_scale: float,
    preserve_center_of_mass: bool,
) -> list[np.ndarray]:
    positions, velocities = system.split_state(initial_state)
    states = [initial_state.copy()]
    masses = np.asarray(system.masses, dtype=float)
    for _index in range(1, count):
        position_noise = rng.normal(0.0, position_scale, size=positions.shape)
        velocity_noise = rng.normal(0.0, velocity_scale, size=velocities.shape)
        if preserve_center_of_mass:
            position_noise = position_noise - np.average(position_noise, axis=0, weights=masses)
            velocity_noise = velocity_noise - np.average(velocity_noise, axis=0, weights=masses)
        states.append(system.flatten_state(positions + position_noise, velocities + velocity_noise))
    return states


def _position_distribution_summary(positions: list[np.ndarray], dimension: int) -> dict[str, object]:
    if not positions:
        return {
            "mean_positions": [],
            "median_positions": [],
            "q05_positions": [],
            "q95_positions": [],
            "flat_covariance": [],
            "body_covariances": [],
            "max_body_radius_from_mean": math.inf,
        }
    stack = np.asarray(positions, dtype=float)
    flat = stack.reshape(stack.shape[0], 3 * dimension)
    mean = np.mean(stack, axis=0)
    quantiles = np.quantile(stack, [0.05, 0.5, 0.95], axis=0)
    if flat.shape[0] > 1:
        flat_covariance = np.cov(flat, rowvar=False)
        body_covariances = [
            np.cov(stack[:, body_index, :], rowvar=False).reshape(dimension, dimension)
            for body_index in range(3)
        ]
    else:
        flat_covariance = np.zeros((3 * dimension, 3 * dimension), dtype=float)
        body_covariances = [np.zeros((dimension, dimension), dtype=float) for _body in range(3)]
    body_radii = np.linalg.norm(stack - mean[None, :, :], axis=2)
    return {
        "mean_positions": mean.tolist(),
        "median_positions": quantiles[1].tolist(),
        "q05_positions": quantiles[0].tolist(),
        "q95_positions": quantiles[2].tolist(),
        "flat_covariance": flat_covariance.tolist(),
        "body_covariances": [covariance.tolist() for covariance in body_covariances],
        "max_body_radius_from_mean": float(np.max(body_radii)),
    }


def _initial_state_covariance(
    state_dimension: int,
    physical_dimension: int,
    *,
    initial_state_covariance: Sequence[Sequence[float]] | None,
    position_scale: float,
    velocity_scale: float,
) -> np.ndarray:
    if initial_state_covariance is not None:
        covariance = np.asarray(initial_state_covariance, dtype=float)
        if covariance.shape != (state_dimension, state_dimension):
            raise ValueError("initial_state_covariance must have shape (state_dim, state_dim).")
        if np.any(~np.isfinite(covariance)):
            raise ValueError("initial_state_covariance must contain only finite values.")
        return _symmetrize_covariance(covariance)
    position_scale = _nonnegative_float(position_scale, "position_scale")
    velocity_scale = _nonnegative_float(velocity_scale, "velocity_scale")
    position_width = 3 * physical_dimension
    diagonal = np.concatenate(
        [
            np.full(position_width, position_scale**2, dtype=float),
            np.full(state_dimension - position_width, velocity_scale**2, dtype=float),
        ]
    )
    return np.diag(diagonal)


def _linearized_flow_map(
    system: GeneralThreeBodySystem,
    initial_state: np.ndarray,
    target_time: float,
    *,
    jacobian_step: float,
    rtol: float,
    atol: float,
) -> dict[str, object]:
    state_dimension = initial_state.size
    identity = np.eye(state_dimension, dtype=float)
    if target_time == 0.0:
        return {
            "success": True,
            "message": "target_time is zero; returned identity state-transition matrix.",
            "final_state": initial_state.copy(),
            "transition_matrix": identity,
        }
    combined_initial = np.concatenate([initial_state, identity.reshape(-1)])

    def combined_rhs(time: float, combined_state: np.ndarray) -> np.ndarray:
        current_state = combined_state[:state_dimension]
        transition = combined_state[state_dimension:].reshape(state_dimension, state_dimension)
        jacobian = finite_difference_jacobian(system, current_state, time=time, step=jacobian_step)
        return np.concatenate([system.rhs(time, current_state), (jacobian @ transition).reshape(-1)])

    solution = solve_ivp(
        fun=combined_rhs,
        t_span=(0.0, target_time),
        y0=combined_initial,
        method="DOP853",
        t_eval=(target_time,),
        rtol=rtol,
        atol=atol,
    )
    if solution.y.size == 0:
        return {
            "success": False,
            "message": str(solution.message),
            "final_state": np.full_like(initial_state, np.nan, dtype=float),
            "transition_matrix": np.full((state_dimension, state_dimension), np.nan, dtype=float),
        }
    final = np.asarray(solution.y[:, -1], dtype=float)
    return {
        "success": bool(solution.success),
        "message": str(solution.message),
        "final_state": final[:state_dimension],
        "transition_matrix": final[state_dimension:].reshape(state_dimension, state_dimension),
    }


def _symmetrize_covariance(covariance: np.ndarray) -> np.ndarray:
    covariance = np.asarray(covariance, dtype=float)
    return 0.5 * (covariance + covariance.T)


def _prediction_distribution_comparison(
    linearized: Mapping[str, object],
    empirical: Mapping[str, object],
) -> dict[str, object]:
    linearized_mean = np.asarray(linearized.get("mean_positions", []), dtype=float)
    empirical_distribution = empirical.get("position_distribution", {})
    if not isinstance(empirical_distribution, Mapping):
        empirical_distribution = {}
    empirical_mean = np.asarray(empirical_distribution.get("mean_positions", []), dtype=float)
    linearized_covariance = np.asarray(linearized.get("position_covariance", []), dtype=float)
    empirical_covariance = np.asarray(empirical_distribution.get("flat_covariance", []), dtype=float)
    if linearized_mean.shape == empirical_mean.shape and linearized_mean.size:
        body_mean_gap = np.linalg.norm(empirical_mean - linearized_mean, axis=1)
        mean_gap_norm = float(np.linalg.norm(empirical_mean - linearized_mean))
        max_body_mean_gap = float(np.max(body_mean_gap))
    else:
        body_mean_gap = np.asarray([], dtype=float)
        mean_gap_norm = math.inf
        max_body_mean_gap = math.inf
    if linearized_covariance.shape == empirical_covariance.shape and linearized_covariance.size:
        covariance_gap = float(np.linalg.norm(empirical_covariance - linearized_covariance, ord="fro"))
        empirical_norm = float(np.linalg.norm(empirical_covariance, ord="fro"))
        linearized_norm = float(np.linalg.norm(linearized_covariance, ord="fro"))
        covariance_relative_gap = covariance_gap / max(empirical_norm, linearized_norm, 1.0e-300)
        empirical_std = np.sqrt(np.maximum(np.diag(empirical_covariance), 0.0))
        linearized_std = np.sqrt(np.maximum(np.diag(linearized_covariance), 0.0))
        max_empirical_std = float(np.max(empirical_std))
        max_linearized_std = float(np.max(linearized_std))
    else:
        covariance_gap = math.inf
        empirical_norm = math.inf
        linearized_norm = math.inf
        covariance_relative_gap = math.inf
        max_empirical_std = math.inf
        max_linearized_std = math.inf
    spread_scale = max(max_empirical_std, max_linearized_std, 1.0e-300)
    return {
        "body_mean_gap": body_mean_gap.tolist(),
        "mean_gap_norm": mean_gap_norm,
        "max_body_mean_gap": max_body_mean_gap,
        "mean_gap_in_sigma_units": float(max_body_mean_gap / spread_scale),
        "covariance_frobenius_gap": covariance_gap,
        "empirical_covariance_frobenius_norm": empirical_norm,
        "linearized_covariance_frobenius_norm": linearized_norm,
        "covariance_relative_gap": covariance_relative_gap,
        "max_empirical_position_std": max_empirical_std,
        "max_linearized_position_std": max_linearized_std,
    }


def _prediction_report_verdict(
    deterministic: Mapping[str, object],
    linearized: Mapping[str, object],
    empirical: Mapping[str, object],
    comparison: Mapping[str, object],
    *,
    linearized_covariance_relative_tolerance: float,
) -> dict[str, object]:
    invariant_certificate = deterministic.get("invariant_certificate", {})
    if not isinstance(invariant_certificate, Mapping):
        invariant_certificate = {}
    deterministic_resolved = bool(
        deterministic.get("success") is True
        and invariant_certificate.get("maximum_relative_energy_drift", math.inf) <= 1.0e-8
    )
    empirical_success_count = int(empirical.get("success_count", 0))
    empirical_failure_count = int(empirical.get("failure_count", 0))
    empirical_resolved = empirical_success_count > 0 and empirical_failure_count == 0
    covariance_relative_gap = float(comparison.get("covariance_relative_gap", math.inf))
    mean_gap_in_sigma_units = float(comparison.get("mean_gap_in_sigma_units", math.inf))
    linearized_consistent = bool(
        linearized.get("success") is True
        and empirical_resolved
        and covariance_relative_gap <= linearized_covariance_relative_tolerance
        and mean_gap_in_sigma_units <= 3.0
    )
    if linearized_consistent:
        recommended_mode = "linearized-gaussian"
    elif empirical_resolved:
        recommended_mode = "empirical-ensemble"
    elif deterministic_resolved:
        recommended_mode = "deterministic-only"
    else:
        recommended_mode = "unresolved"
    return {
        "deterministic_resolved": deterministic_resolved,
        "linearized_consistent_with_ensemble": linearized_consistent,
        "empirical_distribution_resolved": empirical_resolved,
        "recommended_mode": recommended_mode,
        "linearized_covariance_relative_tolerance": float(linearized_covariance_relative_tolerance),
        "rationale": _prediction_verdict_rationale(
            recommended_mode,
            deterministic_resolved=deterministic_resolved,
            covariance_relative_gap=covariance_relative_gap,
            mean_gap_in_sigma_units=mean_gap_in_sigma_units,
            empirical_failure_count=empirical_failure_count,
        ),
    }


def _prediction_verdict_rationale(
    recommended_mode: str,
    *,
    deterministic_resolved: bool,
    covariance_relative_gap: float,
    mean_gap_in_sigma_units: float,
    empirical_failure_count: int,
) -> str:
    if recommended_mode == "linearized-gaussian":
        return (
            "The deterministic trajectory is resolved, and the variational covariance push-forward agrees "
            "with the empirical ensemble within the declared mean/covariance gates."
        )
    if recommended_mode == "empirical-ensemble":
        return (
            "The empirical ensemble integrated successfully, but the linearized Gaussian approximation is "
            f"not promoted: covariance_relative_gap={covariance_relative_gap:.3g}, "
            f"mean_gap_in_sigma_units={mean_gap_in_sigma_units:.3g}."
        )
    if recommended_mode == "deterministic-only":
        return (
            "Only the nominal trajectory is resolved; the uncertainty propagation did not produce a clean "
            f"ensemble result, with empirical_failure_count={empirical_failure_count}."
        )
    return (
        "The nominal trajectory or uncertainty propagation failed the configured diagnostics; tighten solver "
        f"settings or shorten the forecast horizon. deterministic_resolved={deterministic_resolved}."
    )


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
