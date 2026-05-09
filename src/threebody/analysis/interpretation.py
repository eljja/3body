from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..types import TrajectoryResult
from .atlas import AnalysisAtlas
from .error_bounds import chart_validity_bound
from .types import ChartTransition, ChartType


@dataclass(frozen=True, slots=True)
class InterpretationSegment:
    """One maximal trajectory interval interpreted by a single dominant chart."""

    start_index: int
    end_index: int
    start_time: float
    end_time: float
    chart: ChartType
    model_family: str
    local_claim: str
    validity_statement: str
    qualitative_error_bound: str
    confidence_min: float
    confidence_mean: float
    unresolved_obligations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, float | int | str | list[str]]:
        return {
            "start_index": self.start_index,
            "end_index": self.end_index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "chart": self.chart.value,
            "model_family": self.model_family,
            "local_claim": self.local_claim,
            "validity_statement": self.validity_statement,
            "qualitative_error_bound": self.qualitative_error_bound,
            "confidence_min": self.confidence_min,
            "confidence_mean": self.confidence_mean,
            "unresolved_obligations": list(self.unresolved_obligations),
        }


@dataclass(frozen=True, slots=True)
class TrajectoryInterpretation:
    """Structured, falsifiable interpretation of one trajectory."""

    method_statement: str
    segments: tuple[InterpretationSegment, ...]
    transitions: tuple[ChartTransition, ...]
    chart_distribution: dict[ChartType, float] = field(default_factory=dict)

    @property
    def unresolved_obligations(self) -> tuple[str, ...]:
        obligations = []
        for segment in self.segments:
            obligations.extend(segment.unresolved_obligations)
        return tuple(dict.fromkeys(obligations))

    def as_dict(self) -> dict[str, object]:
        return {
            "method_statement": self.method_statement,
            "segments": [segment.as_dict() for segment in self.segments],
            "transitions": [
                {
                    "index": transition.index,
                    "time": transition.time,
                    "previous": transition.previous.value,
                    "current": transition.current.value,
                    "reason": transition.reason,
                }
                for transition in self.transitions
            ],
            "chart_distribution": {chart.value: fraction for chart, fraction in self.chart_distribution.items()},
            "unresolved_obligations": list(self.unresolved_obligations),
        }


@dataclass(slots=True)
class ThreeBodyInterpreter:
    """Convert a numerical trajectory into chart-local analytic claims."""

    atlas: AnalysisAtlas = field(default_factory=AnalysisAtlas)

    def interpret(self, system: object, trajectory: TrajectoryResult, stride: int = 10) -> TrajectoryInterpretation:
        if stride < 1:
            raise ValueError("stride must be >= 1.")
        reports = self.atlas.analyze_trajectory(system, trajectory, stride=stride)
        transitions = self.atlas.transitions(system, trajectory, stride=stride)
        segments = _segments_from_reports(reports, trajectory, stride)
        return TrajectoryInterpretation(
            method_statement=(
                "No global closed form is asserted. The trajectory is interpreted by a finite atlas of local "
                "charts, each with an explicit model family, validity statement, and unresolved proof obligation."
            ),
            segments=segments,
            transitions=transitions,
            chart_distribution=self.atlas.chart_distribution(reports),
        )


def _segments_from_reports(
    reports: tuple[object, ...],
    trajectory: TrajectoryResult,
    stride: int,
) -> tuple[InterpretationSegment, ...]:
    if not reports:
        return ()
    segments = []
    start = 0
    current_chart = reports[0].primary_chart
    for index, report in enumerate(reports[1:], start=1):
        if report.primary_chart == current_chart:
            continue
        segments.append(_make_segment(reports[start:index], trajectory, stride, start, index - 1))
        start = index
        current_chart = report.primary_chart
    segments.append(_make_segment(reports[start:], trajectory, stride, start, len(reports) - 1))
    return tuple(segments)


