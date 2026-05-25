from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from html.parser import HTMLParser
from math import pi
from pathlib import Path
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .analysis import AnalysisAtlas, ResearchPipeline, ThreeBodyInterpreter
from .experiments import (
    BoundaryResolutionStudy,
    ClassifierArtifactStudy,
    CloseEncounterResidualGridStudy,
    CloseEncounterResidualStudy,
    FigureEightStabilityProbe,
    HierarchicalFlybySweep,
    InterpretationSuite,
    IntegratorComparisonStudy,
    KnownBenchmarkSuite,
    NearCollisionScalingStudy,
    OrbitLibrary,
    RegimeProbeSuite,
    TheoremSuite,
)
from .solvers import AdaptiveIntegrator
from .types import Scenario


PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE = "public-claims-v1"
STATIC_SITE_ARTIFACT_NAMES = ("index.html", "certificate.json", "favicon.svg", ".gitattributes")
STATIC_SITE_BUNDLE_NAMES = (*STATIC_SITE_ARTIFACT_NAMES, "manifest.json")
STATIC_SITE_GITATTRIBUTES_POLICY = b"* text eol=lf\n"
PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES = (
    "artifact-availability",
    "json-parse-errors",
    "artifact-identity",
    "manifest-hash-algorithm",
    "index-artifact-discoverability",
    "publication-pipeline-links",
    "published-branch-line-ending-policy",
    "commit-provenance",
    "active-profile-descriptor",
    "profile-gates",
    "numeric-minimums",
    "numeric-maximums",
)
STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES = (
    *PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES,
    "certificate-verifier-capability-digest",
)
STATIC_ARTIFACT_REQUIREMENT_PROFILES: dict[str, dict[str, tuple[str, ...]]] = {
    PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE: {
        "require_gates": (
            "picard_certified",
            "poincare_markov_significant_baseline_win",
            "poincare_passes_permutation_control",
            "poincare_passes_section_robustness",
            "symbolic_passes_stride_robustness",
        ),
        "require_minimums": (
            "publication_pipeline.promotion_gate_pass_count=7",
            "promotion_gates.picard_contraction_reserve=0",
            "promotion_gates.poincare_section_robust_pass_fraction=1",
            "promotion_gates.symbolic_stride_robust_pass_fraction=1",
        ),
        "require_maximums": (
            "metrics.general_max_energy_drift=1e-8",
            "metrics.restricted_max_jacobi_drift=1e-9",
            "metrics.picard_max_contraction=0.35",
        ),
        "require_features": PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES,
    }
}


def static_artifact_requirement_profile_descriptor(profile_name: str) -> dict[str, object]:
    if profile_name not in STATIC_ARTIFACT_REQUIREMENT_PROFILES:
        raise ValueError(f"Unknown verification profile: {profile_name}")
    return {
        "profile": profile_name,
        "profile_schema_version": 1,
        "requirements": _static_artifact_profile_requirements((profile_name,)),
    }


