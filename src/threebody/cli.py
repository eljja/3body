from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from math import pi
from pathlib import Path
from typing import Sequence

from .analysis import ResearchPipeline
from .experiments import (
    BoundaryResolutionStudy,
    ClassifierArtifactStudy,
    FigureEightStabilityProbe,
    HierarchicalFlybySweep,
    IntegratorComparisonStudy,
    KnownBenchmarkSuite,
    OrbitLibrary,
    RegimeProbeSuite,
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
        },
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"artifact_cases={len(artifact)} benchmarks={len(benchmarks)} regimes={len(regimes)}")
    return 0


def _scenario_from_args(args: argparse.Namespace) -> Scenario:
    library = OrbitLibrary()
    if args.scenario == "figure-eight":
        return library.general_figure_eight(periods=args.periods, samples=args.samples)
    if args.scenario == "hierarchical-flyby":
        return library.general_hierarchical_flyby(duration=args.periods, samples=args.samples)
    if args.scenario == "restricted-l4":
        return library.restricted_l4(periods=args.periods, samples=args.samples)
    if args.scenario == "restricted-l5":
        return library.restricted_l5(periods=args.periods, samples=args.samples)
    raise ValueError(f"Unknown scenario: {args.scenario}")


def _default_output_path(scenario: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(".runtime") / "research_runs" / f"{stamp}-{scenario}.json"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
