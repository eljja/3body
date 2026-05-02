from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .transition_model import TransitionSample
from .types import ChartType


@dataclass(frozen=True, slots=True)
class CandidateTransitionLaw:
    previous: ChartType
    current: ChartType
    feature: str
    lower: float
    upper: float
    center: float
    width: float
    support: int
    contrast: float

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper


@dataclass(slots=True)
class TransitionRuleMiner:
    """Mine simple feature intervals that characterize observed chart transitions."""

    min_support: int = 2
    sigma: float = 1.0

    def mine(self, samples: list[TransitionSample] | tuple[TransitionSample, ...]) -> tuple[CandidateTransitionLaw, ...]:
        if not samples:
            return ()
        feature_names = samples[0].feature_names
        grouped: dict[tuple[ChartType, ChartType], list[np.ndarray]] = {}
        all_features = np.vstack([sample.features for sample in samples])
        global_mean = np.mean(all_features, axis=0)
        global_std = np.where(np.std(all_features, axis=0) < 1.0e-9, 1.0, np.std(all_features, axis=0))

        for sample in samples:
            if sample.feature_names != feature_names:
                raise ValueError("All samples must use the same feature names.")
            grouped.setdefault((sample.previous, sample.current), []).append(sample.features)

        laws: list[CandidateTransitionLaw] = []
        for (previous, current), vectors in grouped.items():
            if len(vectors) < self.min_support:
                continue
            matrix = np.vstack(vectors)
            local_mean = np.mean(matrix, axis=0)
            local_std = np.where(np.std(matrix, axis=0) < 1.0e-9, 0.0, np.std(matrix, axis=0))
            contrast_by_feature = np.abs(local_mean - global_mean) / global_std
            best_index = int(np.argmax(contrast_by_feature))
            width = float(self.sigma * local_std[best_index])
            center = float(local_mean[best_index])
            laws.append(
                CandidateTransitionLaw(
                    previous=previous,
                    current=current,
                    feature=feature_names[best_index],
                    lower=center - width,
                    upper=center + width,
                    center=center,
                    width=width,
                    support=len(vectors),
                    contrast=float(contrast_by_feature[best_index]),
                )
            )
        return tuple(sorted(laws, key=lambda law: (law.support, law.contrast), reverse=True))
