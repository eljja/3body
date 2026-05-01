from __future__ import annotations

from threebody.analysis import ChartTransition, ChartType, TransitionGraph


def test_transition_graph_accumulates_probabilities() -> None:
    graph = TransitionGraph()
    graph.add(
        [
            ChartTransition(1, 0.1, ChartType.DEMOCRATIC_THREE_BODY, ChartType.CHAOTIC_TRANSPORT, "a"),
            ChartTransition(2, 0.2, ChartType.DEMOCRATIC_THREE_BODY, ChartType.CHAOTIC_TRANSPORT, "b"),
            ChartTransition(3, 0.3, ChartType.DEMOCRATIC_THREE_BODY, ChartType.TWO_BODY_HIERARCHY, "c"),
        ]
    )

    assert graph.probability(ChartType.DEMOCRATIC_THREE_BODY, ChartType.CHAOTIC_TRANSPORT) == 2.0 / 3.0
    matrix, charts = graph.matrix()
    assert matrix.shape == (len(charts), len(charts))
    assert graph.rows()[0]["count"] >= 1
