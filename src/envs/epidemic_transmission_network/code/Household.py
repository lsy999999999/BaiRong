from typing import Any, List, Optional
import json
import asyncio
from loguru import logger
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.relationship import RelationshipManager
from onesim.events import *
from .events import *


class Household(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("BehaviorAdjustedEvent", "update_quarantine_status")

    async def update_quarantine_status(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "BehaviorAdjustedEvent":
            return []
        
        behavior_changes = event.behavior_changes
        household_id = event.household_id

        instruction = f"""
        The household with ID {household_id} has received a BehaviorAdjustedEvent from one of its members.
        The event contains the following behavior changes: {behavior_changes}.
        Based on these changes, determine if the household's quarantine status should be updated.
        Please return the new quarantine status and the target IDs (which should be the household ID) in the following JSON format:

        {{
            "quarantine_status": "<The new quarantine status of the household>",
            "target_ids": ["<The household ID>"]
        }}
        """
        
        result = await self.generate_reaction(instruction)
        quarantine_status = result.get('quarantine_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        if not target_ids:  # Check if target_ids is empty
            return []
        
        events = []
        for target_id in target_ids:
            if target_id != 'ENV':
                quarantine_event = QuarantineStatusUpdatedEvent(self.profile_id, target_id, household_id=household_id, quarantine_status=quarantine_status)
                events.append(quarantine_event)
        
        return events