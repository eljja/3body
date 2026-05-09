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
    proof_status: str
    interpretability_score: float
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
            "proof_status": self.proof_status,
            "interpretability_score": self.interpretability_score,
            "confidence_min": self.confidence_min,
            "confidence_mean": self.confidence_mean,
            "unresolved_obligations": list(self.unresolved_obligations),
        }


@dataclass(frozen=True, slots=True)
class InterpretationCertificate:
    """Summary of what kind of interpretation has actually been achieved."""

    local_interpretation_available: bool
    theorem_ready: bool
    regime_status: str
    segment_count: int
    transition_count: int
    minimum_confidence: float | None
    mean_interpretability_score: float | None
    primary_blockers: tuple[str, ...]
    path_to_solution: tuple[str, ...]

    def as_dict(self) -> dict[str, bool | float | int | str | list[str] | None]:
        return {
            "local_interpretation_available": self.local_interpretation_available,
            "theorem_ready": self.theorem_ready,
            "regime_status": self.regime_status,
            "segment_count": self.segment_count,
            "transition_count": self.transition_count,
            "minimum_confidence": self.minimum_confidence,
            "mean_interpretability_score": self.mean_interpretability_score,
            "primary_blockers": list(self.primary_blockers),
            "path_to_solution": list(self.path_to_solution),
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

    @property
    def certificate(self) -> InterpretationCertificate:
        if not self.segments:
            return InterpretationCertificate(
                local_interpretation_available=False,
                theorem_ready=False,
                regime_status="not_interpretable",
                segment_count=0,
                transition_count=len(self.transitions),
                minimum_confidence=None,
                mean_interpretability_score=None,
                primary_blockers=("no chart segment was classified",),
                path_to_solution=_path_to_solution(),
            )
        minimum_confidence = float(min(segment.confidence_min for segment in self.segments))
        mean_score = float(np.mean([segment.interpretability_score for segment in self.segments]))
        local_available = all(segment.model_family for segment in self.segments) and minimum_confidence > 0.0
        theorem_ready = local_available and not self.unresolved_obligations and minimum_confidence >= 0.5
        if theorem_ready:
            status = "theorem_ready"
        elif local_available:
            status = "locally_interpretable_not_theorem_ready"
        else:
            status = "not_interpretable"
        return InterpretationCertificate(
            local_interpretation_available=local_available,
            theorem_ready=theorem_ready,
            regime_status=status,
            segment_count=len(self.segments),
            transition_count=len(self.transitions),
            minimum_confidence=minimum_confidence,
            mean_interpretability_score=mean_score,
            primary_blockers=self.unresolved_obligations[:5],
            path_to_solution=_path_to_solution(),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "method_statement": self.method_statement,
            "certificate": self.certificate.as_dict(),
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
        proof_status=str(model["proof_status"]),
        interpretability_score=float(model["interpretability_score"]),
        confidence_min=float(np.min(confidences)),
        confidence_mean=float(np.mean(confidences)),
        unresolved_obligations=tuple(model["unresolved_obligations"]),
    )


def _model_for_chart(chart: ChartType) -> dict[str, str | tuple[str, ...]]:
    models: dict[ChartType, dict[str, str | tuple[str, ...]]] = {
        ChartType.TWO_BODY_HIERARCHY: {
            "model_family": "osculating_kepler_plus_tidal_perturbation",
            "local_claim": "Treat the tight pair as an osculating Kepler binary driven by third-body tidal forcing.",
            "proof_status": "perturbative_local_model_available",
            "interpretability_score": 0.7,
            "unresolved_obligations": (
                "derive hierarchy action drift bounds",
                "separate resonant and nonresonant hierarchy intervals",
            ),
        },
        ChartType.CLOSE_ENCOUNTER: {
            "model_family": "regularized_collision_chart",
            "local_claim": "Raw coordinates are not analytic enough; switch to Levi-Civita/McGehee-style coordinates.",
            "proof_status": "blocked_until_regularized_flow_exists",
            "interpretability_score": 0.25,
            "unresolved_obligations": (
                "implement regularized flow",
                "prove equivalence between regularized and inertial charts away from collision",
            ),
        },
        ChartType.ESCAPE_TRANSPORT: {
            "model_family": "asymptotic_scattering_map",
            "local_claim": "Model the escaping body by outgoing Kepler elements and a finite-time scattering map.",
            "proof_status": "asymptotic_model_available_but_unbounded",
            "interpretability_score": 0.45,
            "unresolved_obligations": (
                "prove outgoing element convergence",
                "bound finite-time escape classification error",
            ),
        },
        ChartType.RESTRICTED_LAGRANGE: {
            "model_family": "lagrange_normal_form",
            "local_claim": "Use local linearization, normal forms, and monodromy around Lagrange equilibria.",
            "proof_status": "local_linear_model_available",
            "interpretability_score": 0.65,
            "unresolved_obligations": (
                "compute normal-form remainder bounds",
                "validate Floquet multipliers against reference values",
            ),
        },
        ChartType.RESTRICTED_GATEWAY: {
            "model_family": "neck_transport_manifold",
            "local_claim": "Use zero-velocity neck geometry and stable/unstable manifold transit certificates.",
            "proof_status": "geometric_transport_model_available",
            "interpretability_score": 0.55,
            "unresolved_obligations": (
                "construct invariant manifold tubes",
                "bound Jacobi drift relative to gateway margin",
            ),
        },
        ChartType.PERIODIC_ORBIT_NEIGHBORHOOD: {
            "model_family": "periodic_orbit_monodromy",
            "local_claim": "Compare against nearby periodic orbit families and their variational monodromy.",
            "proof_status": "variational_local_model_available",
            "interpretability_score": 0.6,
            "unresolved_obligations": (
                "compute monodromy over full periods",
                "derive local shadowing radius",
            ),
        },
        ChartType.CHAOTIC_TRANSPORT: {
            "model_family": "poincare_return_symbolic_dynamics",
            "local_claim": "Use return maps and symbolic chart words rather than scalar boundary collapse.",
            "proof_status": "symbolic_proxy_available",
            "interpretability_score": 0.4,
            "unresolved_obligations": (
                "replace proxy return words with a true Poincare section",
                "prove branch-wise return-map error bounds",
            ),
        },
        ChartType.DEMOCRATIC_THREE_BODY: {
            "model_family": "shape_space_atlas",
            "local_claim": "Use reduced shape-scale coordinates because no pairwise Kepler hierarchy dominates.",
            "proof_status": "reduced_coordinate_model_available",
            "interpretability_score": 0.45,
            "unresolved_obligations": (
                "derive shape-space chart covering inequalities",
                "separate democratic bounded motion from chaotic transport",
            ),
        },
    }
    return models[chart]


def _path_to_solution() -> tuple[str, ...]:
    return (
        "cover the target regime with chart inequalities",
        "derive a local error bound for every active chart",
        "replace empirical transition labels with return-map or scattering-map laws",
        "validate branch-wise laws against negative controls and independent integrators",
        "prove collision regularization and escape asymptotic convergence where those charts appear",
    )
