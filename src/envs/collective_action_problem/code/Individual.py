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


class Individual(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "calculate_cooperation_willingness")

    async def calculate_cooperation_willingness(self, event: Event) -> List[Event]:
        # No condition to check, proceed directly with the handler logic

        # Retrieve personal_cost and personal_benefit from agent's profile
        personal_cost = self.profile.get_data("personal_cost", 0.0)
        personal_benefit = self.profile.get_data("personal_benefit", 0.0)

        group_agent_ids = await self.env.get_agent_data_by_type('Group', 'id')

        # Craft instruction for generating cooperation willingness
        instruction = """
        Calculate the cooperation willingness based on a cost-benefit analysis. Send your decision to some of the Group Agents.
        Please return the information in the following JSON format:

        {
        "cooperation_willingness": "<Calculated willingness to cooperate>",
        "target_ids": ["<The string ID(s) of the Group agent(s)>"]
        }
        """

        # Observation context
        observation = f"Personal cost: {personal_cost}, Personal benefit: {personal_benefit}, Candidate IDs of Group Agents: {group_agent_ids}"

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract cooperation willingness and target_ids from the result
        cooperation_willingness = result.get('cooperation_willingness', 0.0)
        target_ids = result.get('target_ids', [])

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state with the calculated cooperation_willingness
        self.profile.update_data("cooperation_willingness", cooperation_willingness)

        # Prepare and send CooperationDecisionEvent to each target_id
        events = []
        for target_id in target_ids:
            cooperation_event = CooperationDecisionEvent(
                self.profile_id, target_id,
                individual_id=self.profile_id,
                cooperation_willingness=cooperation_willingness,
                personal_cost=personal_cost,
                personal_benefit=personal_benefit
            )
            events.append(cooperation_event)

        return events
