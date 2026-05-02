from __future__ import annotations

from dataclasses import dataclass

from .rule_miner import CandidateTransitionLaw
from .transition_model import TransitionSample
from .types import ChartType


@dataclass(frozen=True, slots=True)
class TransitionLawValidation:
    previous: ChartType
    current: ChartType
    feature: str
    lower: float
    upper: float
    true_positives: int
    false_positives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        denominator = self.true_positives + self.false_positives
        return 0.0 if denominator == 0 else self.true_positives / denominator

    @property
    def recall(self) -> float:
        denominator = self.true_positives + self.false_negatives
        return 0.0 if denominator == 0 else self.true_positives / denominator


@dataclass(slots=True)
class TransitionLawValidator:
    """Validate mined transition rules against held-out transition samples."""

    def validate(
        self,
        laws: tuple[CandidateTransitionLaw, ...] | list[CandidateTransitionLaw],
        samples: tuple[TransitionSample, ...] | list[TransitionSample],
    ) -> tuple[TransitionLawValidation, ...]:
        rows: list[TransitionLawValidation] = []
        for law in laws:
            feature_index = _feature_index(law.feature, samples)
            if feature_index is None:
                rows.append(_empty_validation(law))
                continue
            true_positives = 0
            false_positives = 0
            false_negatives = 0
            for sample in samples:
                if sample.previous != law.previous:
                    continue
                predicted = law.contains(float(sample.features[feature_index]))
                actual = sample.current == law.current
                if predicted and actual:
                    true_positives += 1
                elif predicted and not actual:
                    false_positives += 1
                elif not predicted and actual:
                    false_negatives += 1
            rows.append(
                TransitionLawValidation(
                    previous=law.previous,
                    current=law.current,
                    feature=law.feature,
                    lower=law.lower,
                    upper=law.upper,
                    true_positives=true_positives,
                    false_positives=false_positives,
                    false_negatives=false_negatives,
                )
            )
        return tuple(sorted(rows, key=lambda row: (row.precision, row.recall), reverse=True))

    @staticmethod
    def rows(validations: tuple[TransitionLawValidation, ...] | list[TransitionLawValidation]) -> list[dict[str, float | int | str]]:
        return [
            {
                "from": str(row.previous),
                "to": str(row.current),
                "feature": row.feature,
                "lower": row.lower,
                "upper": row.upper,
                "true_positives": row.true_positives,
                "false_positives": row.false_positives,
                "false_negatives": row.false_negatives,
                "precision": row.precision,
                "recall": row.recall,
            }
            for row in validations
        ]


def _feature_index(feature: str, samples: tuple[TransitionSample, ...] | list[TransitionSample]) -> int | None:
    for sample in samples:
        if feature in sample.feature_names:
            return sample.feature_names.index(feature)
    return None


def _empty_validation(law: CandidateTransitionLaw) -> TransitionLawValidation:
    return TransitionLawValidation(
        previous=law.previous,
        current=law.current,
        feature=law.feature,
        lower=law.lower,
        upper=law.upper,
        true_positives=0,
        false_positives=0,
        false_negatives=0,
    )
