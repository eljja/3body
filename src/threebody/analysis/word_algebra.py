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


@dataclass(frozen=True, slots=True)
class ChartWordMarkovChain:
    """First-order symbolic dynamics model over chart-word symbols."""

    states: tuple[object, ...]
    transition_counts: tuple[tuple[int, ...], ...]
    transition_probabilities: tuple[tuple[float, ...], ...]
    stationary_distribution: tuple[float, ...]
    absorbing_states: tuple[object, ...]
    transition_entropy_rate: float

    def as_dict(self) -> dict[str, object]:
        return {
            "states": [str(state) for state in self.states],
            "transition_counts": [list(row) for row in self.transition_counts],
            "transition_probabilities": [list(row) for row in self.transition_probabilities],
            "stationary_distribution": list(self.stationary_distribution),
            "absorbing_states": [str(state) for state in self.absorbing_states],
            "transition_entropy_rate": self.transition_entropy_rate,
        }


@dataclass(frozen=True, slots=True)
class ChartWordMarkovValidation:
    """Held-out likelihood validation for a symbolic Markov chain."""

    transition_count: int
    covered_transition_count: int
    unseen_transition_count: int
    coverage_fraction: float
    mean_log_likelihood: float
    perplexity: float
    deterministic_accuracy: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "transition_count": self.transition_count,
            "covered_transition_count": self.covered_transition_count,
            "unseen_transition_count": self.unseen_transition_count,
            "coverage_fraction": self.coverage_fraction,
            "mean_log_likelihood": self.mean_log_likelihood,
            "perplexity": self.perplexity,
            "deterministic_accuracy": self.deterministic_accuracy,
        }


@dataclass(frozen=True, slots=True)
class ChartWordMarkovBaselineComparison:
    """Compare Markov validation against an independent-symbol baseline."""

    markov_validation: ChartWordMarkovValidation
    baseline_mean_log_likelihood: float
    baseline_perplexity: float
    log_likelihood_gain: float
    perplexity_ratio: float
    beats_baseline: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "markov_validation": self.markov_validation.as_dict(),
            "baseline_mean_log_likelihood": self.baseline_mean_log_likelihood,
            "baseline_perplexity": self.baseline_perplexity,
            "log_likelihood_gain": self.log_likelihood_gain,
            "perplexity_ratio": self.perplexity_ratio,
            "beats_baseline": self.beats_baseline,
        }


@dataclass(frozen=True, slots=True)
class ChartWordMarkovBootstrapComparison:
    """Bootstrap uncertainty estimate for a Markov-vs-independent comparison."""

    comparison: ChartWordMarkovBaselineComparison
    resample_count: int
    confidence_level: float
    random_seed: int
    log_likelihood_gain_ci: tuple[float, float]
    perplexity_ratio_ci: tuple[float, float]
    beats_baseline_fraction: float
    significant_baseline_win: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "comparison": self.comparison.as_dict(),
            "resample_count": self.resample_count,
            "confidence_level": self.confidence_level,
            "random_seed": self.random_seed,
            "log_likelihood_gain_ci": list(self.log_likelihood_gain_ci),
            "perplexity_ratio_ci": list(self.perplexity_ratio_ci),
            "beats_baseline_fraction": self.beats_baseline_fraction,
            "significant_baseline_win": self.significant_baseline_win,
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


def markov_chain_from_words(words: tuple[ChartWord, ...] | list[ChartWord]) -> ChartWordMarkovChain:
    """Fit a first-order Markov chain to symbolic chart words."""

    states = tuple(sorted({symbol for word in words for symbol in word.symbols}, key=str))
    if not states:
        return ChartWordMarkovChain((), (), (), (), (), 0.0)
    index_by_state = {state: index for index, state in enumerate(states)}
    counts = np.zeros((len(states), len(states)), dtype=int)
    for word in words:
        for previous, current in word.transition_pairs():
            counts[index_by_state[previous], index_by_state[current]] += 1
    probabilities = np.zeros(counts.shape, dtype=float)
    for row_index, row in enumerate(counts):
        total = int(np.sum(row))
        if total > 0:
            probabilities[row_index] = row / total
        else:
            probabilities[row_index, row_index] = 1.0
    stationary = _stationary_distribution(probabilities)
    absorbing = tuple(
        state
        for state_index, state in enumerate(states)
        if probabilities[state_index, state_index] >= 1.0 - 1.0e-12
    )
    entropy_rate = 0.0
    for state_index, row in enumerate(probabilities):
        nonzero = row[row > 0.0]
        entropy_rate += stationary[state_index] * float(-np.sum(nonzero * np.log2(nonzero)))
    return ChartWordMarkovChain(
        states=states,
        transition_counts=tuple(tuple(int(value) for value in row) for row in counts),
        transition_probabilities=tuple(tuple(float(value) for value in row) for row in probabilities),
        stationary_distribution=tuple(float(value) for value in stationary),
        absorbing_states=absorbing,
        transition_entropy_rate=float(entropy_rate),
    )