def static_artifact_requirement_profile_sha256(profile_name: str) -> str:
    descriptor = static_artifact_requirement_profile_descriptor(profile_name)
    canonical = json.dumps(descriptor, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def static_artifact_verification_features_sha256(features: Sequence[str]) -> str:
    canonical = json.dumps(list(features), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def static_artifact_receipt_payload_sha256(receipt: Mapping[str, object]) -> str:
    payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"verified_at_utc", "receipt_payload_sha256"}
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="threebody",
        description="Three-body research tools for surveys, transition mining, and compact-model preparation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    survey = subparsers.add_parser("survey", help="Run a perturbation survey and export transition evidence.")
    survey.add_argument(
        "--scenario",
        choices=("figure-eight", "hierarchical-flyby", "restricted-l4", "restricted-l5"),
        default="figure-eight",
        help="Reference scenario to perturb.",
    )
    survey.add_argument("--count", type=int, default=8, help="Number of perturbed trajectories.")
    survey.add_argument(
        "--periods",
        type=float,
        default=0.25,
        help="Scenario duration. For periodic scenarios this is periods; for flyby it is integration time.",
    )
    survey.add_argument("--samples", type=int, default=600, help="Number of solver sample times.")
    survey.add_argument("--stride", type=int, default=15, help="Classification stride through each trajectory.")
    survey.add_argument("--position-scale", type=float, default=1.0e-3, help="Position perturbation scale.")
    survey.add_argument("--velocity-scale", type=float, default=1.0e-3, help="Velocity perturbation scale.")
    survey.add_argument(
        "--validation-count",
        type=int,
        default=0,
        help="If positive, mine laws on --count trajectories and validate them on this many held-out trajectories.",
    )
    survey.add_argument("--rtol", type=float, default=1.0e-9, help="Adaptive integrator relative tolerance.")
    survey.add_argument("--atol", type=float, default=1.0e-11, help="Adaptive integrator absolute tolerance.")
    survey.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-<scenario>.json.",
    )
    survey.set_defaults(func=run_survey_command)
    flyby_sweep = subparsers.add_parser("flyby-sweep", help="Sweep hierarchical flyby parameters and export boundary evidence.")
    flyby_sweep.add_argument("--samples", type=int, default=600, help="Number of solver sample times per case.")
    flyby_sweep.add_argument("--stride", type=int, default=20, help="Classification stride through each trajectory.")
    flyby_sweep.add_argument("--duration", type=float, default=8.0, help="Integration time per flyby case.")
    flyby_sweep.add_argument(
        "--heldout",
        action="store_true",
        help="Run separate discovery and held-out validation flyby grids for collapse fits.",
    )
    flyby_sweep.add_argument(
        "--phase-sweep",
        action="store_true",
        help="Vary inner-binary phase to test phase-conditioned and resonance-sensitive collapse models.",
    )
    flyby_sweep.add_argument("--rtol", type=float, default=1.0e-9, help="Adaptive integrator relative tolerance.")
    flyby_sweep.add_argument("--atol", type=float, default=1.0e-11, help="Adaptive integrator absolute tolerance.")
    flyby_sweep.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-flyby-sweep.json.",
    )
    flyby_sweep.set_defaults(func=run_flyby_sweep_command)
    resolution = subparsers.add_parser("boundary-resolution", help="Check boundary sensitivity to samples and stride.")
    resolution.add_argument("--duration", type=float, default=8.0, help="Integration time per resolution case.")
    resolution.add_argument("--rtol", type=float, default=1.0e-9, help="Adaptive integrator relative tolerance.")
    resolution.add_argument("--atol", type=float, default=1.0e-11, help="Adaptive integrator absolute tolerance.")
    resolution.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-boundary-resolution.json.",
    )
    resolution.set_defaults(func=run_boundary_resolution_command)
    checks = subparsers.add_parser("research-checks", help="Run artifact, benchmark, integrator, and regime sanity checks.")
    checks.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-research-checks.json.",
    )
    checks.set_defaults(func=run_research_checks_command)
    theorem = subparsers.add_parser("theorem-suite", help="Run theorem-candidate proof obligations and paper benchmarks.")
    theorem.add_argument(
        "--mode",
        choices=("quick", "paper"),
        default="quick",
        help="Use quick for development checks or paper for the full Picard-certified 5x5x5 parameter grid.",
    )
    theorem.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-theorem-suite.json.",
    )
    theorem.set_defaults(func=run_theorem_suite_command)
    interpret = subparsers.add_parser("interpret", help="Integrate a reference scenario and export chart-local interpretation segments.")
    interpret.add_argument(
        "--scenario",
        choices=("figure-eight", "hierarchical-flyby", "restricted-l4", "restricted-l5"),
        default="hierarchical-flyby",
        help="Reference scenario to interpret.",
    )
    interpret.add_argument(
        "--periods",
        type=float,
        default=0.25,
        help="Scenario duration. For periodic scenarios this is periods; for flyby it is integration time.",
    )
    interpret.add_argument("--samples", type=int, default=600, help="Number of solver sample times.")
    interpret.add_argument("--stride", type=int, default=20, help="Classification stride through the trajectory.")
    interpret.add_argument("--rtol", type=float, default=1.0e-9, help="Adaptive integrator relative tolerance.")
    interpret.add_argument("--atol", type=float, default=1.0e-11, help="Adaptive integrator absolute tolerance.")
    interpret.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-interpret.json.",
    )
    interpret.set_defaults(func=run_interpret_command)
    interpretation_suite = subparsers.add_parser(
        "interpretation-suite",
        help="Run representative regimes through chart-local interpretation certificates.",
    )
    interpretation_suite.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-interpretation-suite.json.",
    )
    interpretation_suite.set_defaults(func=run_interpretation_suite_command)
    benchmark = subparsers.add_parser("atlas-benchmark", help="Export reproducible atlas benchmark cases.")
    benchmark.add_argument(
        "--scenario",
        action="append",
        choices=("figure-eight", "hierarchical-flyby", "restricted-l4", "restricted-l5"),
        default=None,
        help="Scenario to include. Repeat to include multiple cases. Defaults to a representative smoke suite.",
    )
    benchmark.add_argument("--periods", type=float, default=0.25, help="Scenario duration or flyby integration time.")
    benchmark.add_argument("--samples", type=int, default=240, help="Number of solver sample times per case.")
    benchmark.add_argument("--stride", type=int, default=20, help="Classification stride through each trajectory.")
    benchmark.add_argument("--rtol", type=float, default=1.0e-9, help="Adaptive integrator relative tolerance.")
    benchmark.add_argument("--atol", type=float, default=1.0e-11, help="Adaptive integrator absolute tolerance.")
    benchmark.add_argument(
        "--include-trajectories",
        action="store_true",
        help="Include sampled state arrays in the JSON artifact.",
    )
    benchmark.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON output path. Defaults to .runtime/research_runs/<timestamp>-atlas-benchmark.json.",
    )
    benchmark.set_defaults(func=run_atlas_benchmark_command)
    predict = subparsers.add_parser(
        "predict",
        help="Predict general three-body positions or an empirical final-position distribution from JSON input.",
    )
    predict.add_argument(
        "--input",
        type=Path,
        required=True,
        help="JSON file with masses, positions, velocities, and target_time.",
    )
    predict.add_argument(
        "--target-time",
        type=float,
        default=None,
        help="Override target_time from the input JSON.",
    )
    predict.add_argument(
        "--distribution",
        action="store_true",
        help="Propagate Gaussian initial-condition uncertainty and return a final-position distribution.",
    )
    predict.add_argument("--count", type=int, default=64, help="Distribution ensemble size.")
    predict.add_argument("--position-scale", type=float, default=1.0e-6, help="Initial position uncertainty scale.")
    predict.add_argument("--velocity-scale", type=float, default=1.0e-6, help="Initial velocity uncertainty scale.")
    predict.add_argument("--seed", type=int, default=0, help="Distribution ensemble random seed.")
    predict.add_argument("--samples", type=int, default=256, help="Number of solver sample times.")
    predict.add_argument("--rtol", type=float, default=1.0e-10, help="Adaptive integrator relative tolerance.")
    predict.add_argument("--atol", type=float, default=1.0e-12, help="Adaptive integrator absolute tolerance.")
    predict.add_argument("--max-step", type=float, default=float("inf"), help="Adaptive integrator maximum step.")
    predict.add_argument("--gravitational-constant", type=float, default=1.0, help="Newtonian gravitational constant.")
    predict.add_argument("--softening", type=float, default=0.0, help="Optional Plummer-style softening length.")
    predict.add_argument(
        "--include-sample-positions",
        action="store_true",
        help="Include every ensemble member's final positions in distribution mode.",
    )
    predict.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    predict.set_defaults(func=run_predict_command)
    verify_static = subparsers.add_parser(
        "verify-static-artifacts",
        help="Verify static Pages certificate and manifest artifact integrity.",
    )
    verify_static.add_argument(
        "--site-dir",
        type=Path,
        default=Path("site"),
        help="Directory containing index.html, certificate.json, favicon.svg, .gitattributes, and manifest.json.",
    )
    verify_static.add_argument(
        "--base-url",
        default=None,
        help="Base URL containing index.html, certificate.json, favicon.svg, .gitattributes, and manifest.json.",
    )
    verify_static.add_argument(
        "--require-commit",
        default=None,
        help="Require certificate.json and manifest.json provenance to match this commit SHA or prefix.",
    )
    verify_static.add_argument(
        "--require-gate",
        action="append",
        default=[],
        help="Require a named certificate promotion_gates entry to be exactly true. Repeat for multiple gates.",
    )
    verify_static.add_argument(
        "--require-min",
        action="append",
        default=[],
        metavar="PATH=VALUE",
        help="Require a numeric certificate field to be at least VALUE. Use dotted paths and repeat as needed.",
    )
    verify_static.add_argument(
        "--require-max",
        action="append",
        default=[],
        metavar="PATH=VALUE",
        help="Require a numeric certificate field to be at most VALUE. Use dotted paths and repeat as needed.",
    )
    verify_static.add_argument(
        "--require-profile",
        action="append",
        choices=tuple(STATIC_ARTIFACT_REQUIREMENT_PROFILES),
        default=[],
        metavar="NAME",
        help=(
            "Apply a named verification profile that expands to a versioned set of gate/min/max requirements. "
            f"Available: {PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE}."
        ),
    )
    verify_static.add_argument(
        "--require-public-claim",
        action="store_true",
        help=(
            f"Apply {PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE} and pin this verifier build's current "
            "capability-set digest."
        ),
    )
    verify_static.add_argument(
        "--require-feature",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Require this verifier receipt to advertise a named verification_schema_features capability. "
            "Repeat for multiple capabilities."
        ),
    )
    feature_set_group = verify_static.add_mutually_exclusive_group()
    feature_set_group.add_argument(
        "--require-feature-set-sha256",
        default=None,
        metavar="SHA256",
        help="Require verification_schema_features_sha256 to match this canonical verifier capability-set digest.",
    )
    feature_set_group.add_argument(
        "--require-current-feature-set",
        action="store_true",
        help="Pin required_feature_set_sha256 to this verifier build's current canonical capability-set digest.",
    )
    verify_static.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON path for writing a persistent verification receipt.",
    )
    verify_static.set_defaults(func=run_verify_static_artifacts_command)
    return parser


