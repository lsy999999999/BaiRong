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

class GovernmentAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "implement_policy")

    async def implement_policy(self, event: Event) -> List[Event]:
        # There is no specific condition to check for implement_policy, proceed directly

        # # Extract necessary fields from the event
        # policy_id = event.policy_id
        # policy_effect = event.policy_effect

        # Update the agent's profile with the policy status
        self.profile.update_data("policy_status", "Policy Implemented")

        # Prepare the instruction for the LLM
        instruction = f"""
        Determine the appropriate target IDs to receive the policy implementation impact. 
        The target IDs can be individual agents or group agents based on the policy effect.
        Please return the information in the following JSON format:

        {{
            "policy_status": "Policy Implemented",
            "individual_target_ids": ["<List of individual target agent IDs (string)>"],
            "group_target_ids": ["<List of group target agent IDs (string)>"]
        }}
        """

        # Generate a reaction using the LLM
        # observation = f"Policy ID: {policy_id}, Policy Effect: {policy_effect}"
        result = await self.generate_reaction(instruction)

        # Extract the target IDs from the result
        individual_target_ids = result.get('individual_target_ids', [])
        group_target_ids = result.get('group_target_ids', [])
        if not isinstance(individual_target_ids, list):
            individual_target_ids = [individual_target_ids]
        if not isinstance(group_target_ids, list):
            group_target_ids = [group_target_ids]

        # Create events to send to the target agents
        events = []
        for individual_target_id in individual_target_ids:
            event = PolicyImplementationEvent(self.profile_id, individual_target_id)
            events.append(event)
        for group_target_id in group_target_ids:
            event = PolicyImpactEvent(self.profile_id, group_target_id, impact_level=1.0)  # Example impact level
            events.append(event)

        return events