from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class BoundaryCollapseFit:
    """Power-law boundary collapse fit in log coordinates."""

    target_name: str
    feature_names: tuple[str, ...]
    intercept: float
    coefficients: tuple[float, ...]
    raw_cv: float | None
    collapsed_cv: float | None
    improvement: float | None
    support: int

    def predict(self, features: np.ndarray) -> np.ndarray:
        features = np.atleast_2d(np.asarray(features, dtype=float))
        log_features = np.log(np.maximum(features, 1.0e-300))
        log_prediction = self.intercept + log_features @ np.asarray(self.coefficients, dtype=float)
        return np.exp(log_prediction)

    def rows(self) -> dict[str, float | int | str | None]:
        row: dict[str, float | int | str | None] = {
            "target": self.target_name,
            "support": self.support,
            "intercept": self.intercept,
            "raw_cv": self.raw_cv,
            "collapsed_cv": self.collapsed_cv,
            "improvement": self.improvement,
        }
        for name, coefficient in zip(self.feature_names, self.coefficients, strict=True):
            row[f"exponent_{name}"] = coefficient
        return row


def fit_power_law_boundary_collapse(
    target: np.ndarray,
    features: np.ndarray,
    feature_names: tuple[str, ...],
    target_name: str,
) -> BoundaryCollapseFit:
    target = np.asarray(target, dtype=float)
    features = np.asarray(features, dtype=float)
    if target.size == 0 or features.size == 0:
        return BoundaryCollapseFit(
            target_name=target_name,
            feature_names=feature_names,
            intercept=0.0,
            coefficients=tuple(0.0 for _ in feature_names),
            raw_cv=None,
            collapsed_cv=None,
            improvement=None,
            support=0,
        )
    features = np.atleast_2d(features)
    mask = np.isfinite(target) & (target > 0.0) & np.all(np.isfinite(features) & (features > 0.0), axis=1)
    target = target[mask]
    features = features[mask]
    if target.size < len(feature_names) + 1:
        return BoundaryCollapseFit(
            target_name=target_name,
            feature_names=feature_names,
            intercept=0.0,
            coefficients=tuple(0.0 for _ in feature_names),
            raw_cv=_coefficient_of_variation(target),
            collapsed_cv=None,
            improvement=None,
            support=int(target.size),
        )

    design = np.column_stack([np.ones(target.size), np.log(features)])
    coefficients, *_unused = np.linalg.lstsq(design, np.log(target), rcond=None)
    intercept = float(coefficients[0])
    exponents = tuple(float(value) for value in coefficients[1:])
    predicted = np.exp(design @ coefficients)
    collapsed = target / predicted
    raw_cv = _coefficient_of_variation(target)
    collapsed_cv = _coefficient_of_variation(collapsed)
    improvement = None if raw_cv in (None, 0.0) or collapsed_cv is None else float(1.0 - collapsed_cv / raw_cv)
    return BoundaryCollapseFit(
        target_name=target_name,
        feature_names=feature_names,
        intercept=intercept,
        coefficients=exponents,
        raw_cv=raw_cv,
        collapsed_cv=collapsed_cv,
        improvement=improvement,
        support=int(target.size),
    )


def _coefficient_of_variation(values: np.ndarray) -> float | None:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return None
    mean = float(np.mean(values))
    if abs(mean) < 1.0e-12:
        return None
    return float(np.std(values) / abs(mean))
