from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .types import AnalysisReport, ChartType


@dataclass(frozen=True, slots=True)
class ChartWord:
    """Compressed word over the chart alphabet."""

    symbols: tuple[object, ...]

    @property
    def length(self) -> int:
        return len(self.symbols)

    def as_string(self) -> str:
        return " -> ".join(str(symbol) for symbol in self.symbols)

    def reversal(self) -> ChartWord:
        return ChartWord(tuple(reversed(self.symbols)))

    def transition_pairs(self) -> tuple[tuple[object, object], ...]:
        return tuple(zip(self.symbols, self.symbols[1:], strict=False))


@dataclass(frozen=True, slots=True)
class ChartWordSignature:
    word: ChartWord
    transition_entropy: float
    reversal_defect: float
    primitive_period: int
    repeated: bool
    grammar_rank: int

    def as_dict(self) -> dict[str, float | int | str | bool]:
        return {
            "word": self.word.as_string(),
            "length": self.word.length,
            "transition_entropy": self.transition_entropy,
            "reversal_defect": self.reversal_defect,
            "primitive_period": self.primitive_period,
            "repeated": self.repeated,
            "grammar_rank": self.grammar_rank,
        }


def chart_word_from_reports(reports: tuple[AnalysisReport, ...] | list[AnalysisReport]) -> ChartWord:
    symbols: list[object] = []
    previous: object | None = None
    for report in reports:
        chart = report.primary_chart
        if chart == previous:
            continue
        symbols.append(chart)
        previous = chart
    return ChartWord(tuple(symbols))


def refined_chart_word_from_reports(reports: tuple[AnalysisReport, ...] | list[AnalysisReport]) -> ChartWord:
    """Compressed word over chart labels enriched with coarse physical bins."""

    symbols: list[object] = []
    previous: object | None = None
    for report in reports:
        symbol = refined_chart_symbol(report)
        if symbol == previous:
            continue
        symbols.append(symbol)
        previous = symbol
    return ChartWord(tuple(symbols))


def return_map_word_from_reports(
    reports: tuple[AnalysisReport, ...] | list[AnalysisReport],
    *,
    coordinate: str = "hierarchy_ratio",
) -> ChartWord:
    """Symbolic proxy for a return map built from extrema of a diagnostic coordinate."""

    if len(reports) < 3:
        return refined_chart_word_from_reports(reports)
    values = np.asarray([_feature_value(report, coordinate) for report in reports], dtype=float)
    symbols: list[object] = []
    for index in range(1, len(reports) - 1):
        previous, current, following = values[index - 1], values[index], values[index + 1]
        if not np.isfinite(current):
            continue
        if current >= previous and current > following:
            event = "max"
        elif current <= previous and current < following:
            event = "min"
        else:
            continue
        symbol = return_map_symbol(reports[index], coordinate=coordinate, event=event)
        if symbols and symbols[-1] == symbol:
            continue
        symbols.append(symbol)
    if not symbols:
        return refined_chart_word_from_reports(reports)
    return ChartWord(tuple(symbols))


def return_map_symbol(report: AnalysisReport, *, coordinate: str, event: str) -> str:
    value = _feature_value(report, coordinate)
    if coordinate == "hierarchy_perturbation_strength":
        bucket = _log_strength_bin(value)
    else:
        bucket = _linear_bin(value, width=2.0, maximum=9)
    return f"return:{coordinate}:{event}:B{bucket}:{refined_chart_symbol(report)}"


def refined_chart_symbol(report: AnalysisReport) -> str:
    chart = report.primary_chart
    features = report.features
    if chart == ChartType.TWO_BODY_HIERARCHY:
        pair = "".join(str(index) for index in getattr(features, "nearest_pair", ()))
        hierarchy = _linear_bin(getattr(features, "hierarchy_ratio", 0.0), width=2.0, maximum=9)
        perturbation = _log_strength_bin(getattr(features, "hierarchy_perturbation_strength", np.inf))
        inner_energy = "B" if getattr(features, "nearest_pair_specific_energy", 1.0) < 0.0 else "U"
        return f"{chart.value}:pair{pair}:H{hierarchy}:P{perturbation}:{inner_energy}"
    if chart == ChartType.PERIODIC_ORBIT_NEIGHBORHOOD:
        virial = _linear_bin(abs(getattr(features, "virial_ratio", 0.0) - 1.0), width=0.2, maximum=9)
        area = _linear_bin(getattr(features, "normalized_area", 0.0), width=0.2, maximum=5)
        outer_energy = "E+" if getattr(features, "outer_specific_energy", -1.0) > 0.0 else "E-"
        return f"{chart.value}:V{virial}:A{area}:{outer_energy}"
    if chart == ChartType.CHAOTIC_TRANSPORT:
        area = _linear_bin(getattr(features, "normalized_area", 0.0), width=0.2, maximum=5)
        anisotropy = _linear_bin(getattr(features, "shape_anisotropy", 0.0), width=0.33, maximum=9)
        return f"{chart.value}:A{area}:S{anisotropy}"
    if chart == ChartType.DEMOCRATIC_THREE_BODY:
        area = _linear_bin(getattr(features, "normalized_area", 0.0), width=0.2, maximum=5)
        anisotropy = _linear_bin(getattr(features, "shape_anisotropy", 0.0), width=0.33, maximum=9)
        return f"{chart.value}:A{area}:S{anisotropy}"
    if chart == ChartType.CLOSE_ENCOUNTER:
        pair = "".join(str(index) for index in getattr(features, "nearest_pair", ()))
        distance = _log_distance_bin(getattr(features, "nearest_distance", np.inf))
        return f"{chart.value}:pair{pair}:D{distance}"
    if chart == ChartType.ESCAPE_TRANSPORT:
        escape = _linear_bin(getattr(features, "escape_index", 0.0), width=1.0, maximum=9)
        outer_energy = "E+" if getattr(features, "outer_specific_energy", -1.0) > 0.0 else "E-"
        return f"{chart.value}:X{escape}:{outer_energy}"
    if chart in {ChartType.RESTRICTED_LAGRANGE, ChartType.RESTRICTED_GATEWAY}:
        lagrange = getattr(features, "nearest_lagrange", "?")
        margin = _signed_linear_bin(getattr(features, "gateway_margin", 0.0), width=0.05, maximum=9)
        return f"{chart.value}:{lagrange}:M{margin}"
    return chart.value


