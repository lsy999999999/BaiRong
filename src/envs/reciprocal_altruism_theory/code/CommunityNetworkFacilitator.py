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

class CommunityNetworkFacilitator(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("CommitToSpreadEvent", "facilitate_behavior_spread")

    async def facilitate_behavior_spread(self, event: Event) -> List[Event]:
        # Since the condition is "null", proceed directly with the handler logic

        # Access event data
        recipient_id = event.recipient_id
        commitment_level = event.commitment_level
        spread_target = event.spread_target

        # Prepare instruction for generate_reaction
        instruction = f"""
        The CommunityNetworkFacilitator is tasked with supporting the recipient's commitment to spreading health behavior.
        Use the recipient_id '{recipient_id}', commitment_level '{commitment_level}', and spread_target '{spread_target}' 
        to determine the appropriate target_ids for facilitating behavior spread. 
        Please return the information in the following JSON format:
    
        {{
        "target_ids": ["ENV"],
        "spread_result": "<Indicate 'success' or 'failure' of the spread>"
        }}
        """

        # Generate reaction based on instruction
        result = await self.generate_reaction(instruction, observation=f"Recipient ID: {recipient_id}, Commitment Level: {commitment_level}, Spread Target: {spread_target}")

        # Parse LLM's JSON response
        target_ids = result.get('target_ids', ["ENV"])
        spread_result = result.get('spread_result', "failure")

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Retrieve environment data
        network_id = await self.get_env_data("network_id", "")

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            completion_status = (spread_result == "success")
            behavior_spread_event = BehaviorSpreadEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                network_id=network_id,
                spread_result=spread_result,
                completion_status=completion_status
            )
            events.append(behavior_spread_event)

        return events