from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from math import pi
from pathlib import Path
from typing import Sequence

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
    verify_static = subparsers.add_parser(
        "verify-static-artifacts",
        help="Verify static Pages certificate and manifest artifact integrity.",
    )
    verify_static.add_argument(
        "--site-dir",
        type=Path,
        default=Path("site"),
        help="Directory containing index.html, certificate.json, and manifest.json.",
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
    result = verify_static_artifacts(args.site_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 1


def verify_static_artifacts(site_dir: Path) -> dict[str, object]:
    manifest_path = site_dir / "manifest.json"
    certificate_path = site_dir / "certificate.json"
    index_path = site_dir / "index.html"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    checks = {
        "manifest_schema": manifest.get("manifest_schema_version") == 1,
        "certificate_schema": certificate.get("certificate_schema_version") == 1,
        "certificate_manifest_link": certificate.get("artifact_manifest") == "manifest.json",
        "provenance_commit_match": (
            certificate.get("build_provenance", {}).get("commit_sha")
            == manifest.get("build_provenance", {}).get("commit_sha")
        ),
        "index_hash": _manifest_hash_matches(manifest, "index.html", index_path),
        "certificate_hash": _manifest_hash_matches(manifest, "certificate.json", certificate_path),
        "index_size": _manifest_size_matches(manifest, "index.html", index_path),
        "certificate_size": _manifest_size_matches(manifest, "certificate.json", certificate_path),
    }
    return {
        "verified": all(checks.values()),
        "site_dir": str(site_dir),
        "commit_sha_short": certificate.get("build_provenance", {}).get("commit_sha_short"),
        "checks": checks,
    }


def _manifest_hash_matches(manifest: dict[str, object], artifact_name: str, path: Path) -> bool:
    artifact = manifest.get("artifacts", {}).get(artifact_name, {})
    return artifact.get("sha256") == _sha256(path)


def _manifest_size_matches(manifest: dict[str, object], artifact_name: str, path: Path) -> bool:
    artifact = manifest.get("artifacts", {}).get(artifact_name, {})
    return artifact.get("bytes") == path.stat().st_size


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _default_output_path(scenario: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(".runtime") / "research_runs" / f"{stamp}-{scenario}.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
