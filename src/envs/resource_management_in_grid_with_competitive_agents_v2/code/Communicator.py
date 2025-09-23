
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


class Communicator(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("RequestProcessedEvent", "send_response")

    async def send_response(self, event: Event) -> List[Event]:
        # Condition check: no condition required
        observation = f"Request processed with response data: {event.response_data} and status: {event.status}"
        instruction = """Please generate a reaction for the 'send_response' action. 
        The action requires sending the response data and status to the environment. 
        The target agent is 'ENV' (EnvAgent). 
        Please return the following JSON format:
        {
            "target_ids": ["ENV"]
        }
        """
        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        events = []
        for target_id in target_ids:
            # Create ResponseSentEvent with status and response_data from the event
            response_sent_event = ResponseSentEvent(self.profile_id, target_id, event.status, event.response_data)
            events.append(response_sent_event)
        
        # Update environment data
        self.env.update_data("status", event.status)
        self.env.update_data("response_data", event.response_data)
        
        return events
