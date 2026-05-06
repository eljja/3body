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
    log_residual_sum_squares: float | None
    aic: float | None
    bic: float | None
    support: int

    def predict(self, features: np.ndarray) -> np.ndarray:
        features = np.atleast_2d(np.asarray(features, dtype=float))
        log_features = np.log(np.maximum(features, 1.0e-300))
        log_prediction = self.intercept + log_features @ np.asarray(self.coefficients, dtype=float)
        return np.exp(log_prediction)

    def rows(self) -> dict[str, float | int | str | bool | None]:
        row: dict[str, float | int | str | None] = {
            "target": self.target_name,
            "support": self.support,
            "intercept": self.intercept,
            "raw_cv": self.raw_cv,
            "collapsed_cv": self.collapsed_cv,
            "improvement": self.improvement,
            "log_residual_sum_squares": self.log_residual_sum_squares,
            "aic": self.aic,
            "bic": self.bic,
        }
        for name, coefficient in zip(self.feature_names, self.coefficients, strict=True):
            row[f"exponent_{name}"] = coefficient
        return row


@dataclass(frozen=True, slots=True)
class BoundaryCollapseValidation:
    target_name: str
    feature_names: tuple[str, ...]
    training_support: int
    validation_support: int
    training_raw_cv: float | None
    training_collapsed_cv: float | None
    training_improvement: float | None
    validation_raw_cv: float | None
    validation_collapsed_cv: float | None
    validation_improvement: float | None

    @property
    def passes_validation(self) -> bool:
        return self.validation_improvement is not None and self.validation_improvement > 0.25

    @property
    def complexity_penalized_validation_score(self) -> float | None:
        if self.validation_improvement is None:
            return None
        return float(self.validation_improvement - 0.03 * len(self.feature_names))

    def rows(self) -> dict[str, float | int | str | bool | None]:
        return {
            "target": self.target_name,
            "features": ",".join(self.feature_names),
            "feature_count": len(self.feature_names),
            "training_support": self.training_support,
            "validation_support": self.validation_support,
            "training_raw_cv": self.training_raw_cv,
            "training_collapsed_cv": self.training_collapsed_cv,
            "training_improvement": self.training_improvement,
            "validation_raw_cv": self.validation_raw_cv,
            "validation_collapsed_cv": self.validation_collapsed_cv,
            "validation_improvement": self.validation_improvement,
            "complexity_penalized_validation_score": self.complexity_penalized_validation_score,
            "passes_validation": self.passes_validation,
        }


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
            log_residual_sum_squares=None,
            aic=None,
            bic=None,
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
            log_residual_sum_squares=None,
            aic=None,
            bic=None,
            support=int(target.size),
        )

    design = np.column_stack([np.ones(target.size), np.log(features)])
    coefficients, *_unused = np.linalg.lstsq(design, np.log(target), rcond=None)
    intercept = float(coefficients[0])
    exponents = tuple(float(value) for value in coefficients[1:])
    predicted = np.exp(design @ coefficients)
    collapsed = target / predicted
    log_residuals = np.log(target) - np.log(np.maximum(predicted, 1.0e-300))
    rss = float(np.sum(log_residuals**2))
    parameter_count = len(feature_names) + 1
    aic = _information_criterion(rss, target.size, parameter_count, kind="aic")
    bic = _information_criterion(rss, target.size, parameter_count, kind="bic")
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
        log_residual_sum_squares=rss,
        aic=aic,
        bic=bic,
        support=int(target.size),
    )


def validate_power_law_boundary_collapse(
    fit: BoundaryCollapseFit,
    target: np.ndarray,
    features: np.ndarray,
) -> BoundaryCollapseValidation:
    target = np.asarray(target, dtype=float)
    features = np.asarray(features, dtype=float)
    if target.size == 0 or features.size == 0:
        validation_raw_cv = None
        validation_collapsed_cv = None
        validation_improvement = None
        support = 0
    else:
        features = np.atleast_2d(features)
        mask = np.isfinite(target) & (target > 0.0) & np.all(np.isfinite(features) & (features > 0.0), axis=1)
        target = target[mask]
        features = features[mask]
        support = int(target.size)
        if support == 0:
            validation_raw_cv = None
            validation_collapsed_cv = None
            validation_improvement = None
        else:
            predicted = fit.predict(features)
            collapsed = target / np.maximum(predicted, 1.0e-300)
            validation_raw_cv = _coefficient_of_variation(target)
            validation_collapsed_cv = _coefficient_of_variation(collapsed)
            validation_improvement = (
                None
                if validation_raw_cv in (None, 0.0) or validation_collapsed_cv is None
                else float(1.0 - validation_collapsed_cv / validation_raw_cv)
            )
    return BoundaryCollapseValidation(
        target_name=fit.target_name,
        feature_names=fit.feature_names,
        training_support=fit.support,
        validation_support=support,
        training_raw_cv=fit.raw_cv,
        training_collapsed_cv=fit.collapsed_cv,
        training_improvement=fit.improvement,
        validation_raw_cv=validation_raw_cv,
        validation_collapsed_cv=validation_collapsed_cv,
        validation_improvement=validation_improvement,
    )


def _coefficient_of_variation(values: np.ndarray) -> float | None:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return None
    mean = float(np.mean(values))
    if abs(mean) < 1.0e-12:
        return None
    return float(np.std(values) / abs(mean))


def _information_criterion(rss: float, sample_count: int, parameter_count: int, kind: str) -> float | None:
    if sample_count <= 0:
        return None
    likelihood_term = sample_count * np.log(max(rss, 1.0e-300) / sample_count)
    if kind == "aic":
        return float(likelihood_term + 2.0 * parameter_count)
    if kind == "bic":
        return float(likelihood_term + parameter_count * np.log(sample_count))
    raise ValueError(f"Unknown information criterion: {kind}")
