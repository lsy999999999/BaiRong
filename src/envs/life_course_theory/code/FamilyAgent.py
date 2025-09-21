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

class FamilyAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_family_influence")

    async def initiate_family_influence(self, event: Event) -> List[Event]:
        # Check if the event is relevant for triggering the action
        if event.__class__.__name__ != "StartEvent":
            return []

        # Retrieve necessary agent data
        family_resources = self.profile.get_data("family_resources", 0.0)

        # Generate instruction for the LLM
        instruction = f"""
        Begin the process of providing support and influence to individual agents, impacting their health and education.
        Consider the available family resources ({family_resources}) and determine the type and level of support to provide.
        Please return the information in the following JSON format:

        {{
        "support_type": "<Type of family support provided>",
        "support_level": <Quantitative level of support>,
        "target_ids": ["<The string ID(s) of the IndividualAgent(s)>"]
        }}
        """

        # Generate reaction using the LLM
        observation = f"Current family resources: {family_resources}"
        result = await self.generate_reaction(instruction, observation)

        # Extract data from the LLM response
        support_type = result.get("support_type", "")
        support_level = result.get("support_level", 0.0)
        target_ids = result.get("target_ids", None)
        if target_ids is None:
            return []

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent data
        self.profile.update_data("family_support_provided", True)

        # Prepare and send FamilySupportEvent to each target individual agent
        events = []
        for target_id in target_ids:
            family_support_event = FamilySupportEvent(
                self.profile_id, target_id, support_type=support_type, support_level=support_level
            )
            events.append(family_support_event)

        return events