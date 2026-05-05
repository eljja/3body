from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .coordinates import general_three_body_features, restricted_three_body_features
from .types import AnalysisReport, ChartScore, ChartType


@dataclass(slots=True)
class ChartClassifier:
    """Classify a state into the interpretive chart most likely to explain it."""

    close_encounter_radius: float = 0.08
    hierarchy_ratio_threshold: float = 5.0
    hierarchy_perturbation_threshold: float = 4.0e-3
    escape_index_threshold: float = 6.0
    lagrange_radius: float = 0.15
    gateway_margin_threshold: float = 0.03

    def classify(self, system: object, state: np.ndarray) -> AnalysisReport:
        if hasattr(system, "mass_ratio") and hasattr(system, "jacobi_constant"):
            return self.classify_restricted(system, state)
        if getattr(system, "body_count", None) == 3:
            return self.classify_general(system, state)
        raise TypeError(f"Unsupported system type for chart classification: {type(system)!r}")

    def classify_general(self, system: object, state: np.ndarray) -> AnalysisReport:
        features = general_three_body_features(system, state)
        scores = [
            self._score_close_encounter(features),
            self._score_hierarchy(features),
            self._score_escape(features),
            self._score_periodic_neighborhood(features),
            self._score_chaotic_transport(features),
            self._score_democratic(features),
        ]
        ranked = tuple(sorted(scores, key=lambda item: item.score, reverse=True))
        return AnalysisReport(primary_chart=ranked[0].chart, scores=ranked, features=features)

    def classify_restricted(self, system: object, state: np.ndarray) -> AnalysisReport:
        features = restricted_three_body_features(system, state)
        near_lagrange = _clamped_score(1.0 - features.nearest_lagrange_distance / self.lagrange_radius)
        near_primary = _clamped_score(1.0 - np.min(features.distances_to_primaries) / self.close_encounter_radius)
        collinear_gate = 1.0 if features.nearest_lagrange in {"L1", "L2", "L3"} else 0.0
        gateway = collinear_gate * _clamped_score(1.0 - features.gateway_margin / self.gateway_margin_threshold)
        speed_score = _clamped_score(features.speed / 1.5)
        scores = [
            ChartScore(
                ChartType.RESTRICTED_LAGRANGE,
                near_lagrange,
                f"Near {features.nearest_lagrange}; use local normal forms and invariant manifolds.",
                {"nearest_lagrange_distance": features.nearest_lagrange_distance},
            ),
            ChartScore(
                ChartType.CLOSE_ENCOUNTER,
                near_primary,
                "Close to a primary; switch to regularized coordinates before interpreting the flow.",
                {"nearest_primary_distance": float(np.min(features.distances_to_primaries))},
            ),
            ChartScore(
                ChartType.RESTRICTED_GATEWAY,
                gateway,
                "Near a zero-velocity gateway; transport channels and neck geometry dominate.",
                {"gateway_margin": features.gateway_margin},
            ),
            ChartScore(
                ChartType.CHAOTIC_TRANSPORT,
                speed_score,
                "High rotating-frame speed; use Poincare maps and transport diagnostics.",
                {"speed": features.speed},
            ),
        ]
        ranked = tuple(sorted(scores, key=lambda item: item.score, reverse=True))
        return AnalysisReport(primary_chart=ranked[0].chart, scores=ranked, features=features)

    def _score_close_encounter(self, features: object) -> ChartScore:
        score = _clamped_score(1.0 - features.nearest_distance / self.close_encounter_radius)
        return ChartScore(
            ChartType.CLOSE_ENCOUNTER,
            score,
            "Nearest pair is inside the close-encounter scale; regularization should lead.",
            {"nearest_distance": features.nearest_distance},
        )

    def _score_hierarchy(self, features: object) -> ChartScore:
        geometric_separation = _clamped_score((features.hierarchy_ratio - 1.0) / (self.hierarchy_ratio_threshold - 1.0))
        perturbative_validity = _clamped_score(
            1.0 - features.hierarchy_perturbation_strength / self.hierarchy_perturbation_threshold
        )
        score = _clamped_score(geometric_separation * perturbative_validity)
        return ChartScore(
            ChartType.TWO_BODY_HIERARCHY,
            score,
            "One pair is separated and third-body tidal perturbation is small enough for Jacobi/Kepler analysis.",
            {
                "hierarchy_ratio": features.hierarchy_ratio,
                "hierarchy_perturbation_strength": features.hierarchy_perturbation_strength,
                "perturbative_validity": perturbative_validity,
            },
        )

    def _score_escape(self, features: object) -> ChartScore:
        score = _clamped_score(features.escape_index / self.escape_index_threshold)
        return ChartScore(
            ChartType.ESCAPE_TRANSPORT,
            score,
            "Large radius-speed product indicates possible scattering or escape transport.",
            {"escape_index": features.escape_index},
        )

    def _score_periodic_neighborhood(self, features: object) -> ChartScore:
        virial_closeness = 1.0 - abs(features.virial_ratio - 1.0)
        angular_penalty = 1.0 / (1.0 + features.angular_momentum_norm)
        score = _clamped_score(0.7 * virial_closeness + 0.3 * angular_penalty)
        return ChartScore(
            ChartType.PERIODIC_ORBIT_NEIGHBORHOOD,
            score,
            "Balanced virial structure suggests testing against periodic-orbit families and monodromy.",
            {"virial_ratio": features.virial_ratio, "angular_momentum_norm": features.angular_momentum_norm},
        )

    def _score_chaotic_transport(self, features: object) -> ChartScore:
        nonhierarchical = 1.0 - _clamped_score((features.hierarchy_ratio - 1.0) / 3.0)
        virial_offset = _clamped_score(abs(features.virial_ratio - 1.0))
        score = _clamped_score(0.6 * nonhierarchical + 0.4 * virial_offset)
        return ChartScore(
            ChartType.CHAOTIC_TRANSPORT,
            score,
            "No dominant hierarchy with energetic imbalance; analyze through sections and transport maps.",
            {"hierarchy_ratio": features.hierarchy_ratio, "virial_ratio": features.virial_ratio},
        )

    def _score_democratic(self, features: object) -> ChartScore:
        ratio_score = 1.0 - _clamped_score((features.hierarchy_ratio - 1.0) / 2.0)
        score = _clamped_score(ratio_score)
        return ChartScore(
            ChartType.DEMOCRATIC_THREE_BODY,
            score,
            "All pair distances are comparable; no two-body reduction is currently dominant.",
            {"hierarchy_ratio": features.hierarchy_ratio},
        )


def _clamped_score(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return float(np.clip(value, 0.0, 1.0))
