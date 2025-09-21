
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


class NeutralMember(GeneralAgent):
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
        # No condition check required as condition is None
    
        # Retrieve required variables
        interaction_type = await self.get_env_data("interaction_type", "dialogue")
        initiator_emotion = self.profile.get_data("initiator_emotion", "neutral")
        receiver_role = "TeamLeader"  # Fixed value based on event description
        ids = await self.env.get_agent_data_by_type("TeamLeader", "id")
    
        # Craft instruction for decision making
        instruction = f"""
        The neutral member is initiating a social interaction with a team leader. 
        Context:
        - Interaction type: {interaction_type}
        - Initiator emotion: {initiator_emotion}
        - Receiver role: {receiver_role}
        - Candidate Target IDs: {ids}
    
        Please analyze the current context and decide the target IDs for the interaction.
        Return the result in the following JSON format:
        {{
            "interaction_status": "<Indicates if the interaction was successful>",
            "initiator_emotion": "<Updated emotional state of the initiator>",
            "target_ids": ["<List of target agent IDs or a single ID>"]
        }}
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction)
    
        # Parse the LLM response
        interaction_status = result.get("interaction_status", "failed")
        updated_emotion = result.get("initiator_emotion", initiator_emotion)
        target_ids = result.get("target_ids", [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state
        self.profile.update_data("interaction_status", interaction_status)
        self.profile.update_data("initiator_emotion", updated_emotion)
    
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            interaction_event = InteractionEvent(
                self.profile_id, target_id, interaction_type, updated_emotion, receiver_role
            )
            events.append(interaction_event)
    
        return events
