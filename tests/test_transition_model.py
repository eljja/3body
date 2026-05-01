from __future__ import annotations

import numpy as np

from threebody.analysis import (
    ChartType,
    FeatureConditionedTransitionModel,
    TransitionSample,
)


def test_feature_conditioned_transition_model_predicts_nearest_transition() -> None:
    samples = [
        TransitionSample(
            ChartType.TWO_BODY_HIERARCHY,
            ChartType.CHAOTIC_TRANSPORT,
            np.array([5.0, 1.0]),
            ("hierarchy_ratio", "virial_offset"),
        ),
        TransitionSample(
            ChartType.TWO_BODY_HIERARCHY,
            ChartType.CHAOTIC_TRANSPORT,
            np.array([5.2, 1.1]),
            ("hierarchy_ratio", "virial_offset"),
        ),
        TransitionSample(
            ChartType.TWO_BODY_HIERARCHY,
            ChartType.ESCAPE_TRANSPORT,
            np.array([10.0, 3.0]),
            ("hierarchy_ratio", "virial_offset"),
        ),
    ]
    model = FeatureConditionedTransitionModel()

    model.fit(samples)
    prediction = model.predict(ChartType.TWO_BODY_HIERARCHY, np.array([5.1, 1.05]))[0]

    assert prediction.current == ChartType.CHAOTIC_TRANSPORT
    assert prediction.score > 0.0


def test_feature_conditioned_transition_model_rejects_mixed_features() -> None:
    model = FeatureConditionedTransitionModel()
    samples = [
        TransitionSample(ChartType.DEMOCRATIC_THREE_BODY, ChartType.CHAOTIC_TRANSPORT, np.array([1.0]), ("a",)),
        TransitionSample(ChartType.DEMOCRATIC_THREE_BODY, ChartType.ESCAPE_TRANSPORT, np.array([1.0]), ("b",)),
    ]

    try:
        model.fit(samples)
    except ValueError as error:
        assert "feature names" in str(error)
    else:
        raise AssertionError("Expected mixed feature names to fail.")
