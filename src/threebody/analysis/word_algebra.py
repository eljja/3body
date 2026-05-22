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


@dataclass(frozen=True, slots=True)
class ChartWordMarkovPermutationControl:
    """Negative control that shuffles held-out symbols while preserving counts."""

    markov_validation: ChartWordMarkovValidation
    resample_count: int
    confidence_level: float
    random_seed: int
    control_mean_log_likelihood: float
    control_mean_log_likelihood_ci: tuple[float, float]
    actual_minus_control: float
    control_exceedance_fraction: float
    passes_permutation_control: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "markov_validation": self.markov_validation.as_dict(),
            "resample_count": self.resample_count,
            "confidence_level": self.confidence_level,
            "random_seed": self.random_seed,
            "control_mean_log_likelihood": self.control_mean_log_likelihood,
            "control_mean_log_likelihood_ci": list(self.control_mean_log_likelihood_ci),
            "actual_minus_control": self.actual_minus_control,
            "control_exceedance_fraction": self.control_exceedance_fraction,
            "passes_permutation_control": self.passes_permutation_control,
        }


@dataclass(frozen=True, slots=True)
class ChartWordMarkovOrderScore:
    """Held-out score for one symbolic Markov order."""

    order: int
    transition_count: int
    covered_transition_count: int
    coverage_fraction: float
    parameter_count: int
    mean_log_likelihood: float
    perplexity: float
    aic: float
    bic: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "order": self.order,
            "transition_count": self.transition_count,
            "covered_transition_count": self.covered_transition_count,
            "coverage_fraction": self.coverage_fraction,
            "parameter_count": self.parameter_count,
            "mean_log_likelihood": self.mean_log_likelihood,
            "perplexity": self.perplexity,
            "aic": self.aic,
            "bic": self.bic,
        }


@dataclass(frozen=True, slots=True)
class ChartWordMarkovOrderSelection:
    """Compare independent and memory-based symbolic dynamics orders."""

    selected_order: int
    criterion: str
    scores: tuple[ChartWordMarkovOrderScore, ...]
    memory_selected: bool
    selected_score_margin: float

    def as_dict(self) -> dict[str, object]:
        return {
            "selected_order": self.selected_order,
            "criterion": self.criterion,
            "scores": [score.as_dict() for score in self.scores],
            "memory_selected": self.memory_selected,
            "selected_score_margin": self.selected_score_margin,
        }


@dataclass(frozen=True, slots=True)
class PoincareSectionCandidate:
    """One candidate diagnostic section for symbolic crossing words."""

    coordinate: str
    quantile: float
    section_value: float
    direction: str
    word: ChartWord
    crossing_count: int
    distinct_symbol_count: int
    sufficient_crossings: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinate": self.coordinate,
            "quantile": self.quantile,
            "section_value": self.section_value,
            "direction": self.direction,
            "word": self.word.as_string(),
            "word_length": self.word.length,
            "crossing_count": self.crossing_count,
            "distinct_symbol_count": self.distinct_symbol_count,
            "sufficient_crossings": self.sufficient_crossings,
        }


@dataclass(frozen=True, slots=True)
class PoincareSectionSweep:
    """Quantile sweep used to find usable Poincare-section crossing words."""

    coordinate: str
    direction: str
    minimum_crossings: int
    best: PoincareSectionCandidate
    candidates: tuple[PoincareSectionCandidate, ...]

    @property
    def has_sufficient_section(self) -> bool:
        return self.best.sufficient_crossings

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinate": self.coordinate,
            "direction": self.direction,
            "minimum_crossings": self.minimum_crossings,
            "has_sufficient_section": self.has_sufficient_section,
            "best": self.best.as_dict(),
            "candidates": [candidate.as_dict() for candidate in self.candidates],
        }


@dataclass(frozen=True, slots=True)
class PoincareCoordinateSweep:
    """Sweep section coordinates and quantiles for usable Poincare words."""

    coordinates: tuple[str, ...]
    minimum_crossings: int
    best: PoincareSectionSweep
    sweeps: tuple[PoincareSectionSweep, ...]

    @property
    def has_sufficient_section(self) -> bool:
        return self.best.has_sufficient_section

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinates": list(self.coordinates),
            "minimum_crossings": self.minimum_crossings,
            "has_sufficient_section": self.has_sufficient_section,
            "best": self.best.as_dict(),
            "sweeps": [sweep.as_dict() for sweep in self.sweeps],
        }


