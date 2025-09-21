
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


class MediaAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "generate_information")

    async def generate_information(self, event: Event) -> List[Event]:
        # Check if the incoming event is 'StartEvent'
        if event.__class__.__name__ != "StartEvent":
            return []
    
        # Generate new information content and determine target opinion leaders
        instruction = """
        You are a MediaAgent tasked with generating new information content for dissemination. 
        Your goal is to initiate the information spread process by targeting opinion leaders.
        Please generate a string for 'information_content' and decide on 'target_ids' which can be a single ID or a list of IDs of opinion leader agents.
        Return the information in the following JSON format:
    
        {
        "information_content": "<The content of the new information>",
        "target_ids": ["<The string ID or IDs of the opinion leader agents>"]
        }
        """
        
        # Generate the reaction using the LLM
        result = await self.generate_reaction(instruction)
    
        # Extract information content and target opinion leaders from the result
        information_content = result.get('information_content', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Create and send InformationGeneratedEvent to each target opinion leader
        events = []
        for target_id in target_ids:
            information_event = InformationGeneratedEvent(self.profile_id, target_id, information_content, target_ids)
            events.append(information_event)
    
        return events
