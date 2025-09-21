
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


class FamilyAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "provide_support")
        self.register_event("HealthThreatEvaluatedEvent", "provide_support")

    async def provide_support(self, event: Event) -> List[Event]:
        # Access family health priorities
        family_health_priorities = self.profile.get_data("family_health_priorities", [])
    
        # Generate reaction to decide on support type and intensity
        instruction = """You are a FamilyAgent tasked with providing support to family members for adopting health behaviors. 
        Consider the family's health priorities: {family_health_priorities}. 
        Determine the type of support and its intensity to be provided. 
        Ensure to specify 'target_ids' which can be a single ID or a list of IDs. 
        The response should be in the following JSON format:
    
        {{
        "support_type": "<Type of support provided>",
        "intensity": <Intensity level of support>,
        "target_ids": ["<ID of family member(s) receiving support>"]
        }}
        """
        observation = f"Event received: {event.__class__.__name__}"
        result = await self.generate_reaction(instruction.format(family_health_priorities=family_health_priorities), observation)
    
        support_type = result.get('support_type', "emotional")
        intensity = result.get('intensity', 1)
        target_ids = result.get('target_ids', [])
    
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state with support provided
        self.profile.update_data("support_provided", support_type)
    
        # Prepare and send SupportProvidedEvent to target individual(s)
        events = []
        for target_id in target_ids:
            support_event = SupportProvidedEvent(self.profile_id, target_id, support_type=support_type, intensity=intensity)
            events.append(support_event)
    
        return events