def run_survey_command(args: argparse.Namespace) -> int:
    scenario = _scenario_from_args(args)
    pipeline = ResearchPipeline(
        integrator=AdaptiveIntegrator(rtol=args.rtol, atol=args.atol),
    )
    if args.validation_count > 0:
        result = pipeline.run_discovery_validation_study(
            scenario,
            discovery_count=args.count,
            validation_count=args.validation_count,
            position_scale=args.position_scale,
            velocity_scale=args.velocity_scale,
            stride=args.stride,
        )
        summary = result.summary()
        trajectory_count = len(result.discovery.trajectories) + len(result.validation.trajectories)
        transition_count = len(result.discovery.survey.graph.rows()) + len(result.validation.survey.graph.rows())
        candidate_law_count = len(result.discovery.candidate_laws)
    else:
        result = pipeline.run_perturbation_study(
            scenario,
            count=args.count,
            position_scale=args.position_scale,
            velocity_scale=args.velocity_scale,
            stride=args.stride,
        )
        summary = result.summary()
        trajectory_count = len(result.trajectories)
        transition_count = len(result.survey.graph.rows())
        candidate_law_count = len(result.candidate_laws)
    output = args.output or _default_output_path(args.scenario)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "scenario": scenario.name,
            "description": scenario.description,
            "t_span": list(scenario.t_span),
            "samples": 0 if scenario.t_eval is None else int(len(scenario.t_eval)),
            "parameters": {
                "count": args.count,
                "periods": args.periods,
                "stride": args.stride,
                "position_scale": args.position_scale,
                "velocity_scale": args.velocity_scale,
                "rtol": args.rtol,
                "atol": args.atol,
                "validation_count": args.validation_count,
            },
        },
        "summary": summary,
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"trajectories={trajectory_count} transitions={transition_count}")
    print(f"candidate_laws={candidate_law_count}")
    return 0


def run_predict_command(args: argparse.Namespace) -> int:
    from threebody_engine import predict_three_body_position_distribution, predict_three_body_positions

    payload = _read_prediction_input(args.input)
    target_time = args.target_time if args.target_time is not None else _required_prediction_field(payload, "target_time")
    common_kwargs = {
        "gravitational_constant": args.gravitational_constant,
        "softening": args.softening,
        "samples": args.samples,
        "rtol": args.rtol,
        "atol": args.atol,
        "max_step": args.max_step,
    }
    if args.distribution:
        result = predict_three_body_position_distribution(
            _required_prediction_field(payload, "masses"),
            _required_prediction_field(payload, "positions"),
            _required_prediction_field(payload, "velocities"),
            target_time,
            count=args.count,
            position_scale=args.position_scale,
            velocity_scale=args.velocity_scale,
            seed=args.seed,
            include_sample_positions=args.include_sample_positions,
            **common_kwargs,
        )
        exit_code = 0 if result["success_count"] else 1
    else:
        result = predict_three_body_positions(
            _required_prediction_field(payload, "masses"),
            _required_prediction_field(payload, "positions"),
            _required_prediction_field(payload, "velocities"),
            target_time,
            **common_kwargs,
        )
        exit_code = 0 if result["success"] else 1
    _write_json_result(result, args.output)
    if args.output is not None:
        print(f"wrote {args.output}")
    return exit_code


def run_flyby_sweep_command(args: argparse.Namespace) -> int:
    sweep = HierarchicalFlybySweep(
        integrator=AdaptiveIntegrator(rtol=args.rtol, atol=args.atol),
    )
    if args.heldout:
        discovery_phases = (0.0, 0.5 * pi) if args.phase_sweep else (0.0,)
        validation_phases = (0.25 * pi, 0.75 * pi) if args.phase_sweep else (0.0,)
        result = sweep.run_discovery_validation(
            discovery_binary_phases=discovery_phases,
            validation_binary_phases=validation_phases,
            duration=args.duration,
            samples=args.samples,
            stride=args.stride,
        )
        summary = result.as_dict()
        case_count = result.discovery.as_dict()["case_count"] + result.validation.as_dict()["case_count"]
        transitioning_count = (
            result.discovery.as_dict()["transitioning_case_count"] + result.validation.as_dict()["transitioning_case_count"]
        )
    else:
        phases = (0.0, 0.5 * pi, pi, 1.5 * pi) if args.phase_sweep else (0.0,)
        result = sweep.run(binary_phases=phases, duration=args.duration, samples=args.samples, stride=args.stride)
        summary = result.as_dict()
        case_count = len(result.rows)
        transitioning_count = result.as_dict()["transitioning_case_count"]
    output = args.output or _default_output_path("flyby-sweep")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "hierarchical-flyby-sweep",
            "parameters": {
                "duration": args.duration,
                "samples": args.samples,
                "stride": args.stride,
                "rtol": args.rtol,
                "atol": args.atol,
                "heldout": args.heldout,
                "phase_sweep": args.phase_sweep,
            },
        },
        "summary": summary,
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"cases={case_count} transitioning={transitioning_count}")
    return 0


