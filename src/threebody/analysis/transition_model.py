from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .coordinates import GeneralThreeBodyFeatures, RestrictedThreeBodyFeatures
from .transition_graph import TransitionGraph
from .types import AnalysisReport, ChartType


@dataclass(frozen=True, slots=True)
class TransitionSample:
    previous: ChartType
    current: ChartType
    features: np.ndarray
    feature_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransitionPrediction:
    previous: ChartType
    current: ChartType
    score: float
    prior: float
    feature_distance: float
    samples: int


@dataclass(slots=True)
class FeatureConditionedTransitionModel:
    """Prototype model for chart transitions conditioned on state features."""

    graph: TransitionGraph = field(default_factory=TransitionGraph)
    centroids: dict[tuple[ChartType, ChartType], np.ndarray] = field(default_factory=dict)
    scales: dict[tuple[ChartType, ChartType], np.ndarray] = field(default_factory=dict)
    sample_counts: dict[tuple[ChartType, ChartType], int] = field(default_factory=dict)
    feature_names: tuple[str, ...] = ()

    def fit(self, samples: list[TransitionSample] | tuple[TransitionSample, ...]) -> None:
        if not samples:
            return
        self.feature_names = samples[0].feature_names
        grouped: dict[tuple[ChartType, ChartType], list[np.ndarray]] = {}
        for sample in samples:
            if sample.feature_names != self.feature_names:
                raise ValueError("All transition samples must use the same feature names.")
            key = (sample.previous, sample.current)
            grouped.setdefault(key, []).append(np.asarray(sample.features, dtype=float))
            self.graph.counts[key] = self.graph.counts.get(key, 0) + 1

        for key, vectors in grouped.items():
            matrix = np.vstack(vectors)
            self.centroids[key] = np.mean(matrix, axis=0)
            scale = np.std(matrix, axis=0)
            self.scales[key] = np.where(scale < 1.0e-9, 1.0, scale)
            self.sample_counts[key] = matrix.shape[0]

    def predict(
        self,
        previous: ChartType,
        features: np.ndarray,
        top_k: int = 3,
    ) -> tuple[TransitionPrediction, ...]:
        features = np.asarray(features, dtype=float)
        predictions: list[TransitionPrediction] = []
        for source, target in self.centroids:
            if source != previous:
                continue
            key = (source, target)
            centroid = self.centroids[key]
            scale = self.scales[key]
            normalized = (features - centroid) / scale
            distance = float(np.linalg.norm(normalized))
            prior = float(self.graph.probability(source, target))
            score = prior * float(np.exp(-0.5 * distance))
            predictions.append(
                TransitionPrediction(
                    previous=source,
                    current=target,
                    score=score,
                    prior=prior,
                    feature_distance=distance,
                    samples=self.sample_counts[key],
                )
            )
        return tuple(sorted(predictions, key=lambda item: item.score, reverse=True)[:top_k])

    @classmethod
    def from_reports(cls, reports: tuple[AnalysisReport, ...] | list[AnalysisReport]) -> FeatureConditionedTransitionModel:
        samples = transition_samples_from_reports(reports)
        model = cls()
        model.fit(samples)
        return model


def transition_samples_from_reports(reports: tuple[AnalysisReport, ...] | list[AnalysisReport]) -> list[TransitionSample]:
    samples: list[TransitionSample] = []
    if len(reports) < 2:
        return samples

    feature_names = feature_names_for_report(reports[0])
    for previous_report, current_report in zip(reports, reports[1:], strict=False):
        previous = previous_report.primary_chart
        current = current_report.primary_chart
        if previous == current:
            continue
        names = feature_names_for_report(current_report)
        if names != feature_names:
            continue
        samples.append(
            TransitionSample(
                previous=previous,
                current=current,
                features=feature_vector_for_report(current_report),
                feature_names=names,
            )
        )
    return samples


def feature_names_for_report(report: AnalysisReport) -> tuple[str, ...]:
    features = report.features
    if isinstance(features, GeneralThreeBodyFeatures):
        return (
            "nearest_distance",
            "outer_distance",
            "hierarchy_ratio",
            "virial_ratio",
            "total_energy",
            "angular_momentum_norm",
            "escape_index",
        )
    if isinstance(features, RestrictedThreeBodyFeatures):
        return (
            "nearest_primary_distance",
            "nearest_lagrange_distance",
            "jacobi_constant",
            "speed",
            "gateway_margin",
        )
    raise TypeError(f"Unsupported report feature type: {type(features)!r}")


def feature_vector_for_report(report: AnalysisReport) -> np.ndarray:
    features = report.features
    if isinstance(features, GeneralThreeBodyFeatures):
        return np.array(
            [
                features.nearest_distance,
                features.outer_distance,
                features.hierarchy_ratio,
                features.virial_ratio,
                features.total_energy,
                features.angular_momentum_norm,
                features.escape_index,
            ],
            dtype=float,
        )
    if isinstance(features, RestrictedThreeBodyFeatures):
        return np.array(
            [
                float(np.min(features.distances_to_primaries)),
                features.nearest_lagrange_distance,
                features.jacobi_constant,
                features.speed,
                features.gateway_margin,
            ],
            dtype=float,
        )
    raise TypeError(f"Unsupported report feature type: {type(features)!r}")
