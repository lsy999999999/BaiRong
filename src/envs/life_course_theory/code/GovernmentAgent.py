from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import PolicyImpactEvent, StartEvent

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
        self.register_event("StartEvent", "implement_policy")

    async def implement_policy(self, event: Event) -> List[Event]:
        # Check if the event is 'StartEvent' and proceed if it is
        if not isinstance(event, StartEvent):
            return []

        # Retrieve current socioeconomic conditions and policy requirements
        socioeconomic_conditions = await self.get_env_data("socioeconomic_conditions", "default")
        policy_requirements = await self.get_env_data("policy_requirements", "default")

        # Check condition: Current socioeconomic conditions and policy requirements
        if not (socioeconomic_conditions and policy_requirements):
            return []

        # Retrieve policy details from agent's profile
        policy_details = self.profile.get_data("policy_details", "default")

        # Generate reaction using generate_reaction
        instruction = """
        Please determine the target individual agents affected by the policy implementation.
        Consider the current socioeconomic conditions and the policy details.
        Return the information in the following JSON format:

        {
        "target_ids": ["<A list of target individual agent IDs>"],
        "policy_effect": "<Description of the policy impact on the individual>",
        "impact_level": <Quantitative measure of the policy impact level>
        }
        """
        observation = f"Policy Details: {policy_details}, Socioeconomic Conditions: {socioeconomic_conditions}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        target_ids = result.get('target_ids', [])
        policy_effect = result.get('policy_effect', "")
        impact_level = result.get('impact_level', 0.0)

        if not isinstance(target_ids, list):
            target_ids = [target_ids] if target_ids is not None else []

        # Update agent's profile to indicate the policy has been implemented
        self.profile.update_data("policy_implemented", True)

        # Prepare and send PolicyImpactEvent to each target individual agent
        events = []
        for target_id in target_ids:
            policy_impact_event = PolicyImpactEvent(self.profile_id, target_id, policy_effect=policy_effect, impact_level=impact_level)
            events.append(policy_impact_event)

        return events