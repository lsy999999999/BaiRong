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

class Group(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("CooperationDecisionEvent", "evaluate_collective_action_success")

    async def evaluate_collective_action_success(self, event: Event) -> List[Event]:
        # Check if all individual cooperation decisions have been received
        expected_individuals = await self.get_env_data("expected_individuals", 1)  # Ensure a valid default
        received_decisions = self.profile.get_data("received_decisions", [])

        # Add the decision if it's not already recorded
        individual_id = event.individual_id
        cooperation_willingness = event.cooperation_willingness

        if individual_id not in received_decisions:
            received_decisions.append(individual_id)
            self.profile.update_data("received_decisions", received_decisions)

        # Aggregate cooperation willingness
        total_cooperation = self.profile.get_data("total_cooperation", 0.0)
        total_cooperation += cooperation_willingness
        self.profile.update_data("total_cooperation", total_cooperation)

        # Check if all decisions are received
        if len(received_decisions) < expected_individuals:
            return []  # Not all decisions received yet

        # Once all decisions are received, evaluate collective action success
        group_goal = await self.get_env_data("group_goal", 0.0)

        instruction = """Evaluate the success of the collective action based on the aggregated cooperation level.
        Determine if the collective action was successful, calculate the total cooperation, and the group benefit.
        Return the information in the following JSON format:

        {
        "collective_success": <bool indicating success>,
        "total_cooperation": <aggregated cooperation level>,
        "group_benefit": <calculated group benefit>,
        "target_ids": ["ENV"]
        }
        """

        observation = f"Total cooperation: {total_cooperation}, Group goal: {group_goal}"
        result = await self.generate_reaction(instruction, observation)

        collective_success = result.get('collective_success', False)
        total_cooperation = result.get('total_cooperation', 0.0)
        group_benefit = result.get('group_benefit', 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update environment with the results
        self.env.update_data("collective_success", collective_success)
        self.env.update_data("total_cooperation", total_cooperation)
        self.env.update_data("group_benefit", group_benefit)

        # Create and send the CollectiveActionResultEvent to the environment
        events = []
        for target_id in target_ids:
            result_event = CollectiveActionResultEvent(self.profile_id, target_id, collective_success, total_cooperation, group_benefit)
            events.append(result_event)

        return events
