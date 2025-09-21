from typing import Any, List, Optional
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

class Aggressor(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_threat")

    async def initiate_threat(self, event: Event) -> List[Event]:
        # Access the required data from the agent's profile
        aggressor_id = self.profile.get_data("aggressor_id", "")
        defender_id = self.profile.get_data("defender_id", "")
        
        # Prepare the instruction for generate_reaction
        instruction = """The aggressor is initiating a threat towards the defender. 
        Please determine the level of threat and ensure to specify the target_ids for the event. 
        You should determine the actual target_ids as the defender, do not use the current defender_id(unknown_defender).
        Return the information in the following JSON format:
        {
            "threat_level": "<The severity level of the threat, integer>",
            "target_ids": ["<The string ID of the Defender agent>"]
        }
        """
        
        # Generate the reaction based on the current context
        # observation = f"Aggressor ID: {aggressor_id}, Defender ID: {defender_id}"
        result = await self.generate_reaction(instruction)
        
        # Extract the threat level and target_ids from the result
        threat_level = int(result.get('threat_level', self.profile.get_data("default_threat_level", 1)))
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids] if isinstance(target_ids, str) else []

        # Update the agent's data with the new threat level
        self.profile.update_data("threat_level", threat_level)
        self.profile.update_data("defender_id", target_ids[0])
        
        # Create and send the ThreatEvent to each target_id
        events = []
        for target_id in target_ids:
            threat_event = ThreatEvent(self.profile_id, target_id, threat_level=threat_level, aggressor_id=aggressor_id, defender_id=defender_id)
            events.append(threat_event)
        
        return events