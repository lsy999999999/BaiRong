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

class Defendant(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("PleaNegotiationEvent", "consider_plea")

    async def consider_plea(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ != "PleaNegotiationEvent":
            return []

        # Retrieve plea terms from event
        plea_terms = event.plea_terms

        # Generate decision using LLM
        instruction = f"""
        You are the Defendant in a court trial simulation. The Defense Lawyer has proposed a plea deal with the following terms: {plea_terms}.
        Please evaluate these terms and decide whether to accept the plea deal. Your decision should be based on the favorability of the terms.
        Return the decision in the following JSON format:
        {{
            "plea_acceptance": "<accepted or rejected>",
            "target_ids": ["<The string ID of the Judge agent>"]
        }}
        """

        observation = f"Current plea terms: {plea_terms}"

        result = await self.generate_reaction(instruction, observation)

        plea_acceptance = result.get('plea_acceptance', "undecided")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update Defendant's profile with plea acceptance decision
        self.profile.update_data("plea_acceptance", plea_acceptance)

        # Create and send PleaDecisionEvent to the Judge
        events = []
        for target_id in target_ids:
            plea_decision_event = PleaDecisionEvent(self.profile_id, target_id, plea_acceptance)
            events.append(plea_decision_event)

        return events