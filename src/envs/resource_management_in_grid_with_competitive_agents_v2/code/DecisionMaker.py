
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


class DecisionMaker(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "process_request")

    async def process_request(self, event: Event) -> List[Event]:
        # No condition check needed
        # Generate response_data and status
        response_data = "Processed response data"
        status = "processed"
        # Call generate_reaction to get target_ids
        instruction = """Please select the target_ids as the Communicator agent's ID (target_id=2). 
        The response_data and status are already generated as "Processed response data" and "processed" respectively."""
        result = await self.generate_reaction(instruction)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        # Create and send the RequestProcessedEvent
        events = []
        for target_id in target_ids:
            event = RequestProcessedEvent(self.profile_id, target_id, response_data, status)
            events.append(event)
        return events
