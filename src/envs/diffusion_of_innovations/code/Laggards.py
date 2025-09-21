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

class Laggards(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("LateMajorityAdoptionEvent", "adopt_under_pressure")
        self.predefined_threshold = 0.5  # Define a threshold value for influence factor

    async def adopt_under_pressure(self, event: Event) -> List[Event]:
        # Condition Check
        # if event.influence_factor < self.predefined_threshold:
        #     return []

        # Access required variables from event
        innovation_id = event.innovation_id
        influence_factor = event.influence_factor

        # Update agent profile
        self.profile.update_data("adoption_status", True)

        # Prepare instruction for decision making
        instruction = f"""
        You are tasked with determining the completion status and final adoption rate for the diffusion process.
        The influence factor is {influence_factor}, which indicates the pressure on laggards to adopt the innovation.
        Please return the information in the following JSON format:

        {{
            "completion_status": "<Boolean indicating if the diffusion is complete>",
            "final_adoption_rate": "<Final rate of adoption after laggards adopt>",
            "target_ids": ["ENV"]
        }}
        """

        # Generate reaction based on instruction
        result = await self.generate_reaction(instruction)

        # Extract data from result
        completion_status = result.get('completion_status', False)
        final_adoption_rate = result.get('final_adoption_rate', 0.0)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update environment data
        self.env.update_data("completion_status", completion_status)

        # Prepare and send outgoing event
        events = []
        for target_id in target_ids:
            laggard_adoption_event = LaggardAdoptionEvent(
                self.profile_id,
                target_id,
                innovation_id=innovation_id,
                completion_status=completion_status,
                final_adoption_rate=final_adoption_rate
            )
            events.append(laggard_adoption_event)

        return events