from __future__ import annotations

from dataclasses import dataclass

from .boundaries import TransitionBoundaryEstimate
from .types import ChartType


@dataclass(frozen=True, slots=True)
class TransitionHysteresisLoop:
    low_crossing_previous: ChartType
    low_crossing_current: ChartType
    high_crossing_previous: ChartType
    high_crossing_current: ChartType
    coordinate: str
    low_crossing: float
    high_crossing: float
    width: float
    low_crossing_direction: str
    high_crossing_direction: str
    support: int

    @property
    def is_open(self) -> bool:
        return self.width > 0.0


def detect_hysteresis_loops(
    estimates: tuple[TransitionBoundaryEstimate, ...] | list[TransitionBoundaryEstimate],
) -> tuple[TransitionHysteresisLoop, ...]:
    by_edge = {(estimate.previous, estimate.current, estimate.coordinate): estimate for estimate in estimates}
    loops: list[TransitionHysteresisLoop] = []
    seen: set[frozenset[tuple[ChartType, ChartType]]] = set()
    for estimate in estimates:
        reverse = by_edge.get((estimate.current, estimate.previous, estimate.coordinate))
        if reverse is None:
            continue
        edge_key = frozenset({(estimate.previous, estimate.current), (estimate.current, estimate.previous)})
        if edge_key in seen:
            continue
        seen.add(edge_key)

        first = estimate
        second = reverse
        if first.crossing_mean <= second.crossing_mean:
            lower_crossing = first
            upper_crossing = second
        else:
            lower_crossing = second
            upper_crossing = first
        loops.append(
            TransitionHysteresisLoop(
                low_crossing_previous=lower_crossing.previous,
                low_crossing_current=lower_crossing.current,
                high_crossing_previous=upper_crossing.previous,
                high_crossing_current=upper_crossing.current,
                coordinate=estimate.coordinate,
                low_crossing=lower_crossing.crossing_mean,
                high_crossing=upper_crossing.crossing_mean,
                width=abs(upper_crossing.crossing_mean - lower_crossing.crossing_mean),
                low_crossing_direction=lower_crossing.direction,
                high_crossing_direction=upper_crossing.direction,
                support=lower_crossing.support + upper_crossing.support,
            )
        )
    return tuple(
        sorted(loops, key=lambda loop: (str(loop.low_crossing_previous), str(loop.low_crossing_current), loop.coordinate))
    )


def hysteresis_loop_rows(
    loops: tuple[TransitionHysteresisLoop, ...] | list[TransitionHysteresisLoop],
) -> list[dict[str, float | int | str | bool]]:
    return [
        {
            "low_crossing_from": str(loop.low_crossing_previous),
            "low_crossing_to": str(loop.low_crossing_current),
            "high_crossing_from": str(loop.high_crossing_previous),
            "high_crossing_to": str(loop.high_crossing_current),
            "coordinate": loop.coordinate,
            "low_crossing": loop.low_crossing,
            "high_crossing": loop.high_crossing,
            "width": loop.width,
            "low_crossing_direction": loop.low_crossing_direction,
            "high_crossing_direction": loop.high_crossing_direction,
            "support": loop.support,
            "is_open": loop.is_open,
        }
        for loop in loops
    ]
