from __future__ import annotations

from dataclasses import dataclass

from .types import AnalysisReport, ChartType


@dataclass(frozen=True, slots=True)
class ChartValidityBound:
    """Local, falsifiable validity claim for one atlas chart."""

    chart: ChartType
    statement: str
    control_parameter: str
    observed_value: float | None
    qualitative_error_bound: str
    hard_theorem: bool = False

    def as_dict(self) -> dict[str, float | str | bool | None]:
        return {
            "chart": self.chart.value,
            "statement": self.statement,
            "control_parameter": self.control_parameter,
            "observed_value": self.observed_value,
            "qualitative_error_bound": self.qualitative_error_bound,
            "hard_theorem": self.hard_theorem,
        }


def chart_validity_bound(report: AnalysisReport) -> ChartValidityBound:
    """Return the current local claim that is allowed for a classified chart."""

    diagnostics = report.scores[0].diagnostics if report.scores else {}
    chart = report.primary_chart
    if chart == ChartType.TWO_BODY_HIERARCHY:
        value = diagnostics.get("hierarchy_perturbation_strength")
        return ChartValidityBound(
            chart=chart,
            statement="Jacobi/Kepler hierarchy is a perturbative chart, not an exact reduction.",
            control_parameter="hierarchy_perturbation_strength",
            observed_value=value,
            qualitative_error_bound="local model error should scale with the tidal perturbation parameter until resonance or close encounter invalidates the chart",
        )
    if chart == ChartType.RESTRICTED_LAGRANGE:
        value = diagnostics.get("nearest_lagrange_distance")
        return ChartValidityBound(
            chart=chart,
            statement="Linear and normal-form analysis is valid only inside a small Lagrange neighborhood.",
            control_parameter="nearest_lagrange_distance",
            observed_value=value,
            qualitative_error_bound="linear error grows with distance from the equilibrium and must be checked by monodromy/Floquet diagnostics",
        )
    if chart == ChartType.RESTRICTED_GATEWAY:
        value = diagnostics.get("gateway_margin")
        return ChartValidityBound(
            chart=chart,
            statement="Transport through a neck is controlled by zero-velocity geometry and invariant manifolds.",
            control_parameter="gateway_margin",
            observed_value=value,
            qualitative_error_bound="gateway prediction is unreliable when the Jacobi margin is not resolved relative to numerical drift",
        )
    if chart == ChartType.CLOSE_ENCOUNTER:
        value = diagnostics.get("nearest_distance")
        return ChartValidityBound(
            chart=chart,
            statement="Raw inertial coordinates are a poor analytic chart near collision.",
            control_parameter="nearest_distance",
            observed_value=value,
            qualitative_error_bound="ordinary integration error can blow up as inverse powers of pair distance; regularized coordinates are required before claiming a law",
        )
    if chart == ChartType.ESCAPE_TRANSPORT:
        value = diagnostics.get("escape_index")
        return ChartValidityBound(
            chart=chart,
            statement="Escape should be modeled by asymptotic Kepler elements and a scattering map.",
            control_parameter="escape_index",
            observed_value=value,
            qualitative_error_bound="finite-time escape labels require convergence of outgoing energy and deflection angle",
        )
    return ChartValidityBound(
        chart=chart,
        statement="This chart is currently empirical and needs a chart-specific compact model.",
        control_parameter="classifier_confidence",
        observed_value=report.confidence,
        qualitative_error_bound="no theorem-level error bound is implemented yet; use held-out transition validation only",
    )
