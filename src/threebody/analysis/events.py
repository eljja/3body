from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .transition_model import feature_names_for_report, feature_vector_for_report
from .types import AnalysisReport, ChartType


@dataclass(frozen=True, slots=True)
class TransitionEventEvidence:
    scenario: str
    report_index: int
    previous: ChartType
    current: ChartType
    strongest_feature: str
    before: float
    after: float
    delta: float
    abs_delta: float


def transition_event_evidence(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
) -> tuple[TransitionEventEvidence, ...]:
    events: list[TransitionEventEvidence] = []
    for scenario, reports in reports_by_name.items():
        if len(reports) < 2:
            continue
        for index, (before_report, after_report) in enumerate(zip(reports, reports[1:], strict=False), start=1):
            if before_report.primary_chart == after_report.primary_chart:
                continue
            before_names = feature_names_for_report(before_report)
            after_names = feature_names_for_report(after_report)
            if before_names != after_names:
                continue
            before_vector = feature_vector_for_report(before_report)
            after_vector = feature_vector_for_report(after_report)
            delta = after_vector - before_vector
            finite_delta = np.where(np.isfinite(delta), delta, 0.0)
            strongest_index = int(np.argmax(np.abs(finite_delta)))
            events.append(
                TransitionEventEvidence(
                    scenario=scenario,
                    report_index=index,
                    previous=before_report.primary_chart,
                    current=after_report.primary_chart,
                    strongest_feature=before_names[strongest_index],
                    before=float(before_vector[strongest_index]),
                    after=float(after_vector[strongest_index]),
                    delta=float(finite_delta[strongest_index]),
                    abs_delta=float(abs(finite_delta[strongest_index])),
                )
            )
    return tuple(events)


def transition_event_rows(events: tuple[TransitionEventEvidence, ...] | list[TransitionEventEvidence]) -> list[dict[str, float | int | str]]:
    return [
        {
            "scenario": event.scenario,
            "report_index": event.report_index,
            "from": str(event.previous),
            "to": str(event.current),
            "strongest_feature": event.strongest_feature,
            "before": event.before,
            "after": event.after,
            "delta": event.delta,
            "abs_delta": event.abs_delta,
        }
        for event in events
    ]
