from __future__ import annotations

from dataclasses import dataclass, field

from ..types import TrajectoryResult
from .atlas import AnalysisAtlas
from .boundaries import estimate_transition_boundaries, transition_boundary_rows
from .hysteresis import detect_hysteresis_loops, hysteresis_loop_rows
from .transition_graph import TransitionGraph
from .transition_model import FeatureConditionedTransitionModel, transition_samples_from_reports
from .types import AnalysisReport
from .events import transition_event_evidence, transition_event_rows
from .word_algebra import refined_word_signature_rows, return_word_signature_rows, word_signature_rows


@dataclass(frozen=True, slots=True)
class TransitionSurveyResult:
    reports_by_name: dict[str, tuple[AnalysisReport, ...]]
    graph: TransitionGraph
    model: FeatureConditionedTransitionModel

    def chart_distribution_rows(self) -> list[dict[str, float | str]]:
        rows: list[dict[str, float | str]] = []
        for name, reports in self.reports_by_name.items():
            distribution = AnalysisAtlas.chart_distribution(reports)
            for chart, share in distribution.items():
                rows.append({"scenario": name, "chart": str(chart), "share": share})
        return rows

    def transition_event_rows(self) -> list[dict[str, float | int | str]]:
        return transition_event_rows(transition_event_evidence(self.reports_by_name))

    def transition_boundary_rows(self, coordinate: str = "hierarchy_perturbation_strength") -> list[dict[str, float | int | str]]:
        return transition_boundary_rows(estimate_transition_boundaries(self.reports_by_name, coordinate=coordinate))

    def hysteresis_loop_rows(self, coordinate: str = "hierarchy_perturbation_strength") -> list[dict[str, float | int | str | bool]]:
        estimates = estimate_transition_boundaries(self.reports_by_name, coordinate=coordinate)
        return hysteresis_loop_rows(detect_hysteresis_loops(estimates))

    def word_signature_rows(self) -> list[dict[str, float | int | str | bool]]:
        return word_signature_rows(self.reports_by_name)

    def refined_word_signature_rows(self) -> list[dict[str, float | int | str | bool]]:
        return refined_word_signature_rows(self.reports_by_name)

    def return_word_signature_rows(
        self,
        coordinate: str = "hierarchy_ratio",
    ) -> list[dict[str, float | int | str | bool]]:
        return return_word_signature_rows(self.reports_by_name, coordinate=coordinate)


@dataclass(slots=True)
class TransitionSurvey:
    """Batch analysis loop for building transition evidence from trajectories."""

    atlas: AnalysisAtlas = field(default_factory=AnalysisAtlas)

    def run(
        self,
        cases: dict[str, tuple[object, TrajectoryResult]],
        stride: int = 1,
    ) -> TransitionSurveyResult:
        graph = TransitionGraph()
        all_samples = []
        reports_by_name: dict[str, tuple[AnalysisReport, ...]] = {}

        for name, (system, trajectory) in cases.items():
            reports = self.atlas.analyze_trajectory(system, trajectory, stride=stride)
            reports_by_name[name] = reports
            graph.add(self.atlas.transitions(system, trajectory, stride=stride))
            all_samples.extend(transition_samples_from_reports(reports))

        model = FeatureConditionedTransitionModel()
        model.fit(all_samples)
        if not model.graph.counts:
            model.graph = graph

        return TransitionSurveyResult(
            reports_by_name=reports_by_name,
            graph=graph,
            model=model,
        )
