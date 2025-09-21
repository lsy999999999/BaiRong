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

class InterestGroup(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "influence_media")

    async def influence_media(self, event: Event) -> List[Event]:
        # No condition to check as per the specification
        # Retrieve necessary agent data
        influence_strategy = self.profile.get_data("influence_strategy", "default_strategy")
        connections = self.profile.get_data("connections", [])

        media_ids = await self.env.get_agent_data_by_type("Media", "id")

        # Generate reaction using the LLM
        instruction = """
        You are an interest group aiming to influence media agendas using your strategy and connections. 
        Please decide on the media outlets to target based on your influence strategy and current connections. 
        Return the information in the following JSON format:

        {
        "target_ids": ["<List of Media IDs you aim to influence>"]
        }
        """

        observation = f"Influence Strategy: {influence_strategy}, Connections: {connections}, Candidate Media IDs: {media_ids}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the result
        target_ids = result.get('target_ids', [])
        if target_ids is None:
            target_ids = []
        elif not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and send MediaInfluencedEvent to each target
        events = []
        for target_id in target_ids:
            media_influenced_event = MediaInfluencedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                influence_strategy=influence_strategy,
                target_media_outlets=target_ids
            )
            events.append(media_influenced_event)

        return events