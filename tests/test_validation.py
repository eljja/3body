from __future__ import annotations

import numpy as np

from threebody.analysis import (
    CandidateTransitionLaw,
    ChartType,
    TransitionLawValidator,
    TransitionSample,
)


def test_transition_law_validator_reports_precision_and_recall() -> None:
    law = CandidateTransitionLaw(
        previous=ChartType.TWO_BODY_HIERARCHY,
        current=ChartType.CHAOTIC_TRANSPORT,
        feature="h",
        lower=4.0,
        upper=6.0,
        center=5.0,
        width=1.0,
        support=2,
        contrast=1.0,
    )
    samples = [
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.CHAOTIC_TRANSPORT, np.array([5.0]), ("h",)),
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.ESCAPE_TRANSPORT, np.array([5.5]), ("h",)),
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.CHAOTIC_TRANSPORT, np.array([9.0]), ("h",)),
    ]

    validation = TransitionLawValidator().validate([law], samples)[0]

    assert validation.true_positives == 1
    assert validation.false_positives == 1
    assert validation.false_negatives == 1
    assert validation.precision == 0.5
    assert validation.recall == 0.5
