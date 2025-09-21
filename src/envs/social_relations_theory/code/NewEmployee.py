
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


class NewEmployee(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_interaction")

    async def initiate_interaction(self, event: Event) -> List[Event]:
        # Since the condition is 'None', we proceed directly with the handler logic
    
        # Retrieve required variables
        interaction_type = await self.get_env_data("interaction_type", "dialogue")
        initiator_emotion = self.profile.get_data("initiator_emotion", "neutral")
        receiver_role = self.profile_id

        ids = await self.env.get_agent_data_by_type("TeamLeader", "id")
    
        # Prepare instruction for LLM
        instruction = f"""
        You are simulating an interaction where a new employee initiates a social interaction with a team leader to establish rapport and receive feedback.
        Please generate the interaction outcome and specify the target_ids for the team leader(s) involved.
        Candidate target IDs: {ids}.
        Return the information in the following JSON format:
        {{
            "interaction_status": "<Status of the interaction>",
            "initiator_emotion": "<Updated emotional state of the initiator>",
            "target_ids": ["<The string ID(s) of the TeamLeader agent(s)>"]
        }}
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction)
    
        # Parse LLM response
        interaction_status = result.get('interaction_status', None)
        updated_emotion = result.get('initiator_emotion', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent data
        self.profile.update_data("interaction_status", interaction_status)
        self.profile.update_data("initiator_emotion", updated_emotion)
    
        # Create and send InteractionEvent(s)
        events = []
        for target_id in target_ids:
            interaction_event = InteractionEvent(self.profile_id, target_id)
            interaction_event.interaction_type = interaction_type
            interaction_event.initiator_emotion = updated_emotion
            interaction_event.receiver_role = receiver_role
            events.append(interaction_event)
    
        return events