@dataclass(frozen=True, slots=True)
class PoincareMarkovSectionRobustnessCandidate:
    """Markov-memory validation for one Poincare section candidate."""

    coordinate: str
    quantile: float
    section_value: float
    direction: str
    word_lengths: tuple[int, ...]
    training_word_lengths: tuple[int, ...]
    validation_word_lengths: tuple[int, ...]
    minimum_word_length: int
    significant_baseline_win: bool
    memory_order_selected: bool
    passes_permutation_control: bool
    permutation_control_gap: float
    passes: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinate": self.coordinate,
            "quantile": self.quantile,
            "section_value": self.section_value,
            "direction": self.direction,
            "word_lengths": list(self.word_lengths),
            "training_word_lengths": list(self.training_word_lengths),
            "validation_word_lengths": list(self.validation_word_lengths),
            "minimum_word_length": self.minimum_word_length,
            "significant_baseline_win": self.significant_baseline_win,
            "memory_order_selected": self.memory_order_selected,
            "passes_permutation_control": self.passes_permutation_control,
            "permutation_control_gap": self.permutation_control_gap,
            "passes": self.passes,
        }


@dataclass(frozen=True, slots=True)
class PoincareMarkovSectionRobustness:
    """Section-selection robustness summary for Poincare symbolic memory."""

    coordinate: str
    evaluated_count: int
    pass_count: int
    pass_fraction: float
    minimum_pass_count: int
    minimum_pass_fraction: float
    passes_robustness: bool
    candidates: tuple[PoincareMarkovSectionRobustnessCandidate, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinate": self.coordinate,
            "evaluated_count": self.evaluated_count,
            "pass_count": self.pass_count,
            "pass_fraction": self.pass_fraction,
            "minimum_pass_count": self.minimum_pass_count,
            "minimum_pass_fraction": self.minimum_pass_fraction,
            "passes_robustness": self.passes_robustness,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
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


def poincare_section_word_from_reports(
    reports: tuple[AnalysisReport, ...] | list[AnalysisReport],
    *,
    coordinate: str = "hierarchy_perturbation_strength",
    section_value: float | None = None,
    direction: str = "both",
) -> ChartWord:
    """Build a chart word from crossings of an explicit diagnostic section."""

    if len(reports) < 2:
        return refined_chart_word_from_reports(reports)
    values = np.asarray([_feature_value(report, coordinate) for report in reports], dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return refined_chart_word_from_reports(reports)
    section = float(np.median(finite_values) if section_value is None else section_value)
    direction = direction.lower()
    if direction not in {"both", "up", "down"}:
        raise ValueError("direction must be 'both', 'up', or 'down'.")
    symbols: list[object] = []
    for index in range(1, len(reports)):
        previous, current = values[index - 1], values[index]
        if not np.isfinite(previous) or not np.isfinite(current) or previous == current:
            continue
        previous_offset = previous - section
        current_offset = current - section
        if previous_offset == 0.0:
            previous_offset = -np.sign(current_offset)
        if current_offset == 0.0:
            current_offset = np.sign(previous_offset)
        if previous_offset * current_offset > 0.0:
            continue
        crossing_direction = "up" if current > previous else "down"
        if direction != "both" and crossing_direction != direction:
            continue
        alpha = float(np.clip((section - previous) / (current - previous), 0.0, 1.0))
        symbol = poincare_section_symbol(
            reports[index],
            coordinate=coordinate,
            section_value=section,
            direction=crossing_direction,
            alpha=alpha,
        )
        if symbols and symbols[-1] == symbol:
            continue
        symbols.append(symbol)
    if not symbols:
        return refined_chart_word_from_reports(reports)
    return ChartWord(tuple(symbols))


def poincare_section_sweep_from_reports(
    reports: tuple[AnalysisReport, ...] | list[AnalysisReport],
    *,
    coordinate: str = "hierarchy_perturbation_strength",
    quantiles: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
    direction: str = "both",
    minimum_crossings: int = 4,
) -> PoincareSectionSweep:
    """Sweep diagnostic section levels and select the richest crossing word."""

    values = np.asarray([_feature_value(report, coordinate) for report in reports], dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        empty = PoincareSectionCandidate(
            coordinate=coordinate,
            quantile=float("nan"),
            section_value=float("nan"),
            direction=direction,
            word=ChartWord(()),
            crossing_count=0,
            distinct_symbol_count=0,
            sufficient_crossings=False,
        )
        return PoincareSectionSweep(
            coordinate=coordinate,
            direction=direction,
            minimum_crossings=minimum_crossings,
            best=empty,
            candidates=(empty,),
        )
    candidates = []
    for quantile in quantiles:
        clipped = float(np.clip(quantile, 0.0, 1.0))
        section_value = float(np.quantile(finite_values, clipped))
        word = poincare_section_word_from_reports(
            reports,
            coordinate=coordinate,
            section_value=section_value,
            direction=direction,
        )
        crossing_count = word.length
        candidates.append(
            PoincareSectionCandidate(
                coordinate=coordinate,
                quantile=clipped,
                section_value=section_value,
                direction=direction,
                word=word,
                crossing_count=crossing_count,
                distinct_symbol_count=len(set(word.symbols)),
                sufficient_crossings=crossing_count >= minimum_crossings,
            )
        )
    best = max(candidates, key=lambda candidate: (candidate.crossing_count, candidate.distinct_symbol_count, -abs(candidate.quantile - 0.5)))
    return PoincareSectionSweep(
        coordinate=coordinate,
        direction=direction,
        minimum_crossings=minimum_crossings,
        best=best,
        candidates=tuple(candidates),
    )


def poincare_coordinate_sweep_from_reports(
    reports: tuple[AnalysisReport, ...] | list[AnalysisReport],
    *,
    coordinates: tuple[str, ...] = (
        "hierarchy_perturbation_strength",
        "hierarchy_ratio",
        "escape_index",
        "normalized_area",
        "shape_anisotropy",
        "virial_ratio",
        "outer_specific_energy",
    ),
    direction: str = "both",
    minimum_crossings: int = 4,
) -> PoincareCoordinateSweep:
    """Find the most event-rich section across common chart diagnostics."""

    sweeps = tuple(
        poincare_section_sweep_from_reports(
            reports,
            coordinate=coordinate,
            direction=direction,
            minimum_crossings=minimum_crossings,
        )
        for coordinate in coordinates
    )
    if not sweeps:
        empty = poincare_section_sweep_from_reports(
            reports,
            coordinate="hierarchy_perturbation_strength",
            direction=direction,
            minimum_crossings=minimum_crossings,
        )
        return PoincareCoordinateSweep((), minimum_crossings, empty, (empty,))
    best = max(
        sweeps,
        key=lambda sweep: (
            int(sweep.has_sufficient_section),
            sweep.best.crossing_count,
            sweep.best.distinct_symbol_count,
            -abs(sweep.best.quantile - 0.5),
        ),
    )
    return PoincareCoordinateSweep(
        coordinates=tuple(coordinates),
        minimum_crossings=minimum_crossings,
        best=best,
        sweeps=sweeps,
    )


def poincare_markov_section_robustness(
    report_sets: tuple[tuple[AnalysisReport, ...], ...] | list[tuple[AnalysisReport, ...]],
    section_sweep: PoincareSectionSweep,
    *,
    validation_report_sets: tuple[tuple[AnalysisReport, ...], ...] | list[tuple[AnalysisReport, ...]] | None = None,
    validation_index: int = 0,
    resamples: int = 128,
    permutations: int = 128,
    random_seed: int = 0,
    minimum_pass_count: int = 2,
    minimum_pass_fraction: float = 0.25,
) -> PoincareMarkovSectionRobustness:
    """Check whether Poincare Markov memory survives nearby section choices."""

    training_sets = tuple(tuple(reports) for reports in report_sets)
    validation_sets = (
        training_sets
        if validation_report_sets is None
        else tuple(tuple(reports) for reports in validation_report_sets)
    )
    if not training_sets or not validation_sets:
        return PoincareMarkovSectionRobustness(
            coordinate=section_sweep.coordinate,
            evaluated_count=0,
            pass_count=0,
            pass_fraction=0.0,
            minimum_pass_count=max(int(minimum_pass_count), 0),
            minimum_pass_fraction=float(minimum_pass_fraction),
            passes_robustness=False,
            candidates=(),
        )
    safe_validation_index = int(np.clip(validation_index, 0, len(validation_sets) - 1))
    rows: list[PoincareMarkovSectionRobustnessCandidate] = []
    for candidate_index, candidate in enumerate(section_sweep.candidates):
        if not np.isfinite(candidate.section_value):
            continue
        training_words = tuple(
            poincare_section_word_from_reports(
                reports,
                coordinate=candidate.coordinate,
                section_value=candidate.section_value,
                direction=candidate.direction,
            )
            for reports in training_sets
        )
        validation_words_all = tuple(
            poincare_section_word_from_reports(
                reports,
                coordinate=candidate.coordinate,
                section_value=candidate.section_value,
                direction=candidate.direction,
            )
            for reports in validation_sets
        )
        validation_words = (validation_words_all[safe_validation_index],)
        training_word_lengths = tuple(word.length for word in training_words)
        validation_word_lengths = tuple(word.length for word in validation_words_all)
        word_lengths = training_word_lengths + validation_word_lengths
        minimum_word_length = min(word_lengths) if word_lengths else 0
        sufficient_crossings = minimum_word_length >= section_sweep.minimum_crossings
        chain = markov_chain_from_words(training_words)
        bootstrap = bootstrap_markov_baseline_comparison(
            chain,
            training_words,
            validation_words,
            resamples=resamples,
            random_seed=random_seed + candidate_index,
        )
        order_selection = select_markov_order(training_words, validation_words, max_order=2)
        permutation_control = permutation_control_markov_validation(
            chain,
            validation_words,
            permutations=permutations,
            random_seed=random_seed + 1000 + candidate_index,
        )
        passes = bool(
            sufficient_crossings
            and bootstrap.significant_baseline_win
            and order_selection.memory_selected
            and permutation_control.passes_permutation_control
        )
        rows.append(
            PoincareMarkovSectionRobustnessCandidate(
                coordinate=candidate.coordinate,
                quantile=candidate.quantile,
                section_value=candidate.section_value,
                direction=candidate.direction,
                word_lengths=word_lengths,
                training_word_lengths=training_word_lengths,
                validation_word_lengths=validation_word_lengths,
                minimum_word_length=minimum_word_length,
                significant_baseline_win=bootstrap.significant_baseline_win,
                memory_order_selected=order_selection.memory_selected,
                passes_permutation_control=permutation_control.passes_permutation_control,
                permutation_control_gap=permutation_control.actual_minus_control,
                passes=passes,
            )
        )
    pass_count = sum(1 for row in rows if row.passes)
    evaluated_count = len(rows)
    pass_fraction = float(pass_count / evaluated_count) if evaluated_count else 0.0
    return PoincareMarkovSectionRobustness(
        coordinate=section_sweep.coordinate,
        evaluated_count=evaluated_count,
        pass_count=pass_count,
        pass_fraction=pass_fraction,
        minimum_pass_count=max(int(minimum_pass_count), 0),
        minimum_pass_fraction=float(minimum_pass_fraction),
        passes_robustness=bool(
            pass_count >= max(int(minimum_pass_count), 0)
            and pass_fraction >= float(minimum_pass_fraction)
        ),
        candidates=tuple(rows),
    )


def return_map_symbol(report: AnalysisReport, *, coordinate: str, event: str) -> str:
    value = _feature_value(report, coordinate)
    if coordinate == "hierarchy_perturbation_strength":
        bucket = _log_strength_bin(value)
    else:
        bucket = _linear_bin(value, width=2.0, maximum=9)
    return f"return:{coordinate}:{event}:B{bucket}:{refined_chart_symbol(report)}"


def poincare_section_symbol(
    report: AnalysisReport,
    *,
    coordinate: str,
    section_value: float,
    direction: str,
    alpha: float,
) -> str:
    if coordinate == "hierarchy_perturbation_strength":
        section_bucket = _log_strength_bin(section_value)
    else:
        section_bucket = _linear_bin(section_value, width=2.0, maximum=9)
    phase_bucket = _linear_bin(alpha, width=0.25, maximum=3)
    return f"section:{coordinate}:{direction}:S{section_bucket}:A{phase_bucket}:{refined_chart_symbol(report)}"


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


def permutation_control_markov_validation(
    chain: ChartWordMarkovChain,
    validation_words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    permutations: int = 512,
    confidence_level: float = 0.95,
    random_seed: int = 0,
    unseen_probability: float = 1.0e-12,
) -> ChartWordMarkovPermutationControl:
    """Test whether symbolic order beats shuffled held-out chart words."""

    validation = validate_markov_chain(chain, validation_words, unseen_probability=unseen_probability)
    permutations = max(int(permutations), 0)
    if validation.transition_count == 0 or permutations == 0:
        return ChartWordMarkovPermutationControl(
            markov_validation=validation,
            resample_count=permutations,
            confidence_level=float(confidence_level),
            random_seed=int(random_seed),
            control_mean_log_likelihood=validation.mean_log_likelihood,
            control_mean_log_likelihood_ci=(validation.mean_log_likelihood, validation.mean_log_likelihood),
            actual_minus_control=0.0,
            control_exceedance_fraction=1.0,
            passes_permutation_control=False,
        )

    generator = np.random.default_rng(random_seed)
    control_means = np.empty(permutations, dtype=float)
    for sample_index in range(permutations):
        permuted_words = _permuted_words(validation_words, generator)
        control = validate_markov_chain(chain, permuted_words, unseen_probability=unseen_probability)
        control_means[sample_index] = control.mean_log_likelihood

    alpha = float(np.clip(1.0 - confidence_level, 0.0, 1.0))
    lower_q = 100.0 * (alpha / 2.0)
    upper_q = 100.0 * (1.0 - alpha / 2.0)
    control_mean = float(np.mean(control_means))
    control_ci = (
        float(np.percentile(control_means, lower_q)),
        float(np.percentile(control_means, upper_q)),
    )
    actual_minus_control = float(validation.mean_log_likelihood - control_mean)
    exceedance = float(np.mean(control_means >= validation.mean_log_likelihood))
    return ChartWordMarkovPermutationControl(
        markov_validation=validation,
        resample_count=permutations,
        confidence_level=float(confidence_level),
        random_seed=int(random_seed),
        control_mean_log_likelihood=control_mean,
        control_mean_log_likelihood_ci=control_ci,
        actual_minus_control=actual_minus_control,
        control_exceedance_fraction=exceedance,
        passes_permutation_control=bool(validation.mean_log_likelihood > control_ci[1]),
    )


def select_markov_order(
    training_words: tuple[ChartWord, ...] | list[ChartWord],
    validation_words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    max_order: int = 2,
    criterion: str = "bic",
    unseen_probability: float = 1.0e-12,
) -> ChartWordMarkovOrderSelection:
    """Select symbolic memory depth against independent and higher-order alternatives."""

    max_order = max(int(max_order), 0)
    scores = tuple(
        _score_markov_order(
            training_words,
            validation_words,
            order=order,
            unseen_probability=unseen_probability,
        )
        for order in range(max_order + 1)
    )
    criterion_key = criterion.lower()
    if criterion_key not in {"aic", "bic"}:
        raise ValueError("criterion must be 'aic' or 'bic'.")
    values = [getattr(score, criterion_key) for score in scores]
    selected_index = int(np.argmin(values)) if values else 0
    selected = scores[selected_index]
    ordered_values = sorted(values)
    margin = float(ordered_values[1] - ordered_values[0]) if len(ordered_values) > 1 else 0.0
    return ChartWordMarkovOrderSelection(
        selected_order=selected.order,
        criterion=criterion_key,
        scores=scores,
        memory_selected=bool(selected.order > 0),
        selected_score_margin=margin,
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


def poincare_word_signature_rows(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
    *,
    coordinate: str = "hierarchy_perturbation_strength",
    section_value: float | None = None,
    direction: str = "both",
) -> list[dict[str, float | int | str | bool]]:
    rows = []
    for name, reports in reports_by_name.items():
        word = poincare_section_word_from_reports(
            reports,
            coordinate=coordinate,
            section_value=section_value,
            direction=direction,
        )
        signature = chart_word_signature(word)
        row = signature.as_dict()
        row["scenario"] = name
        row["coordinate"] = coordinate
        row["section_value"] = float("nan") if section_value is None else float(section_value)
        row["direction"] = direction
        rows.append(row)
    return rows


def poincare_section_sweep_rows(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
    *,
    coordinate: str = "hierarchy_perturbation_strength",
    direction: str = "both",
    minimum_crossings: int = 4,
) -> list[dict[str, object]]:
    rows = []
    for name, reports in reports_by_name.items():
        sweep = poincare_section_sweep_from_reports(
            reports,
            coordinate=coordinate,
            direction=direction,
            minimum_crossings=minimum_crossings,
        )
        row = sweep.best.as_dict()
        row["scenario"] = name
        row["has_sufficient_section"] = sweep.has_sufficient_section
        rows.append(row)
    return rows


def poincare_coordinate_sweep_rows(
    reports_by_name: dict[str, tuple[AnalysisReport, ...]],
    *,
    coordinates: tuple[str, ...] = (
        "hierarchy_perturbation_strength",
        "hierarchy_ratio",
        "escape_index",
        "normalized_area",
        "shape_anisotropy",
        "virial_ratio",
        "outer_specific_energy",
    ),
    direction: str = "both",
    minimum_crossings: int = 4,
) -> list[dict[str, object]]:
    rows = []
    for name, reports in reports_by_name.items():
        sweep = poincare_coordinate_sweep_from_reports(
            reports,
            coordinates=coordinates,
            direction=direction,
            minimum_crossings=minimum_crossings,
        )
        row = sweep.best.best.as_dict()
        row["scenario"] = name
        row["best_coordinate"] = sweep.best.coordinate
        row["has_sufficient_section"] = sweep.has_sufficient_section
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


def _permuted_words(
    words: tuple[ChartWord, ...] | list[ChartWord],
    generator: np.random.Generator,
) -> tuple[ChartWord, ...]:
    permuted = []
    for word in words:
        if word.length <= 1:
            permuted.append(word)
            continue
        symbols = list(word.symbols)
        generator.shuffle(symbols)
        permuted.append(ChartWord(tuple(symbols)))
    return tuple(permuted)


def _score_markov_order(
    training_words: tuple[ChartWord, ...] | list[ChartWord],
    validation_words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    order: int,
    unseen_probability: float,
) -> ChartWordMarkovOrderScore:
    counts = _ngram_transition_counts(training_words, order=order)
    states = {symbol for word in training_words for symbol in word.symbols}
    states.update(symbol for word in validation_words for symbol in word.symbols)
    state_count = max(len(states), 1)
    parameter_count = _ngram_parameter_count(counts, state_count=state_count)
    log_likelihood = 0.0
    transition_count = 0
    covered = 0
    for context, current in _ngram_validation_events(validation_words, order=order):
        transition_count += 1
        context_counts = counts.get(context)
        if context_counts is None:
            log_likelihood += float(np.log(unseen_probability))
            continue
        total = sum(context_counts.values())
        count = context_counts.get(current, 0)
        if total > 0 and count > 0:
            covered += 1
            probability = count / total
        else:
            probability = unseen_probability
        log_likelihood += float(np.log(max(probability, unseen_probability)))
    if transition_count == 0:
        mean = 0.0
        perplexity = 1.0
        aic = float(2 * parameter_count)
        bic = float(parameter_count * np.log(1.0))
    else:
        mean = float(log_likelihood / transition_count)
        perplexity = float(np.exp(-mean))
        aic = float(2 * parameter_count - 2 * log_likelihood)
        bic = float(parameter_count * np.log(transition_count) - 2 * log_likelihood)
    return ChartWordMarkovOrderScore(
        order=order,
        transition_count=transition_count,
        covered_transition_count=covered,
        coverage_fraction=float(covered / transition_count) if transition_count else 0.0,
        parameter_count=parameter_count,
        mean_log_likelihood=mean,
        perplexity=perplexity,
        aic=aic,
        bic=bic,
    )


def _ngram_transition_counts(
    words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    order: int,
) -> dict[tuple[object, ...], dict[object, int]]:
    counts: dict[tuple[object, ...], dict[object, int]] = {}
    for context, current in _ngram_validation_events(words, order=order):
        context_counts = counts.setdefault(context, {})
        context_counts[current] = context_counts.get(current, 0) + 1
    return counts


def _ngram_validation_events(
    words: tuple[ChartWord, ...] | list[ChartWord],
    *,
    order: int,
) -> list[tuple[tuple[object, ...], object]]:
    events: list[tuple[tuple[object, ...], object]] = []
    for word in words:
        start = max(order, 1)
        if word.length <= start:
            continue
        for index in range(start, word.length):
            context = tuple(word.symbols[index - order : index]) if order > 0 else ()
            events.append((context, word.symbols[index]))
    return events


def _ngram_parameter_count(counts: dict[tuple[object, ...], dict[object, int]], *, state_count: int) -> int:
    if not counts:
        return 0
    return int(sum(max(min(len(next_counts), state_count) - 1, 0) for next_counts in counts.values()))


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