def chart_word_signature(word: ChartWord) -> ChartWordSignature:
    pairs = word.transition_pairs()
    transition_entropy = _entropy(pairs)
    reversal_defect = _reversal_defect(word)
    primitive_period = _primitive_period(word.symbols)
    repeated = primitive_period < max(word.length, 1)
    grammar_rank = len(set(pairs))
    return ChartWordSignature(
        word=word,
        transition_entropy=transition_entropy,
        reversal_defect=reversal_defect,
        primitive_period=primitive_period,
        repeated=repeated,
        grammar_rank=grammar_rank,
    )


def word_signature_rows(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
) -> list[dict[str, float | int | str | bool]]:
    rows = []
    for name, reports in reports_by_name.items():
        signature = chart_word_signature(chart_word_from_reports(reports))
        row = signature.as_dict()
        row["scenario"] = name
        rows.append(row)
    return rows


def refined_word_signature_rows(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
) -> list[dict[str, float | int | str | bool]]:
    rows = []
    for name, reports in reports_by_name.items():
        signature = chart_word_signature(refined_chart_word_from_reports(reports))
        row = signature.as_dict()
        row["scenario"] = name
        rows.append(row)
    return rows


def return_word_signature_rows(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
    *,
    coordinate: str = "hierarchy_ratio",
) -> list[dict[str, float | int | str | bool]]:
    rows = []
    for name, reports in reports_by_name.items():
        signature = chart_word_signature(return_map_word_from_reports(reports, coordinate=coordinate))
        row = signature.as_dict()
        row["scenario"] = name
        row["coordinate"] = coordinate
        rows.append(row)
    return rows


def word_distance(first: ChartWord, second: ChartWord) -> int:
    """Levenshtein distance between chart words."""

    rows = first.length + 1
    cols = second.length + 1
    matrix = np.zeros((rows, cols), dtype=int)
    matrix[:, 0] = np.arange(rows)
    matrix[0, :] = np.arange(cols)
    for row in range(1, rows):
        for col in range(1, cols):
            substitution = 0 if first.symbols[row - 1] == second.symbols[col - 1] else 1
            matrix[row, col] = min(
                matrix[row - 1, col] + 1,
                matrix[row, col - 1] + 1,
                matrix[row - 1, col - 1] + substitution,
            )
    return int(matrix[-1, -1])


def _entropy(items: tuple[object, ...]) -> float:
    if not items:
        return 0.0
    counts: dict[object, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    probabilities = np.asarray(list(counts.values()), dtype=float) / len(items)
    return float(-np.sum(probabilities * np.log2(probabilities)))


def _reversal_defect(word: ChartWord) -> float:
    if word.length == 0:
        return 0.0
    return float(word_distance(word, word.reversal()) / word.length)


def _primitive_period(symbols: tuple[object, ...]) -> int:
    if not symbols:
        return 0
    for period in range(1, len(symbols) + 1):
        pattern = symbols[:period]
        tiled = tuple(pattern[index % period] for index in range(len(symbols)))
        if tiled == symbols:
            return period
    return len(symbols)


def _linear_bin(value: float, *, width: float, maximum: int) -> int:
    if not np.isfinite(value):
        return maximum
    return int(np.clip(np.floor(max(value, 0.0) / width), 0, maximum))


def _signed_linear_bin(value: float, *, width: float, maximum: int) -> str:
    if not np.isfinite(value):
        return "?"
    sign = "p" if value >= 0.0 else "m"
    return f"{sign}{int(np.clip(np.floor(abs(value) / width), 0, maximum))}"


def _log_strength_bin(value: float) -> int:
    if not np.isfinite(value) or value <= 0.0:
        return 0
    return int(np.clip(np.floor(-np.log10(max(value, 1.0e-12))), 0, 9))


def _log_distance_bin(value: float) -> int:
    if not np.isfinite(value) or value <= 0.0:
        return 9
    return int(np.clip(np.floor(-np.log10(max(value, 1.0e-12))), 0, 9))


def _feature_value(report: AnalysisReport, coordinate: str) -> float:
    value = getattr(report.features, coordinate, np.nan)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")