def hysteresis_markov_chain_from_reports(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
    *,
    coordinate: str = "hierarchy_perturbation_strength",
) -> ChartWordMarkovChain:
    """Build the Markov model used for hysteresis-memory grammar analysis."""

    words = tuple(return_map_word_from_reports(reports, coordinate=coordinate) for reports in reports_by_name.values())
    return markov_chain_from_words(words)


def validate_markov_chain(
    chain: ChartWordMarkovChain,
    words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    unseen_probability: float = 1.0e-12,
) -> ChartWordMarkovValidation:
    """Evaluate held-out chart words under a fitted symbolic Markov chain."""

    if not chain.states:
        return ChartWordMarkovValidation(0, 0, 0, 0.0, float("-inf"), float("inf"), 0.0)
    index_by_state = {state: index for index, state in enumerate(chain.states)}
    probabilities = np.asarray(chain.transition_probabilities, dtype=float)
    transition_count = 0
    covered = 0
    unseen = 0
    log_likelihood = 0.0
    deterministic_hits = 0
    for word in words:
        for previous, current in word.transition_pairs():
            transition_count += 1
            previous_index = index_by_state.get(previous)
            current_index = index_by_state.get(current)
            if previous_index is None or current_index is None:
                unseen += 1
                log_likelihood += float(np.log(unseen_probability))
                continue
            probability = float(probabilities[previous_index, current_index])
            if probability > 0.0:
                covered += 1
                log_likelihood += float(np.log(probability))
            else:
                unseen += 1
                log_likelihood += float(np.log(unseen_probability))
            if int(np.argmax(probabilities[previous_index])) == current_index:
                deterministic_hits += 1
    if transition_count == 0:
        return ChartWordMarkovValidation(0, 0, 0, 0.0, 0.0, 1.0, 0.0)
    mean_log_likelihood = float(log_likelihood / transition_count)
    return ChartWordMarkovValidation(
        transition_count=transition_count,
        covered_transition_count=covered,
        unseen_transition_count=unseen,
        coverage_fraction=float(covered / transition_count),
        mean_log_likelihood=mean_log_likelihood,
        perplexity=float(np.exp(-mean_log_likelihood)),
        deterministic_accuracy=float(deterministic_hits / transition_count),
    )


def compare_markov_chain_to_independent_baseline(
    chain: ChartWordMarkovChain,
    training_words: tuple[ChartWord, ...] | list[ChartWord],
    validation_words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    unseen_probability: float = 1.0e-12,
) -> ChartWordMarkovBaselineComparison:
    """Compare first-order grammar memory against a next-symbol frequency baseline."""

    validation = validate_markov_chain(chain, validation_words, unseen_probability=unseen_probability)
    baseline_probabilities = _next_symbol_baseline_probabilities(training_words)
    log_likelihood = 0.0
    transition_count = 0
    for word in validation_words:
        for _previous, current in word.transition_pairs():
            transition_count += 1
            probability = baseline_probabilities.get(current, unseen_probability)
            log_likelihood += float(np.log(max(probability, unseen_probability)))
    if transition_count == 0:
        baseline_mean = 0.0
        baseline_perplexity = 1.0
    else:
        baseline_mean = float(log_likelihood / transition_count)
        baseline_perplexity = float(np.exp(-baseline_mean))
    gain = float(validation.mean_log_likelihood - baseline_mean)
    ratio = float(validation.perplexity / baseline_perplexity) if baseline_perplexity > 0.0 else float("inf")
    return ChartWordMarkovBaselineComparison(
        markov_validation=validation,
        baseline_mean_log_likelihood=baseline_mean,
        baseline_perplexity=baseline_perplexity,
        log_likelihood_gain=gain,
        perplexity_ratio=ratio,
        beats_baseline=bool(gain > 0.0 and ratio < 1.0),
    )


