
from typing import Any, List,Optional
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


class Prosecutor(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_evidence")

    async def evaluate_evidence(self, event: Event) -> List[Event]:
        # Condition check: Ensure evidence is available for evaluation
        evidence_quality = self.profile.get_data("evidence_quality", None)
        conviction_likelihood = self.profile.get_data("conviction_likelihood", None)

        if evidence_quality is None or conviction_likelihood is None:
            return []  # Condition not met, return empty list

        # Craft instruction for generating prosecution decision and target_ids
        instruction = """Evaluate the 'evidence_quality' and 'conviction_likelihood' to determine the 'prosecution_decision'.
        Return the decision in the following JSON format:
        {
            "prosecution_decision": "<Decision on whether to proceed with prosecution, choose from 'proceed' or 'not_proceed'>",
            "target_ids": ["<ID(s) of the agents to whom the event should be sent>"]
            "evidence_details": "<Details of the evidence to be presented if prosecution_decision is 'proceed'>"
        }
        Please ensure that target_ids should be list of Judge IDs if prosecution_decision is 'proceed' and list of DefenseLawyer IDs if prosecution_decision is 'not_proceed'.
        """

        observation = f"Evidence Quality: {evidence_quality}, Conviction Likelihood: {conviction_likelihood}"
        result = await self.generate_reaction(instruction, observation)

        prosecution_decision = result.get('prosecution_decision', "undecided")
        target_ids = result.get('target_ids', None)
        evidence_details = result.get('evidence_details', "")
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's profile with the prosecution decision
        self.profile.update_data("prosecution_decision", prosecution_decision)

        # Prepare outgoing events based on prosecution decision
        events = []
        for target_id in target_ids:
            if prosecution_decision == "proceed":
                evidence_event = EvidenceEvaluatedEvent(self.profile_id, target_id, evidence_details=evidence_details, ruling_request="pending", prosecution_decision=prosecution_decision)
                events.append(evidence_event)
            else:
                decision_event = ProsecutionDecisionEvent(self.profile_id, target_id, prosecution_decision=prosecution_decision, evidence_quality=evidence_quality, conviction_likelihood=conviction_likelihood)
                events.append(decision_event)

        return events
