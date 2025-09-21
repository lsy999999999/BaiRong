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

class AlternativeOptionsAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("OptionsEvaluatedEvent", "present_alternatives")

    async def present_alternatives(self, event: Event) -> List[Event]:
        # Check if the event is an OptionsEvaluatedEvent
        if event.__class__.__name__ != "OptionsEvaluatedEvent":
            return []

        # Access the required variables from the event
        alternative_id = event.get('option_id', "")
        alternative_details = event.get('evaluation_criteria', "{}")

        # Prepare the instruction for the LLM to generate a reaction
        instruction = """
        The Alternative Options Agent needs to present alternatives to the Decision Maker Agent. 
        Each alternative has distinct costs, utilities, and risks. 
        Please provide the target_ids of the Decision Maker Agents who should receive the alternatives. 
        Return the response in the following JSON format:

        {
            "target_ids": ["<List of Decision Maker Agent IDs>"]
        }
        """
    
        # Observation context for the LLM
        observation = f"Alternative ID: {alternative_id}, Details: {alternative_details}"
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM response
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the AlternativesPresentedEvent to the Decision Maker Agents
        events = []
        for target_id in target_ids:
            alternatives_event = AlternativesPresentedEvent(self.profile_id, target_id, alternative_id, alternative_details)
            events.append(alternatives_event)
    
        return events