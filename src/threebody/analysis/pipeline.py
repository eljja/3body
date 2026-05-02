from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..solvers import AdaptiveIntegrator
from ..types import Scenario, TrajectoryResult
from .ensembles import PerturbationEnsemble
from .rule_miner import CandidateTransitionLaw, TransitionRuleMiner
from .survey import TransitionSurvey, TransitionSurveyResult
from .transition_model import transition_samples_from_reports


@dataclass(frozen=True, slots=True)
class ResearchRunResult:
    trajectories: dict[str, TrajectoryResult]
    survey: TransitionSurveyResult
    candidate_laws: tuple[CandidateTransitionLaw, ...]

    def summary(self) -> dict[str, object]:
        return {
            "trajectory_count": len(self.trajectories),
            "chart_distribution": self.survey.chart_distribution_rows(),
            "transitions": self.survey.graph.rows(),
            "candidate_laws": ResearchPipeline.law_rows(self.candidate_laws),
        }


@dataclass(slots=True)
class ResearchPipeline:
    """End-to-end loop: perturb, integrate, classify, model transitions, mine laws."""

    integrator: AdaptiveIntegrator = field(default_factory=AdaptiveIntegrator)
    ensemble: PerturbationEnsemble = field(default_factory=PerturbationEnsemble)
    survey: TransitionSurvey = field(default_factory=TransitionSurvey)
    rule_miner: TransitionRuleMiner = field(default_factory=TransitionRuleMiner)

    def run_perturbation_study(
        self,
        scenario: Scenario,
        count: int = 8,
        position_scale: float = 1.0e-3,
        velocity_scale: float = 1.0e-3,
        stride: int = 10,
    ) -> ResearchRunResult:
        members = self.ensemble.around_state(
            scenario.system,
            scenario.initial_state,
            count=count,
            position_scale=position_scale,
            velocity_scale=velocity_scale,
        )
        trajectories: dict[str, TrajectoryResult] = {}
        cases = {}
        for member in members:
            trajectory = self.integrator.integrate(
                scenario.system,
                scenario.t_span,
                member.state,
                t_eval=scenario.t_eval,
            )
            trajectories[member.name] = trajectory
            cases[member.name] = (scenario.system, trajectory)

        survey = self.survey.run(cases, stride=stride)
        samples = []
        for reports in survey.reports_by_name.values():
            samples.extend(transition_samples_from_reports(reports))
        laws = self.rule_miner.mine(samples)
        return ResearchRunResult(
            trajectories=trajectories,
            survey=survey,
            candidate_laws=laws,
        )

    @staticmethod
    def law_rows(laws: tuple[CandidateTransitionLaw, ...] | list[CandidateTransitionLaw]) -> list[dict[str, float | int | str]]:
        return [
            {
                "from": str(law.previous),
                "to": str(law.current),
                "feature": law.feature,
                "lower": law.lower,
                "upper": law.upper,
                "support": law.support,
                "contrast": law.contrast,
            }
            for law in laws
        ]
