
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


class SocialStructureAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "assess_social_class")

    async def assess_social_class(self, event: Event) -> List[Event]:
        # No condition to check as per the requirements
    
        # Generate reaction to assess social class
        observation = "Assessing social class based on incoming event."
        instruction = """
        Determine the social class of the individual based on current context and event information. 
        Provide an assessment of the social class and its influence on cultural capital. 
        Return the results in the following JSON format:
        
        {
            "social_class": "<Assessed social class>",
            "influence_on_cultural_capital": "<Influence on cultural capital>",
            "target_ids": ["<Target Individual agent ID or list of Individual agent IDs>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
        
        social_class = result.get('social_class', 'unknown')
        influence_on_cultural_capital = result.get('influence_on_cultural_capital', 'neutral')
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the agent's profile with the assessed social class and influence
        self.profile.update_data("social_class", social_class)
        self.profile.update_data("influence_on_cultural_capital", influence_on_cultural_capital)
    
        # Prepare and send the SocialClassAssessedEvent to the target agents
        events = []
        for target_id in target_ids:
            social_class_event = SocialClassAssessedEvent(
                self.profile_id, target_id, social_class=social_class, influence_on_cultural_capital=influence_on_cultural_capital
            )
            events.append(social_class_event)
        
        return events
