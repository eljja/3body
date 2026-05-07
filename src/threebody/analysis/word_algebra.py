from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .types import AnalysisReport, ChartType


@dataclass(frozen=True, slots=True)
class ChartWord:
    """Compressed word over the chart alphabet."""

    symbols: tuple[ChartType, ...]

    @property
    def length(self) -> int:
        return len(self.symbols)

    def as_string(self) -> str:
        return " -> ".join(str(symbol) for symbol in self.symbols)

    def reversal(self) -> ChartWord:
        return ChartWord(tuple(reversed(self.symbols)))

    def transition_pairs(self) -> tuple[tuple[ChartType, ChartType], ...]:
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
    symbols: list[ChartType] = []
    previous: ChartType | None = None
    for report in reports:
        chart = report.primary_chart
        if chart == previous:
            continue
        symbols.append(chart)
        previous = chart
    return ChartWord(tuple(symbols))


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


def _primitive_period(symbols: tuple[ChartType, ...]) -> int:
    if not symbols:
        return 0
    for period in range(1, len(symbols) + 1):
        pattern = symbols[:period]
        tiled = tuple(pattern[index % period] for index in range(len(symbols)))
        if tiled == symbols:
            return period
    return len(symbols)