def bootstrap_markov_baseline_comparison(
    chain: ChartWordMarkovChain,
    training_words: tuple[ChartWord, ...] | list[ChartWord],
    validation_words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    resamples: int = 512,
    confidence_level: float = 0.95,
    random_seed: int = 0,
    unseen_probability: float = 1.0e-12,
) -> ChartWordMarkovBootstrapComparison:
    """Estimate uncertainty in the Markov gain by resampling held-out transitions."""

    comparison = compare_markov_chain_to_independent_baseline(
        chain,
        training_words,
        validation_words,
        unseen_probability=unseen_probability,
    )
    pairs = _transition_pairs_from_words(validation_words)
    if not pairs or resamples <= 0:
        return ChartWordMarkovBootstrapComparison(
            comparison=comparison,
            resample_count=max(int(resamples), 0),
            confidence_level=float(confidence_level),
            random_seed=int(random_seed),
            log_likelihood_gain_ci=(comparison.log_likelihood_gain, comparison.log_likelihood_gain),
            perplexity_ratio_ci=(comparison.perplexity_ratio, comparison.perplexity_ratio),
            beats_baseline_fraction=float(comparison.beats_baseline),
            significant_baseline_win=comparison.beats_baseline,
        )

    index_by_state = {state: index for index, state in enumerate(chain.states)}
    probabilities = np.asarray(chain.transition_probabilities, dtype=float)
    baseline_probabilities = _next_symbol_baseline_probabilities(training_words)
    gains = np.asarray(
        [
            _markov_transition_log_probability(
                previous,
                current,
                index_by_state=index_by_state,
                probabilities=probabilities,
                unseen_probability=unseen_probability,
            )
            - _baseline_transition_log_probability(
                current,
                baseline_probabilities=baseline_probabilities,
                unseen_probability=unseen_probability,
            )
            for previous, current in pairs
        ],
        dtype=float,
    )
    generator = np.random.default_rng(random_seed)
    means = np.empty(int(resamples), dtype=float)
    for sample_index in range(int(resamples)):
        draw = generator.integers(0, len(gains), size=len(gains))
        means[sample_index] = float(np.mean(gains[draw]))
    alpha = float(np.clip(1.0 - confidence_level, 0.0, 1.0))
    lower_q = 100.0 * (alpha / 2.0)
    upper_q = 100.0 * (1.0 - alpha / 2.0)
    gain_ci = (
        float(np.percentile(means, lower_q)),
        float(np.percentile(means, upper_q)),
    )
    ratio_samples = np.exp(-means)
    ratio_ci = (
        float(np.percentile(ratio_samples, lower_q)),
        float(np.percentile(ratio_samples, upper_q)),
    )
    beats_fraction = float(np.mean(means > 0.0))
    return ChartWordMarkovBootstrapComparison(
        comparison=comparison,
        resample_count=int(resamples),
        confidence_level=float(confidence_level),
        random_seed=int(random_seed),
        log_likelihood_gain_ci=gain_ci,
        perplexity_ratio_ci=ratio_ci,
        beats_baseline_fraction=beats_fraction,
        significant_baseline_win=bool(gain_ci[0] > 0.0 and ratio_ci[1] < 1.0),
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


def _stationary_distribution(probabilities: np.ndarray) -> np.ndarray:
    if probabilities.size == 0:
        return np.zeros(0, dtype=float)
    values, vectors = np.linalg.eig(probabilities.T)
    index = int(np.argmin(np.abs(values - 1.0)))
    stationary = np.real(vectors[:, index])
    if np.all(stationary <= 0.0):
        stationary = -stationary
    stationary = np.maximum(stationary, 0.0)
    total = float(np.sum(stationary))
    if total <= 0.0 or not np.isfinite(total):
        return np.ones(probabilities.shape[0], dtype=float) / probabilities.shape[0]
    return stationary / total


def _next_symbol_baseline_probabilities(words: tuple[ChartWord, ...] | list[ChartWord]) -> dict[object, float]:
    counts: dict[object, int] = {}
    total = 0
    for word in words:
        for _previous, current in word.transition_pairs():
            counts[current] = counts.get(current, 0) + 1
            total += 1
    if total == 0:
        return {}
    return {symbol: count / total for symbol, count in counts.items()}


def _transition_pairs_from_words(words: tuple[ChartWord, ...] | list[ChartWord]) -> list[tuple[object, object]]:
    pairs: list[tuple[object, object]] = []
    for word in words:
        pairs.extend(word.transition_pairs())
    return pairs


def _markov_transition_log_probability(
    previous: object,
    current: object,
    *,
    index_by_state: dict[object, int],
    probabilities: np.ndarray,
    unseen_probability: float,
) -> float:
    previous_index = index_by_state.get(previous)
    current_index = index_by_state.get(current)
    if previous_index is None or current_index is None:
        return float(np.log(unseen_probability))
    probability = float(probabilities[previous_index, current_index])
    return float(np.log(max(probability, unseen_probability)))


def _baseline_transition_log_probability(
    current: object,
    *,
    baseline_probabilities: dict[object, float],
    unseen_probability: float,
) -> float:
    probability = baseline_probabilities.get(current, unseen_probability)
    return float(np.log(max(probability, unseen_probability)))


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
