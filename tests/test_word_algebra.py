from __future__ import annotations

from threebody.analysis import AnalysisReport, ChartScore, ChartType, chart_word_from_reports, chart_word_signature, word_distance


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