def run_boundary_resolution_command(args: argparse.Namespace) -> int:
    study = BoundaryResolutionStudy(integrator=AdaptiveIntegrator(rtol=args.rtol, atol=args.atol))
    result = study.run(duration=args.duration)
    output = args.output or _default_output_path("boundary-resolution")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "boundary-resolution",
            "parameters": {
                "duration": args.duration,
                "rtol": args.rtol,
                "atol": args.atol,
            },
        },
        "summary": result.as_dict(),
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"cases={len(result.rows)}")
    return 0


def run_research_checks_command(args: argparse.Namespace) -> int:
    artifact = ClassifierArtifactStudy().run()
    integrators = IntegratorComparisonStudy().run()
    benchmarks = KnownBenchmarkSuite().run()
    regimes = RegimeProbeSuite().run()
    figure_eight = FigureEightStabilityProbe().run()
    close_residual = CloseEncounterResidualStudy().run()
    close_residual_grid = CloseEncounterResidualGridStudy().run()
    near_collision_scaling = NearCollisionScalingStudy().run()
    output = args.output or _default_output_path("research-checks")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "research-checks",
        },
        "summary": {
            "classifier_artifacts": [row.as_dict() for row in artifact],
            "integrator_comparison": integrators.as_dict(),
            "known_benchmarks": [row.as_dict() for row in benchmarks],
            "regime_probes": [row.as_dict() for row in regimes],
            "figure_eight_stability": figure_eight.as_dict(),
            "close_encounter_residual": close_residual.as_dict(),
            "close_encounter_residual_grid": close_residual_grid.as_dict(),
            "near_collision_scaling": near_collision_scaling.as_dict(),
        },
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"artifact_cases={len(artifact)} benchmarks={len(benchmarks)} regimes={len(regimes)}")
    return 0


def run_theorem_suite_command(args: argparse.Namespace) -> int:
    result = TheoremSuite(mode=args.mode).run()
    output = args.output or _default_output_path("theorem-suite")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "theorem-suite",
            "mode": args.mode,
        },
        "summary": result.as_dict(),
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"mode={result.mode} theorem_candidates={len(result.theorem_candidates)} benchmarks={len(result.benchmarks)}")
    return 0


def run_interpret_command(args: argparse.Namespace) -> int:
    scenario = _scenario_from_args(args)
    trajectory = AdaptiveIntegrator(rtol=args.rtol, atol=args.atol).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    interpretation = ThreeBodyInterpreter().interpret(scenario.system, trajectory, stride=args.stride)
    output = args.output or _default_output_path("interpret")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "trajectory-interpretation",
            "scenario": scenario.name,
            "description": scenario.description,
            "t_span": list(scenario.t_span),
            "samples": 0 if scenario.t_eval is None else int(len(scenario.t_eval)),
            "parameters": {
                "periods": args.periods,
                "stride": args.stride,
                "rtol": args.rtol,
                "atol": args.atol,
            },
        },
        "summary": interpretation.as_dict(),
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"segments={len(interpretation.segments)} transitions={len(interpretation.transitions)}")
    print(f"regime_status={interpretation.certificate.regime_status}")
    print(f"unresolved_obligations={len(interpretation.unresolved_obligations)}")
    return 0


def run_interpretation_suite_command(args: argparse.Namespace) -> int:
    result = InterpretationSuite().run()
    output = args.output or _default_output_path("interpretation-suite")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "interpretation-suite",
        },
        "summary": result.as_dict(),
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"cases={len(result.rows)} local_interpretation_rate={result.local_interpretation_rate:.3f}")
    print(f"covered_chart_types={','.join(result.covered_chart_types)}")
    print(f"unresolved_blockers={len(result.unresolved_blockers)}")
    return 0


def run_atlas_benchmark_command(args: argparse.Namespace) -> int:
    library = OrbitLibrary()
    integrator = AdaptiveIntegrator(rtol=args.rtol, atol=args.atol)
    atlas = AnalysisAtlas()
    scenario_names = args.scenario or ["figure-eight", "hierarchical-flyby", "restricted-l4"]
    cases = []
    for scenario_name in scenario_names:
        scenario = _scenario_from_name(library, scenario_name, periods=args.periods, samples=args.samples)
        trajectory = integrator.integrate(
            scenario.system,
            scenario.t_span,
            scenario.initial_state,
            t_eval=scenario.t_eval,
        )
        reports = atlas.analyze_trajectory(scenario.system, trajectory, stride=args.stride)
        transitions = atlas.transitions(scenario.system, trajectory, stride=args.stride)
        case = {
            "scenario": scenario.name,
            "source_name": scenario_name,
            "description": scenario.description,
            "t_span": list(scenario.t_span),
            "samples": 0 if scenario.t_eval is None else int(len(scenario.t_eval)),
            "initial_state": scenario.initial_state.tolist(),
            "chart_distribution": {
                str(chart): float(fraction)
                for chart, fraction in atlas.chart_distribution(reports).items()
            },
            "transitions": [
                {
                    "index": transition.index,
                    "time": transition.time,
                    "previous": str(transition.previous),
                    "current": str(transition.current),
                    "reason": transition.reason,
                }
                for transition in transitions
            ],
            "reproduce": (
                "threebody interpret "
                f"--scenario {scenario_name} --periods {args.periods} "
                f"--samples {args.samples} --stride {args.stride}"
            ),
        }
        if args.include_trajectories:
            case["trajectory"] = {
                "t": trajectory.t.tolist(),
                "y": trajectory.y.tolist(),
                "success": trajectory.success,
                "message": trajectory.message,
            }
        cases.append(case)
    output = args.output or _default_output_path("atlas-benchmark")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "atlas-benchmark",
            "schema_version": 1,
            "parameters": {
                "periods": args.periods,
                "samples": args.samples,
                "stride": args.stride,
                "rtol": args.rtol,
                "atol": args.atol,
                "include_trajectories": args.include_trajectories,
            },
        },
        "cases": cases,
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"cases={len(cases)}")
    return 0


