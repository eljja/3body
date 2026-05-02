from __future__ import annotations

import numpy as np

from threebody.analysis import ChartType, TransitionRuleMiner, TransitionSample


def test_transition_rule_miner_finds_contrasting_feature_interval() -> None:
    samples = [
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.CHAOTIC_TRANSPORT, np.array([5.0, 1.0]), ("h", "v")),
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.CHAOTIC_TRANSPORT, np.array([5.2, 1.2]), ("h", "v")),
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.ESCAPE_TRANSPORT, np.array([10.0, 1.1]), ("h", "v")),
        TransitionSample(ChartType.TWO_BODY_HIERARCHY, ChartType.ESCAPE_TRANSPORT, np.array([10.3, 1.0]), ("h", "v")),
    ]

    laws = TransitionRuleMiner(min_support=2).mine(samples)

    assert laws
    assert laws[0].support == 2
    assert laws[0].feature == "h"
