
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


class ContractBreakdownAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("LawEnforcementEvent", "simulate_conflict")

    async def simulate_conflict(self, event: Event) -> List[Event]:
        # Condition check: Only proceed if the event is LawEnforcementEvent and conflict_trigger is true
        if event.__class__.__name__ != "LawEnforcementEvent" or not event.conflict_trigger:
            return []
    
        # Access required variables
        conflict_trigger = event.conflict_trigger
        conflict_details = self.profile.get_data("conflict_details", "")
    
        # Generate decision using LLM
        observation = f"Conflict Trigger: {conflict_trigger}, Conflict Details: {conflict_details}"
        instruction = """Simulate the conflict arising from the law enforcement event. 
        Provide the conflict details and determine the target IDs for resolution. 
        Return the following JSON format:
    
        {
        "conflict_details": "<Details of the simulated conflict>",
        "target_ids": ["ENV"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
        
        conflict_details = result.get('conflict_details', "")
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update conflict status in agent profile
        self.profile.update_data("conflict_status", "simulating")
    
        # Prepare and send ConflictResolutionEvent to each target
        events = []
        for target_id in target_ids:
            conflict_event = ConflictResolutionEvent(self.profile_id, target_id, conflict_details, "", "in_progress")
            events.append(conflict_event)
    
        return events
