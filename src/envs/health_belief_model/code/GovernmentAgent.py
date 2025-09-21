
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


class GovernmentAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "implement_policy")

    async def implement_policy(self, event: Event) -> List[Event]:
        # No condition to check as the condition is None
    
        # Retrieve required variables
        policy_goals = self.profile.get_data("policy_goals", "default")
        resource_availability = await self.get_env_data("resource_availability", 0.0)
    
        # Instruction for LLM to generate implemented_policy and policy_impact
        instruction = """You are a GovernmentAgent implementing a health policy. 
        Use the provided policy goals and resource availability to determine the policy to implement and its expected impact.
        Please return the information in the following JSON format:
    
        {
            "implemented_policy": "<Details of the policy implemented>",
            "policy_impact": <Expected impact level of the policy on health behaviors>,
            "target_ids": ["<The string ID(s) of the target Individual agents>"]
        }
        Note: "target_ids" should only include IndividualAgent id(s).
        """
        observation = f"Policy Goals: {policy_goals}, Resource Availability: {resource_availability}"
        
        result = await self.generate_reaction(instruction, observation)
        
        implemented_policy = result.get('implemented_policy', None)
        policy_impact = result.get('policy_impact', 0.0)
        target_ids = result.get('target_ids', None)
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile with implemented_policy and policy_impact
        self.profile.update_data("implemented_policy", implemented_policy)
        self.profile.update_data("policy_impact", policy_impact)
    
        # Create and send PolicyImplementedEvent to each target
        events = []
        for target_id in target_ids:
            policy_event = PolicyImplementedEvent(self.profile_id, target_id, policy_name=implemented_policy, impact_level=policy_impact)
            events.append(policy_event)
    
        return events
