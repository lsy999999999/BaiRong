
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


class PublicAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InformationModifiedEvent", "receive_information")

    async def receive_information(self, event: Event) -> List[Event]:
        # Check if the event is of the correct type
        if event.__class__.__name__ != "InformationModifiedEvent":
            return []
    
        # Retrieve necessary fields from the event
        modified_information = event.modified_information
        opinion_leader_id = event.opinion_leader_id
        target_public_agents = event.target_public_agents
    
        # Generate instruction for LLM
        instruction = f"""PublicAgent has received modified information from OpinionLeaderAgent.
        Please generate a reaction based on the received 'modified_information' and 'opinion_leader_id'.
        Include the following in your JSON response:
        {{
            "public_agent_reaction": "<The reaction or response of the public agent>",
            "received_information": "{modified_information}",
            "completion_status": "completed",
            "target_ids": ["ENV"]
        }}
        """
    
        # Generate reaction using LLM
        observation = f"modified_information: {modified_information}, opinion_leader_id: {opinion_leader_id}, target_public_agents: {target_public_agents}"
        result = await self.generate_reaction(instruction, observation)
    
        # Parse LLM response
        public_agent_reaction = result.get('public_agent_reaction', None)
        received_information = result.get('received_information', None)
        completion_status = result.get('completion_status', None)
        target_ids = result.get('target_ids', ["ENV"])
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile with received information and reaction
        self.profile.update_data("received_information", received_information)
        self.profile.update_data("public_agent_reaction", public_agent_reaction)
        self.profile.update_data("completion_status", completion_status)
    
        # Prepare and send InformationReceivedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            information_received_event = InformationReceivedEvent(
                self.profile_id, target_id, received_information, public_agent_reaction, completion_status)
            events.append(information_received_event)
    
        return events
