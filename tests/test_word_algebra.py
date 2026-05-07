from __future__ import annotations

from threebody.analysis import (
    AnalysisReport,
    ChartScore,
    ChartType,
    chart_word_from_reports,
    chart_word_signature,
    refined_chart_symbol,
    return_map_word_from_reports,
    word_distance,
)


def _report(chart: ChartType) -> AnalysisReport:
    return AnalysisReport(primary_chart=chart, scores=(ChartScore(chart, 1.0, "test"),), features=object())


def test_chart_word_compresses_repeated_symbols() -> None:
    word = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.TWO_BODY_HIERARCHY),
        ]
    )

    assert word.length == 3
    assert word.symbols[0] == ChartType.TWO_BODY_HIERARCHY


def test_chart_word_signature_reports_reversal_defect_and_period() -> None:
    word = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
        ]
    )
    signature = chart_word_signature(word)

    assert signature.transition_entropy >= 0.0
    assert signature.primitive_period == 2
    assert signature.repeated is True
    assert word_distance(word, word.reversal()) >= 0


def test_refined_chart_symbol_splits_same_chart_by_physical_bins() -> None:
    class _Features:
        nearest_pair = (0, 1)
        hierarchy_ratio = 5.0
        hierarchy_perturbation_strength = 1.0e-4
        nearest_pair_specific_energy = -1.0

    first = AnalysisReport(
        primary_chart=ChartType.TWO_BODY_HIERARCHY,
        scores=(ChartScore(ChartType.TWO_BODY_HIERARCHY, 1.0, "test"),),
        features=_Features(),
    )
    second_features = _Features()
    second_features.hierarchy_ratio = 12.0
    second = AnalysisReport(
        primary_chart=ChartType.TWO_BODY_HIERARCHY,
        scores=(ChartScore(ChartType.TWO_BODY_HIERARCHY, 1.0, "test"),),
        features=second_features,
    )

    assert refined_chart_symbol(first) != refined_chart_symbol(second)


def test_return_map_word_uses_coordinate_extrema() -> None:
    class _Features:
        nearest_pair = (0, 1)
        hierarchy_ratio = 1.0
        hierarchy_perturbation_strength = 1.0e-4
        nearest_pair_specific_energy = -1.0

    reports = []
    for value in (1.0, 5.0, 2.0, 6.0, 3.0):
        features = _Features()
        features.hierarchy_ratio = value
        reports.append(
            AnalysisReport(
                primary_chart=ChartType.TWO_BODY_HIERARCHY,
                scores=(ChartScore(ChartType.TWO_BODY_HIERARCHY, 1.0, "test"),),
                features=features,
            )
        )

    word = return_map_word_from_reports(reports)

    assert word.length >= 2
    assert "return:hierarchy_ratio" in word.as_string()
