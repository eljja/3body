from __future__ import annotations

from threebody.analysis import (
    AnalysisReport,
    ChartScore,
    ChartType,
    bootstrap_markov_baseline_comparison,
    chart_word_from_reports,
    chart_word_signature,
    compare_markov_chain_to_independent_baseline,
    markov_chain_from_words,
    poincare_section_word_from_reports,
    refined_chart_symbol,
    return_map_word_from_reports,
    select_markov_order,
    validate_markov_chain,
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


def test_poincare_section_word_uses_explicit_crossings() -> None:
    class _Features:
        nearest_pair = (0, 1)
        hierarchy_ratio = 1.0
        hierarchy_perturbation_strength = 1.0
        nearest_pair_specific_energy = -1.0

    reports = []
    for value in (0.2, 1.2, 0.4, 1.4, 0.3):
        features = _Features()
        features.hierarchy_perturbation_strength = value
        reports.append(
            AnalysisReport(
                primary_chart=ChartType.TWO_BODY_HIERARCHY,
                scores=(ChartScore(ChartType.TWO_BODY_HIERARCHY, 1.0, "test"),),
                features=features,
            )
        )

    word = poincare_section_word_from_reports(
        reports,
        coordinate="hierarchy_perturbation_strength",
        section_value=0.8,
    )

    assert word.length >= 3
    assert "section:hierarchy_perturbation_strength" in word.as_string()


def test_markov_chain_from_words_reports_symbolic_transition_probabilities() -> None:
    first = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.TWO_BODY_HIERARCHY),
        ]
    )
    second = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
        ]
    )

    chain = markov_chain_from_words((first, second))

    assert ChartType.TWO_BODY_HIERARCHY in chain.states
    assert ChartType.CHAOTIC_TRANSPORT in chain.states
    assert chain.transition_entropy_rate >= 0.0
    assert abs(sum(chain.stationary_distribution) - 1.0) < 1.0e-12
    assert chain.as_dict()["transition_probabilities"]


def test_markov_chain_validation_scores_heldout_words() -> None:
    training = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
        ]
    )
    heldout = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
        ]
    )

    chain = markov_chain_from_words((training,))
    validation = validate_markov_chain(chain, (heldout,))

    assert validation.transition_count == 2
    assert validation.coverage_fraction == 1.0
    assert validation.perplexity >= 1.0
    assert validation.deterministic_accuracy == 1.0


def test_markov_chain_baseline_comparison_detects_memory_gain() -> None:
    training_words = (
        chart_word_from_reports(
            [
                _report(ChartType.TWO_BODY_HIERARCHY),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
            ]
        ),
        chart_word_from_reports(
            [
                _report(ChartType.PERIODIC_ORBIT_NEIGHBORHOOD),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
            ]
        ),
    )
    heldout = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
        ]
    )

    chain = markov_chain_from_words(training_words)
    comparison = compare_markov_chain_to_independent_baseline(chain, training_words, (heldout,))

    assert comparison.beats_baseline is True
    assert comparison.log_likelihood_gain > 0.0
    assert comparison.perplexity_ratio < 1.0


def test_markov_chain_bootstrap_comparison_reports_uncertainty() -> None:
    training_words = (
        chart_word_from_reports(
            [
                _report(ChartType.TWO_BODY_HIERARCHY),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
            ]
        ),
        chart_word_from_reports(
            [
                _report(ChartType.PERIODIC_ORBIT_NEIGHBORHOOD),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
            ]
        ),
    )
    heldout = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
        ]
    )

    chain = markov_chain_from_words(training_words)
    bootstrap = bootstrap_markov_baseline_comparison(
        chain,
        training_words,
        (heldout,),
        resamples=64,
        random_seed=7,
    )

    assert bootstrap.comparison.beats_baseline is True
    assert bootstrap.resample_count == 64
    assert bootstrap.log_likelihood_gain_ci[0] <= bootstrap.log_likelihood_gain_ci[1]
    assert bootstrap.perplexity_ratio_ci[0] <= bootstrap.perplexity_ratio_ci[1]
    assert bootstrap.beats_baseline_fraction > 0.5
    assert "significant_baseline_win" in bootstrap.as_dict()


def test_markov_order_selection_prefers_memory_when_bic_improves() -> None:
    training_words = (
        chart_word_from_reports(
            [
                _report(ChartType.TWO_BODY_HIERARCHY),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
            ]
        ),
        chart_word_from_reports(
            [
                _report(ChartType.PERIODIC_ORBIT_NEIGHBORHOOD),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
                _report(ChartType.CHAOTIC_TRANSPORT),
                _report(ChartType.ESCAPE_TRANSPORT),
            ]
        ),
    )
    heldout = chart_word_from_reports(
        [
            _report(ChartType.TWO_BODY_HIERARCHY),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
            _report(ChartType.CHAOTIC_TRANSPORT),
            _report(ChartType.ESCAPE_TRANSPORT),
        ]
    )

    selection = select_markov_order(training_words, (heldout,), max_order=2)

    assert selection.selected_order >= 1
    assert selection.memory_selected is True
    assert selection.selected_score_margin >= 0.0
    assert len(selection.scores) == 3
    assert "selected_order" in selection.as_dict()
