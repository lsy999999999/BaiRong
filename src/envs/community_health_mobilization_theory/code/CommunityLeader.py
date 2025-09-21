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

class CommunityLeader(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_mobilization")
        self.register_event("GuidanceEvent", "initiate_mobilization")

    async def initiate_mobilization(self, event: Event) -> List[Event]:
        # No condition check needed as the condition is 'null'
        
        # Access required environmental variables
        community_context = await self.get_env_data("community_context", "default_context")
        available_resources = await self.get_env_data("available_resources", "default_resources")
        
        # Formulate the instruction for the LLM
        instruction = f"""
        Organize community health mobilization activities based on the following context:
        - Community Context: {community_context}
        - Available Resources: {available_resources}
        
        Please generate mobilization activity details and decide on the target community members to engage.
        Return the information in the following JSON format:
        
        {{
        "activity_details": "<Description of the health mobilization activity>",
        "target_ids": ["<String ID of the Community Member(s)>"]
        }}
        """
        
        # Generate the reaction using the LLM
        observation = f"Community Context: {community_context}, Available Resources: {available_resources}"
        result = await self.generate_reaction(instruction, observation)
        
        # Extract the details from the result
        activity_details = result.get('activity_details', 'None')  # Ensure default value is provided
        target_ids = result.get('target_ids', [])
        
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Prepare and send the MobilizationEvent to the specified target_ids
        events = []
        for target_id in target_ids:
            mobilization_event = MobilizationEvent(self.profile_id, target_id, activity_details)
            events.append(mobilization_event)
        
        return events