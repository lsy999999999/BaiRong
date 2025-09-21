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

class ExperiencedEmployee(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_interaction")

    async def initiate_interaction(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "StartEvent":
            return []

        interaction_type = await self.get_env_data("interaction_type", "dialogue")
        initiator_emotion = self.profile.get_data("initiator_emotion", "neutral")
        receiver_role = "TeamLeader"
        ids = await self.env.get_agent_data_by_type("TeamLeader", "id")

        instruction = f"""
        The experienced employee is initiating a social interaction with a team leader. 
        The interaction type is '{interaction_type}', and the initiator's emotional state is '{initiator_emotion}'. 
        Candidate target IDs: {ids}
        Please determine the target(s) for this interaction and return the information in the following JSON format:

        {{
            "interaction_type": "<Type of interaction, e.g., dialogue or task>",
            "updated_emotion": "<New emotional state of the initiator after the interaction>",
            "target_ids": ["<The string ID of the target agent(s)>"]
        }}
        """
        result = await self.generate_reaction(instruction)

        interaction_type = result.get('interaction_type', interaction_type)
        updated_emotion = result.get('updated_emotion', initiator_emotion)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("interaction_status", "success")
        self.profile.update_data("initiator_emotion", updated_emotion)

        events = []
        for target_id in target_ids:
            interaction_event = InteractionEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                interaction_type=interaction_type,
                initiator_emotion=updated_emotion,
                receiver_role=receiver_role
            )
            events.append(interaction_event)

        return events
