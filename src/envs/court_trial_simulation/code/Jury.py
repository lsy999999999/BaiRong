from typing import Any, List, Optional
import json
import asyncio
from loguru import logger
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class Jury(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("EvidenceRulingEvent", "evaluate_evidence")
        self.register_event("TestimonyEvent", "evaluate_evidence")
        self.register_event("TrialManagementEvent", "form_verdict")
        self.register_event("EvidenceEvaluationEvent", "form_verdict")

    async def form_verdict(self, event: Event) -> List[Event]:
        trial_phase = event.trial_phase if event.__class__.__name__ == "TrialManagementEvent" else self.profile.get_data("trial_phase", "ongoing")
        evidence_evaluation = event.evidence_evaluation if event.__class__.__name__ == "EvidenceEvaluationEvent" else self.profile.get_data("evidence_evaluation", [])

        self.profile.update_data("trial_phase", trial_phase)
        self.profile.update_data("evidence_evaluation", evidence_evaluation)

        instruction = """Based on the evaluated evidence and the completed trial phase, form the final verdict for the trial.
        Please return the information in the following JSON format:
    
        {
        "verdict": "<The final verdict formed by the Jury>",
        "completion_status": "complete",
        "target_ids": ["ENV"]
        }
        """
        observation = f"Trial Phase: {trial_phase}, Evidence Evaluation: {evidence_evaluation}"
        result = await self.generate_reaction(instruction, observation)

        verdict = result.get('verdict', "undecided")
        completion_status = result.get('completion_status', "complete")
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("verdict", verdict)

        events = []
        for target_id in target_ids:
            verdict_event = VerdictFormedEvent(self.profile_id, target_id, verdict=verdict, completion_status=completion_status)
            events.append(verdict_event)

        return events

    async def evaluate_evidence(self, event: Event) -> List[Event]:
        evidence_admissibility = None
        testimony_details = None

        if event.__class__.__name__ == "EvidenceRulingEvent":
            evidence_admissibility = event.evidence_admissibility
            if evidence_admissibility != "admissible":
                return []
        elif event.__class__.__name__ == "TestimonyEvent":
            testimony_details = event.testimony_details
            if not testimony_details:
                return []
        else:
            return []

        instruction = """Evaluate the evidence provided during the trial. Consider the credibility and relevance of each item. 
        Return the evaluation results in the following JSON format:
        {
        "evidence_evaluation": ["<Evaluation result for each evidence item>"],
        "target_ids": ["<ID(s) of the agent(s) for the form_verdict action>"]
        }
        """
        observation = f"Testimony Details: {testimony_details}" if testimony_details else f"Evidence Admissibility: {evidence_admissibility}"
    
        result = await self.generate_reaction(instruction, observation)
    
        evidence_evaluation = result.get('evidence_evaluation', [])
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("evidence_evaluation", evidence_evaluation)

        events = []
        for target_id in target_ids:
            evaluation_event = EvidenceEvaluationEvent(self.profile_id, target_id, evidence_evaluation)
            events.append(evaluation_event)
    
        return events