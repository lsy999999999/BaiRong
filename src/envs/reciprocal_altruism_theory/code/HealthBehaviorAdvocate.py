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

class HealthBehaviorAdvocate(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_health_behavior_change")

    async def initiate_health_behavior_change(self, event: Event) -> List[Event]:
        # Condition check: the condition is 'null', proceed directly
        # Access required variables from agent profile
        advocate_id = self.profile.get_data("advocate_id", "")
        behavior_type = self.profile.get_data("behavior_type", "generic_behavior")
        intensity = self.profile.get_data("intensity", 1)
    
        # Generate reaction to determine recipient_id(s)
        instruction = """You are tasked with initiating a health behavior change. 
        Utilize the advocate's details and community network context to determine which recipient(s) should be targeted.
        Please return the information in the following JSON format:
    
        {
        "recipient_id": ["<The string ID of the recipient agent(s)>"],
        "advocate_id": "<The string ID of the health behavior advocate>",
        "behavior_type": "<Type of health behavior being initiated>",
        "intensity": <Intensity level of the behavior change initiation>
        }
        """
        
        observation = f"Advocate ID: {advocate_id}, Behavior Type: {behavior_type}, Intensity: {intensity}"
        result = await self.generate_reaction(instruction, observation)
        
        recipient_ids = result.get('recipient_id', [])
        if not isinstance(recipient_ids, list):
            recipient_ids = [recipient_ids]
    
        # Prepare and send the BehaviorChangeInitiatedEvent to each recipient
        events = []
        for recipient_id in recipient_ids:
            behavior_change_event = BehaviorChangeInitiatedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=recipient_id,
                advocate_id=advocate_id,
                recipient_id=recipient_id,
                behavior_type=behavior_type,
                intensity=intensity
            )
            events.append(behavior_change_event)
        
        return events