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
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "implement_health_policies")
        self.register_event("CommunityResourceEvent", "implement_health_policies")

    async def implement_health_policies(self, event: Event) -> List[Event]:
        # Check if both required events have been received
        start_event_received = self.profile.get_data("start_event_received", False)
        community_resource_event_received = self.profile.get_data("community_resource_event_received", False)

        # Update profile based on the event type
        if event.__class__.__name__ == "StartEvent":
            self.profile.update_data("start_event_received", True)
            start_event_received = True
        elif event.__class__.__name__ == "CommunityResourceEvent":
            self.profile.update_data("community_resource_event_received", True)
            community_resource_event_received = True

        # Proceed only if both events have been received
        if not (start_event_received and community_resource_event_received):
            return []

        # Retrieve necessary data for condition check
        policy_goals = self.profile.get_data("policy_goals", "")
        available_resources = self.profile.get_data("available_resources", 0.0)

        # Implement condition check
        if not (policy_goals and available_resources > 0):
            return []

        # Retrieve required variables from agent context
        policy_details = self.profile.get_data("policy_details", "")
        target_population = self.profile.get_data("target_population", "")
        resource_distribution = self.profile.get_data("resource_distribution", 0.0)

        # Generate reaction using LLM
        instruction = """
        Process the policy details, target population, and resource distribution.
        Determine the target healthcare system agents that should receive the policy implementation event.
        Return the information in the following JSON format:

        {
        "policy_effectiveness": "<Calculated effectiveness of the policy>",
        "target_ids": ["<String ID of the affected healthcare system agents>"]
        }
        """
        observation = f"Policy Details: {policy_details}, Target Population: {target_population}, Resource Distribution: {resource_distribution}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM response
        policy_effectiveness = result.get('policy_effectiveness', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Validate policy_effectiveness and target_ids
        if not policy_effectiveness:
            logger.error("Policy effectiveness is empty or null.")
            return []

        if not target_ids or not all(target_ids):
            logger.error("Target IDs are empty or invalid.")
            return []

        # Update the environment with policy effectiveness
        self.env.update_data("policy_effectiveness", policy_effectiveness)

        # Prepare and send the PolicyImplementationEvent to each target
        events = []
        for target_id in target_ids:
            policy_id = self.profile.get_data("policy_id", -1)
            affected_region = self.profile.get_data("affected_region", "unknown")
            resource_allocation_change = self.profile.get_data("resource_allocation_change", 0.0)
            policy_event = PolicyImplementationEvent(
                self.profile_id,
                target_id,
                policy_id=policy_id,
                affected_region=affected_region,
                resource_allocation_change=resource_allocation_change
            )
            events.append(policy_event)

        return events