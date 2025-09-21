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

class HealthcareSystemAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("HealthStateChangeEvent", "manage_treatment")

    async def manage_treatment(self, event: Event) -> List[Event]:
        # Condition Check: Since the condition is "null", proceed directly with handler logic

        # Access required event data
        individual_id = event.individual_id
        requires_treatment = event.requires_treatment

        # Observation for LLM decision making
        observation = f"Individual ID: {individual_id}, Requires Treatment: {requires_treatment}"

        # Instruction for LLM to decide treatment management and target_ids
        instruction = """
        Oversee the treatment and recovery processes for individuals who have changed health states. 
        Based on the 'requires_treatment' field, determine the treatment outcome and recovery status.
        Please return the information in the following JSON format:

        {
        "treatment_status": "<Current status of treatment outcome>",
        "recovery_status": "<Final recovery status of the individual>",
        "target_ids": ["<The string ID(s) of the EnvAgent>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        treatment_status = result.get('treatment_status', "pending")
        recovery_status = result.get('recovery_status', "not_recovered")
        target_ids = result.get('target_ids', [])

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent data
        self.profile.update_data("treatment_status", treatment_status)
        self.profile.update_data("recovery_status", recovery_status)

        # Prepare and send TreatmentOutcomeEvent(s)
        events = []
        for target_id in target_ids:
            treatment_outcome_event = TreatmentOutcomeEvent(
                self.profile_id, target_id, individual_id, treatment_status, recovery_status
            )
            events.append(treatment_outcome_event)

        return events