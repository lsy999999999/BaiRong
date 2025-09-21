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

class BehaviorChangeRecipient(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("BehaviorChangeInitiatedEvent", "receive_and_commit_to_change")

    async def receive_and_commit_to_change(self, event: Event) -> List[Event]:
        # Access required event data
        advocate_id = event.advocate_id
        recipient_id = event.recipient_id
        behavior_type = event.behavior_type
        intensity = event.intensity

        # Create observation string
        observation = f"Advocate ID: {advocate_id}, Recipient ID: {recipient_id}, Behavior Type: {behavior_type}, Intensity: {intensity}"

        # Generate instruction for the LLM
        instruction = """The BehaviorChangeRecipient receives the health behavior change and commits to spreading it further, thereby contributing to the chain of reciprocal altruism. 
        Please provide the commitment level and spread target. Return the information in the following JSON format:
        
        {
        "commitment_level": "<integer representing the level of commitment>",
        "spread_target": "<string representing the target group or entity>",
        "target_ids": ["<The string ID(s) of the target CommunityNetworkFacilitator agent(s) for behavior spread>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract response data
        commitment_level = result.get('commitment_level', 1)
        spread_target = result.get('spread_target', "community")
        target_ids = result.get('target_ids', [])

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state
        self.profile.update_data("commitment_level", commitment_level)
        self.profile.update_data("spread_target", spread_target)

        # Prepare and send the CommitToSpreadEvent to the CommunityNetworkFacilitator
        events = []
        for target_id in target_ids:
            commit_event = CommitToSpreadEvent(self.profile_id, target_id, recipient_id=recipient_id, commitment_level=commitment_level, spread_target=spread_target)
            events.append(commit_event)

        return events