def run_verify_static_artifacts_command(args: argparse.Namespace) -> int:
    require_profiles, require_feature_set_sha256 = _resolve_static_artifact_claim_requirements(
        args.require_profile,
        args.require_feature_set_sha256,
        require_public_claim=args.require_public_claim,
        require_current_feature_set=args.require_current_feature_set,
    )
    result = (
        verify_static_artifacts_from_url(
            args.base_url,
            require_commit=args.require_commit,
            require_gates=args.require_gate,
            require_minimums=args.require_min,
            require_maximums=args.require_max,
            require_profiles=require_profiles,
            require_features=args.require_feature,
            require_feature_set_sha256=require_feature_set_sha256,
        )
        if args.base_url
        else verify_static_artifacts(
            args.site_dir,
            require_commit=args.require_commit,
            require_gates=args.require_gate,
            require_minimums=args.require_min,
            require_maximums=args.require_max,
            require_profiles=require_profiles,
            require_features=args.require_feature,
            require_feature_set_sha256=require_feature_set_sha256,
        )
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 1


def verify_static_artifacts(
    site_dir: Path,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_profiles: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
    require_public_claim: bool = False,
) -> dict[str, object]:
    artifacts, artifact_errors = _read_static_artifacts_from_dir(site_dir)
    return verify_static_artifact_bytes(
        artifacts,
        source=str(site_dir),
        artifact_errors=artifact_errors,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_profiles=require_profiles,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=require_public_claim,
    )


def verify_static_artifacts_from_url(
    base_url: str,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_profiles: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
    require_public_claim: bool = False,
) -> dict[str, object]:
    normalized_base_url = base_url if base_url.endswith("/") else f"{base_url}/"
    artifacts, artifact_errors = _fetch_static_artifacts_from_url(normalized_base_url)
    return verify_static_artifact_bytes(
        artifacts,
        source=normalized_base_url,
        artifact_errors=artifact_errors,
        require_commit=require_commit,
        require_gates=require_gates,
        require_minimums=require_minimums,
        require_maximums=require_maximums,
        require_profiles=require_profiles,
        require_features=require_features,
        require_feature_set_sha256=require_feature_set_sha256,
        require_public_claim=require_public_claim,
    )


def verify_static_artifact_bytes(
    artifacts: dict[str, bytes],
    source: str,
    artifact_errors: dict[str, str | None] | None = None,
    require_commit: str | None = None,
    require_gates: Sequence[str] | None = None,
    require_minimums: Sequence[str] | None = None,
    require_maximums: Sequence[str] | None = None,
    require_profiles: Sequence[str] | None = None,
    require_features: Sequence[str] | None = None,
    require_feature_set_sha256: str | None = None,
    require_public_claim: bool = False,
) -> dict[str, object]:
    require_profiles, require_feature_set_sha256 = _resolve_static_artifact_claim_requirements(
        require_profiles,
        require_feature_set_sha256,
        require_public_claim=require_public_claim,
    )
    artifacts, artifact_payload_errors, provided_artifact_names = _normalize_static_artifact_bytes(artifacts)
    artifact_errors = _normalize_artifact_errors(artifact_errors, provided_artifact_names, artifact_payload_errors)
    manifest, manifest_parse_error = _json_object_from_bytes(artifacts["manifest.json"])
    certificate, certificate_parse_error = _json_object_from_bytes(artifacts["certificate.json"])
    certificate_provenance = _dict_field(certificate, "build_provenance")
    manifest_provenance = _dict_field(manifest, "build_provenance")
    certificate_commit = certificate_provenance.get("commit_sha")
    manifest_commit = manifest_provenance.get("commit_sha")
    profile_requirements = _static_artifact_profile_requirements(require_profiles)
    profile_hashes = _static_artifact_profile_hashes(require_profiles)
    required_profile_results = _required_profile_results(certificate, profile_hashes)
    expanded_required_gates = _merge_requirements(profile_requirements["require_gates"], require_gates)
    expanded_required_minimums = _merge_requirements(profile_requirements["require_minimums"], require_minimums)
    expanded_required_maximums = _merge_requirements(profile_requirements["require_maximums"], require_maximums)
    verification_schema_features = list(STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    required_gate_results = _required_gate_results(certificate, expanded_required_gates)
    required_minimum_results = _required_minimum_results(certificate, expanded_required_minimums)
    required_maximum_results = _required_maximum_results(certificate, expanded_required_maximums)
    expanded_required_features = _merge_requirements(profile_requirements["require_features"], require_features)
    required_feature_results = _required_feature_results(expanded_required_features, verification_schema_features)
    verification_schema_features_sha256 = static_artifact_verification_features_sha256(verification_schema_features)
    certificate_verification_schema_features = certificate.get("verification_schema_features")
    certificate_verification_schema_features_sha256 = certificate.get("verification_schema_features_sha256")
    checks = {
        **_artifact_available_checks(artifact_errors),
        "manifest_json": manifest_parse_error is None,
        "manifest_schema": manifest.get("manifest_schema_version") == 1,
        "manifest_artifact": manifest.get("artifact") == "threebody-static-site-manifest",
        "manifest_hash_algorithm": manifest.get("hash_algorithm") == "sha256",
        "certificate_json": certificate_parse_error is None,
        "certificate_schema": certificate.get("certificate_schema_version") == 1,
        "certificate_artifact": certificate.get("artifact") == "threebody-static-research-certificate",
        "certificate_manifest_link": certificate.get("artifact_manifest") == "manifest.json",
        "certificate_verification_schema_features": _certificate_verification_schema_features_match(
            certificate_verification_schema_features,
            verification_schema_features,
        ),
        "certificate_verification_schema_features_sha256": certificate_verification_schema_features_sha256
        == verification_schema_features_sha256,
        "publication_pipeline_links": _publication_pipeline_links_match(certificate),
        "provenance_commit_match": _provenance_commits_match(certificate_commit, manifest_commit),
        "required_commit": _required_commit_matches(certificate_commit, manifest_commit, require_commit),
        "required_profile_hashes": all(row["passed"] for row in required_profile_results),
        "required_gates": all(required_gate_results.values()),
        "required_minimums": all(row["passed"] for row in required_minimum_results),
        "required_maximums": all(row["passed"] for row in required_maximum_results),
        "required_features": all(row["passed"] for row in required_feature_results),
        "required_feature_set_sha256": _required_feature_set_sha256_matches(
            verification_schema_features_sha256,
            require_feature_set_sha256,
        ),
        "index_certificate_link": _index_links_to_artifact(artifacts["index.html"], "certificate.json"),
        "index_manifest_link": _index_links_to_artifact(artifacts["index.html"], "manifest.json"),
        "index_favicon_link": _index_links_to_artifact(artifacts["index.html"], "favicon.svg"),
        "index_hash": _manifest_hash_matches(manifest, "index.html", artifacts["index.html"]),
        "certificate_hash": _manifest_hash_matches(manifest, "certificate.json", artifacts["certificate.json"]),
        "favicon_hash": _manifest_hash_matches(manifest, "favicon.svg", artifacts["favicon.svg"]),
        "gitattributes_hash": _manifest_hash_matches(manifest, ".gitattributes", artifacts[".gitattributes"]),
        "index_size": _manifest_size_matches(manifest, "index.html", artifacts["index.html"]),
        "certificate_size": _manifest_size_matches(manifest, "certificate.json", artifacts["certificate.json"]),
        "favicon_size": _manifest_size_matches(manifest, "favicon.svg", artifacts["favicon.svg"]),
        "gitattributes_size": _manifest_size_matches(manifest, ".gitattributes", artifacts[".gitattributes"]),
        "gitattributes_policy": artifacts[".gitattributes"] == STATIC_SITE_GITATTRIBUTES_POLICY,
    }
    receipt = {
        "verification_schema_version": 1,
        "verification_schema_features": verification_schema_features,
        "verification_schema_features_sha256": verification_schema_features_sha256,
        "certificate_verification_schema_features": certificate_verification_schema_features,
        "certificate_verification_schema_features_sha256": certificate_verification_schema_features_sha256,
        "verified_at_utc": _utc_timestamp(),
        "verifier": "threebody.cli verify-static-artifacts",
        "verified": all(checks.values()),
        "source": source,
        "required_commit": require_commit,
        "required_profiles": list(require_profiles or []),
        "required_features": expanded_required_features,
        "required_feature_set_sha256": require_feature_set_sha256,
        "required_feature_results": required_feature_results,
        "required_profile_requirements": profile_requirements,
        "required_profile_hashes": profile_hashes,
        "required_profile_results": required_profile_results,
        "required_gates": expanded_required_gates,
        "required_gate_results": required_gate_results,
        "required_minimums": expanded_required_minimums,
        "required_minimum_results": required_minimum_results,
        "required_maximums": expanded_required_maximums,
        "required_maximum_results": required_maximum_results,
        "commit_sha": certificate_commit,
        "commit_sha_short": certificate_provenance.get("commit_sha_short"),
        "parse_errors": {
            "manifest.json": manifest_parse_error,
            "certificate.json": certificate_parse_error,
        },
        "artifact_errors": artifact_errors,
        "checks": checks,
    }
    receipt["receipt_payload_sha256"] = static_artifact_receipt_payload_sha256(receipt)
    return receipt


def _read_static_artifacts_from_dir(site_dir: Path) -> tuple[dict[str, bytes], dict[str, str | None]]:
    artifacts: dict[str, bytes] = {}
    artifact_errors: dict[str, str | None] = {}
    for name in STATIC_SITE_BUNDLE_NAMES:
        try:
            artifacts[name] = (site_dir / name).read_bytes()
            artifact_errors[name] = None
        except OSError as exc:
            artifacts[name] = b""
            artifact_errors[name] = str(exc)
    return artifacts, artifact_errors


def _fetch_static_artifacts_from_url(base_url: str) -> tuple[dict[str, bytes], dict[str, str | None]]:
    artifacts: dict[str, bytes] = {}
    artifact_errors: dict[str, str | None] = {}
    for name in STATIC_SITE_BUNDLE_NAMES:
        try:
            artifacts[name] = _fetch_url_bytes(urljoin(base_url, name))
            artifact_errors[name] = None
        except (HTTPError, URLError, OSError) as exc:
            artifacts[name] = b""
            artifact_errors[name] = str(exc)
    return artifacts, artifact_errors


def _artifact_available_checks(artifact_errors: dict[str, str | None]) -> dict[str, bool]:
    return {
        f"{_artifact_check_prefix(name)}_available": artifact_errors.get(name) is None
        for name in STATIC_SITE_BUNDLE_NAMES
    }


def _artifact_check_prefix(artifact_name: str) -> str:
    if artifact_name == ".gitattributes":
        return "gitattributes"
    return artifact_name.rsplit(".", 1)[0]


class _ArtifactLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for attr_name, attr_value in attrs:
            if attr_name in {"href", "src"} and attr_value is not None:
                self.references.add(attr_value)


def _index_links_to_artifact(index_bytes: bytes, artifact_name: str) -> bool:
    try:
        index_html = index_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return False
    parser = _ArtifactLinkParser()
    parser.feed(index_html)
    return any(_artifact_reference_matches(reference, artifact_name) for reference in parser.references)


def _artifact_reference_matches(reference: str, artifact_name: str) -> bool:
    normalized = reference.split("#", 1)[0].split("?", 1)[0].replace("\\", "/")
    return normalized in {artifact_name, f"./{artifact_name}"}


def _normalize_static_artifact_bytes(
    artifacts: object,
) -> tuple[dict[str, bytes], dict[str, str], set[str]]:
    normalized: dict[str, bytes] = {}
    payload_errors: dict[str, str] = {}
    if not isinstance(artifacts, Mapping):
        message = f"artifacts is {type(artifacts).__name__}, expected mapping"
        return {name: b"" for name in STATIC_SITE_BUNDLE_NAMES}, {
            name: message for name in STATIC_SITE_BUNDLE_NAMES
        }, set()
    provided_artifact_names = {str(name) for name in artifacts}
    for name in STATIC_SITE_BUNDLE_NAMES:
        payload = artifacts.get(name, b"")
        if isinstance(payload, bytes):
            normalized[name] = payload
        elif isinstance(payload, bytearray):
            normalized[name] = bytes(payload)
        else:
            normalized[name] = b""
            payload_errors[name] = f"artifact payload is {type(payload).__name__}, expected bytes-like"
    return normalized, payload_errors, provided_artifact_names


def _normalize_artifact_errors(
    artifact_errors: object,
    provided_artifact_names: set[str],
    artifact_payload_errors: dict[str, str] | None = None,
) -> dict[str, str | None]:
    normalized: dict[str, str | None] = {}
    artifact_payload_errors = artifact_payload_errors or {}
    explicit_errors = artifact_errors if isinstance(artifact_errors, Mapping) else {}
    malformed_error_map = (
        f"artifact_errors is {type(artifact_errors).__name__}, expected mapping"
        if artifact_errors is not None and not isinstance(artifact_errors, Mapping)
        else None
    )
    for name in STATIC_SITE_BUNDLE_NAMES:
        explicit_error = explicit_errors.get(name)
        normalized_error = str(explicit_error) if explicit_error is not None else None
        payload_error = artifact_payload_errors.get(name)
        if normalized_error is not None and payload_error is not None:
            normalized[name] = f"{normalized_error}; {payload_error}"
        elif normalized_error is not None:
            normalized[name] = normalized_error
        elif payload_error is not None:
            normalized[name] = payload_error
        elif malformed_error_map is not None:
            normalized[name] = malformed_error_map
        elif name not in provided_artifact_names:
            normalized[name] = "artifact missing from provided bytes"
        else:
            normalized[name] = None
    return normalized


def _json_object_from_bytes(payload: bytes) -> tuple[dict[str, object], str | None]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, str(exc)
    if not isinstance(value, dict):
        return {}, "top-level JSON value is not an object"
    return value, None


def _manifest_hash_matches(manifest: dict[str, object], artifact_name: str, artifact_bytes: bytes) -> bool:
    artifact = _dict_field(_dict_field(manifest, "artifacts"), artifact_name)
    return artifact.get("sha256") == _sha256_bytes(artifact_bytes)


def _manifest_size_matches(manifest: dict[str, object], artifact_name: str, artifact_bytes: bytes) -> bool:
    artifact = _dict_field(_dict_field(manifest, "artifacts"), artifact_name)
    return artifact.get("bytes") == len(artifact_bytes)


def _publication_pipeline_links_match(certificate: dict[str, object]) -> bool:
    publication_pipeline = _dict_field(certificate, "publication_pipeline")
    return (
        publication_pipeline.get("engine") == "threebody.ui.static_site"
        and publication_pipeline.get("machine_readable_certificate") == "certificate.json"
        and publication_pipeline.get("integrity_manifest") == "manifest.json"
    )


def _certificate_verification_schema_features_match(
    certificate_features: object,
    expected_features: Sequence[str],
) -> bool:
    return certificate_features == list(expected_features)


def _provenance_commits_match(certificate_commit: object, manifest_commit: object) -> bool:
    return (
        isinstance(certificate_commit, str)
        and bool(certificate_commit)
        and isinstance(manifest_commit, str)
        and bool(manifest_commit)
        and certificate_commit == manifest_commit
    )


def _dict_field(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _required_commit_matches(
    certificate_commit: object,
    manifest_commit: object,
    required_commit: str | None,
) -> bool:
    if not required_commit:
        return True
    if not isinstance(certificate_commit, str) or not isinstance(manifest_commit, str):
        return False
    return certificate_commit.startswith(required_commit) and manifest_commit.startswith(required_commit)


def _required_gate_results(certificate: dict[str, object], required_gates: Sequence[str] | None) -> dict[str, bool]:
    promotion_gates = certificate.get("promotion_gates", {})
    if not isinstance(promotion_gates, dict):
        promotion_gates = {}
    return {gate: promotion_gates.get(gate) is True for gate in required_gates or []}


def _static_artifact_profile_requirements(required_profiles: Sequence[str] | None) -> dict[str, list[str]]:
    requirements: dict[str, list[str]] = {
        "require_gates": [],
        "require_minimums": [],
        "require_maximums": [],
        "require_features": [],
    }
    for profile_name in required_profiles or []:
        profile = STATIC_ARTIFACT_REQUIREMENT_PROFILES.get(profile_name)
        if profile is None:
            raise ValueError(f"Unknown verification profile: {profile_name}")
        for key in requirements:
            requirements[key].extend(profile[key])
    return {key: _unique_requirements(values) for key, values in requirements.items()}


def _static_artifact_profile_hashes(required_profiles: Sequence[str] | None) -> dict[str, str]:
    return {
        profile_name: static_artifact_requirement_profile_sha256(profile_name)
        for profile_name in _unique_requirements(required_profiles or [])
    }


def _required_profile_results(certificate: dict[str, object], required_profile_hashes: dict[str, str]) -> list[dict[str, object]]:
    if not required_profile_hashes:
        return []
    verification_profiles = certificate.get("verification_profiles", {})
    if not isinstance(verification_profiles, dict):
        verification_profiles = {}
    publication_pipeline = certificate.get("publication_pipeline", {})
    if not isinstance(publication_pipeline, dict):
        publication_pipeline = {}
    active_profile = publication_pipeline.get("verification_profile")
    active_hash = publication_pipeline.get("verification_profile_sha256")

    results = []
    for profile_name, profile_hash in required_profile_hashes.items():
        declared_hashes = []
        profile_descriptor = verification_profiles.get(profile_name)
        expected_descriptor = static_artifact_requirement_profile_descriptor(profile_name)
        descriptor_without_hash = None
        descriptor_matches = False
        descriptor_hash_matches = False
        if isinstance(profile_descriptor, dict):
            descriptor_hash = profile_descriptor.get("sha256")
            descriptor_without_hash = {key: value for key, value in profile_descriptor.items() if key != "sha256"}
            descriptor_matches = descriptor_without_hash == expected_descriptor
            descriptor_hash_matches = descriptor_hash == profile_hash
            if descriptor_hash is not None:
                declared_hashes.append(descriptor_hash)
        active_hash_matches = active_profile == profile_name and active_hash == profile_hash
        if active_hash is not None:
            declared_hashes.append(active_hash)
        active_matches = active_profile == profile_name
        hash_matches = active_hash_matches and descriptor_hash_matches
        results.append(
            {
                "profile": profile_name,
                "active_profile": active_profile,
                "expected_sha256": profile_hash,
                "declared_sha256": declared_hashes,
                "active_matches": active_matches,
                "active_sha256": active_hash,
                "active_hash_matches": active_hash_matches,
                "descriptor": descriptor_without_hash,
                "descriptor_matches": descriptor_matches,
                "descriptor_hash_matches": descriptor_hash_matches,
                "hash_matches": hash_matches,
                "passed": active_matches and hash_matches and descriptor_matches,
            }
        )
    return results


def _required_feature_results(
    required_features: Sequence[str] | None,
    verification_schema_features: Sequence[str],
) -> list[dict[str, object]]:
    available_features = set(verification_schema_features)
    return [
        {
            "feature": feature,
            "passed": feature in available_features,
        }
        for feature in (required_features or [])
    ]


def _required_feature_set_sha256_matches(actual_sha256: str, required_sha256: str | None) -> bool:
    return required_sha256 is None or actual_sha256 == required_sha256


def _resolve_static_artifact_claim_requirements(
    require_profiles: Sequence[str] | None,
    require_feature_set_sha256: str | None,
    require_public_claim: bool = False,
    require_current_feature_set: bool = False,
) -> tuple[list[str], str | None]:
    resolved_profiles = _merge_requirements(
        [PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE] if require_public_claim else [],
        require_profiles,
    )
    resolved_feature_set_sha256 = (
        static_artifact_verification_features_sha256(STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
        if require_current_feature_set or (require_public_claim and require_feature_set_sha256 is None)
        else require_feature_set_sha256
    )
    return resolved_profiles, resolved_feature_set_sha256


def _merge_requirements(profile_requirements: Sequence[str], explicit_requirements: Sequence[str] | None) -> list[str]:
    return _unique_requirements([*profile_requirements, *(explicit_requirements or [])])


def _unique_requirements(requirements: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for requirement in requirements:
        if requirement in seen:
            continue
        seen.add(requirement)
        unique.append(requirement)
    return unique


def _required_minimum_results(certificate: dict[str, object], required_minimums: Sequence[str] | None) -> list[dict[str, object]]:
    return [_required_minimum_result(certificate, requirement) for requirement in required_minimums or []]


def _required_minimum_result(certificate: dict[str, object], requirement: str) -> dict[str, object]:
    path, threshold_text = _split_numeric_requirement(requirement, label="Minimum")
    observed = _lookup_dotted_path(certificate, path)
    try:
        threshold = float(threshold_text)
        observed_number = float(observed)
    except (TypeError, ValueError):
        return {
            "path": path,
            "threshold": threshold_text,
            "observed": observed,
            "passed": False,
        }
    return {
        "path": path,
        "threshold": threshold,
        "observed": observed_number,
        "passed": observed_number >= threshold,
    }


def _required_maximum_results(certificate: dict[str, object], required_maximums: Sequence[str] | None) -> list[dict[str, object]]:
    return [_required_maximum_result(certificate, requirement) for requirement in required_maximums or []]


def _required_maximum_result(certificate: dict[str, object], requirement: str) -> dict[str, object]:
    path, threshold_text = _split_numeric_requirement(requirement, label="Maximum")
    observed = _lookup_dotted_path(certificate, path)
    try:
        threshold = float(threshold_text)
        observed_number = float(observed)
    except (TypeError, ValueError):
        return {
            "path": path,
            "threshold": threshold_text,
            "observed": observed,
            "passed": False,
        }
    return {
        "path": path,
        "threshold": threshold,
        "observed": observed_number,
        "passed": observed_number <= threshold,
    }


def _split_numeric_requirement(requirement: str, *, label: str) -> tuple[str, str]:
    if "=" in requirement:
        path, threshold = requirement.split("=", 1)
    elif ":" in requirement:
        path, threshold = requirement.split(":", 1)
    else:
        raise ValueError(f"{label} requirement must use PATH=VALUE: {requirement}")
    path = path.strip()
    threshold = threshold.strip()
    if not path or not threshold:
        raise ValueError(f"{label} requirement must use PATH=VALUE: {requirement}")
    return path, threshold


def _lookup_dotted_path(payload: dict[str, object], path: str) -> object:
    value: object = payload
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fetch_url_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "threebody-cli/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def _sha256_bytes(artifact_bytes: bytes) -> str:
    return hashlib.sha256(artifact_bytes).hexdigest()


def _scenario_from_args(args: argparse.Namespace) -> Scenario:
    library = OrbitLibrary()
    return _scenario_from_name(library, args.scenario, periods=args.periods, samples=args.samples)


def _scenario_from_name(library: OrbitLibrary, scenario: str, periods: float, samples: int) -> Scenario:
    if scenario == "figure-eight":
        return library.general_figure_eight(periods=periods, samples=samples)
    if scenario == "hierarchical-flyby":
        return library.general_hierarchical_flyby(duration=periods, samples=samples)
    if scenario == "restricted-l4":
        return library.restricted_l4(periods=periods, samples=samples)
    if scenario == "restricted-l5":
        return library.restricted_l5(periods=periods, samples=samples)
    raise ValueError(f"Unknown scenario: {scenario}")


def _read_prediction_input(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("prediction input JSON must be an object.")
    return value


def _required_prediction_field(payload: dict[str, object], key: str) -> object:
    if key not in payload:
        raise ValueError(f"prediction input JSON must include {key!r}.")
    return payload[key]


def _write_json_result(result: dict[str, object], output: Path | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    if output is None:
        print(text)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def _default_output_path(scenario: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(".runtime") / "research_runs" / f"{stamp}-{scenario}.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