def _make_segment(
    reports: tuple[object, ...],
    trajectory: TrajectoryResult,
    stride: int,
    report_start: int,
    report_end: int,
) -> InterpretationSegment:
    chart = reports[0].primary_chart
    model = _model_for_chart(chart)
    bound = chart_validity_bound(reports[0])
    confidences = np.asarray([report.confidence for report in reports], dtype=float)
    start_index = min(report_start * stride, len(trajectory.t) - 1)
    end_index = min(report_end * stride, len(trajectory.t) - 1)
    return InterpretationSegment(
        start_index=start_index,
        end_index=end_index,
        start_time=float(trajectory.t[start_index]),
        end_time=float(trajectory.t[end_index]),
        chart=chart,
        model_family=model["model_family"],
        local_claim=model["local_claim"],
        validity_statement=bound.statement,
        qualitative_error_bound=bound.qualitative_error_bound,
        confidence_min=float(np.min(confidences)),
        confidence_mean=float(np.mean(confidences)),
        unresolved_obligations=tuple(model["unresolved_obligations"]),
    )


def _model_for_chart(chart: ChartType) -> dict[str, str | tuple[str, ...]]:
    models: dict[ChartType, dict[str, str | tuple[str, ...]]] = {
        ChartType.TWO_BODY_HIERARCHY: {
            "model_family": "osculating_kepler_plus_tidal_perturbation",
            "local_claim": "Treat the tight pair as an osculating Kepler binary driven by third-body tidal forcing.",
            "unresolved_obligations": (
                "derive hierarchy action drift bounds",
                "separate resonant and nonresonant hierarchy intervals",
            ),
        },
        ChartType.CLOSE_ENCOUNTER: {
            "model_family": "regularized_collision_chart",
            "local_claim": "Raw coordinates are not analytic enough; switch to Levi-Civita/McGehee-style coordinates.",
            "unresolved_obligations": (
                "implement regularized flow",
                "prove equivalence between regularized and inertial charts away from collision",
            ),
        },
        ChartType.ESCAPE_TRANSPORT: {
            "model_family": "asymptotic_scattering_map",
            "local_claim": "Model the escaping body by outgoing Kepler elements and a finite-time scattering map.",
            "unresolved_obligations": (
                "prove outgoing element convergence",
                "bound finite-time escape classification error",
            ),
        },
        ChartType.RESTRICTED_LAGRANGE: {
            "model_family": "lagrange_normal_form",
            "local_claim": "Use local linearization, normal forms, and monodromy around Lagrange equilibria.",
            "unresolved_obligations": (
                "compute normal-form remainder bounds",
                "validate Floquet multipliers against reference values",
            ),
        },
        ChartType.RESTRICTED_GATEWAY: {
            "model_family": "neck_transport_manifold",
            "local_claim": "Use zero-velocity neck geometry and stable/unstable manifold transit certificates.",
            "unresolved_obligations": (
                "construct invariant manifold tubes",
                "bound Jacobi drift relative to gateway margin",
            ),
        },
        ChartType.PERIODIC_ORBIT_NEIGHBORHOOD: {
            "model_family": "periodic_orbit_monodromy",
            "local_claim": "Compare against nearby periodic orbit families and their variational monodromy.",
            "unresolved_obligations": (
                "compute monodromy over full periods",
                "derive local shadowing radius",
            ),
        },
        ChartType.CHAOTIC_TRANSPORT: {
            "model_family": "poincare_return_symbolic_dynamics",
            "local_claim": "Use return maps and symbolic chart words rather than scalar boundary collapse.",
            "unresolved_obligations": (
                "replace proxy return words with a true Poincare section",
                "prove branch-wise return-map error bounds",
            ),
        },
        ChartType.DEMOCRATIC_THREE_BODY: {
            "model_family": "shape_space_atlas",
            "local_claim": "Use reduced shape-scale coordinates because no pairwise Kepler hierarchy dominates.",
            "unresolved_obligations": (
                "derive shape-space chart covering inequalities",
                "separate democratic bounded motion from chaotic transport",
            ),
        },
    }
    return models[chart]
