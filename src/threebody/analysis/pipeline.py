from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..solvers import AdaptiveIntegrator
from ..types import Scenario, TrajectoryResult
from .ensembles import PerturbationEnsemble
from .rule_miner import CandidateTransitionLaw, TransitionRuleMiner
from .survey import TransitionSurvey, TransitionSurveyResult
from .transition_model import transition_samples_from_reports
from .validation import TransitionLawValidation, TransitionLawValidator


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
            "transition_events": self.survey.transition_event_rows(),
            "transition_boundaries": self.survey.transition_boundary_rows(),
            "hysteresis_loops": self.survey.hysteresis_loop_rows(),
            "candidate_laws": ResearchPipeline.law_rows(self.candidate_laws),
        }


@dataclass(frozen=True, slots=True)
class ResearchValidationResult:
    discovery: ResearchRunResult
    validation: ResearchRunResult
    law_validations: tuple[TransitionLawValidation, ...]

    def summary(self) -> dict[str, object]:
        return {
            "discovery": self.discovery.summary(),
            "validation": self.validation.summary(),
            "law_validation": TransitionLawValidator.rows(self.law_validations),
        }


@dataclass(slots=True)
class ResearchPipeline:
    """End-to-end loop: perturb, integrate, classify, model transitions, mine laws."""

    integrator: AdaptiveIntegrator = field(default_factory=AdaptiveIntegrator)
    ensemble: PerturbationEnsemble = field(default_factory=PerturbationEnsemble)
    survey: TransitionSurvey = field(default_factory=TransitionSurvey)
    rule_miner: TransitionRuleMiner = field(default_factory=TransitionRuleMiner)
    law_validator: TransitionLawValidator = field(default_factory=TransitionLawValidator)

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

    def run_discovery_validation_study(
        self,
        scenario: Scenario,
        discovery_count: int = 8,
        validation_count: int = 8,
        position_scale: float = 1.0e-3,
        velocity_scale: float = 1.0e-3,
        stride: int = 10,
        validation_seed_offset: int = 10_000,
    ) -> ResearchValidationResult:
        discovery = self.run_perturbation_study(
            scenario,
            count=discovery_count,
            position_scale=position_scale,
            velocity_scale=velocity_scale,
            stride=stride,
        )
        validation_pipeline = ResearchPipeline(
            integrator=self.integrator,
            ensemble=PerturbationEnsemble(
                seed=self.ensemble.seed + validation_seed_offset,
                recenter_general_three_body=self.ensemble.recenter_general_three_body,
            ),
            survey=self.survey,
            rule_miner=self.rule_miner,
            law_validator=self.law_validator,
        )
        validation = validation_pipeline.run_perturbation_study(
            scenario,
            count=validation_count,
            position_scale=position_scale,
            velocity_scale=velocity_scale,
            stride=stride,
        )
        validation_samples = []
        for reports in validation.survey.reports_by_name.values():
            validation_samples.extend(transition_samples_from_reports(reports))
        law_validations = self.law_validator.validate(discovery.candidate_laws, validation_samples)
        return ResearchValidationResult(
            discovery=discovery,
            validation=validation,
            law_validations=law_validations,
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
