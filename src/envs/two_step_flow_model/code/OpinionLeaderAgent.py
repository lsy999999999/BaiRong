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


class OpinionLeaderAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InformationGeneratedEvent", "filter_and_modify_information")

    async def filter_and_modify_information(self, event: Event) -> List[Event]:
        # Extract required data from the event
        information_content = event.information_content
        target_opinion_leaders = event.target_opinion_leaders

        # Check if the current agent is a target opinion leader
        if self.profile_id not in target_opinion_leaders:
            return []  # Return empty list if not a target

        # Instruction to generate modified information and target public agents
        instruction = """
        Please filter and modify the received information based on personal beliefs.
        Return the modified information and choose appropriate public agents to receive it.
        Use the following JSON format:

        {
            "modified_information": "<The modified version of the information>",
            "target_public_agents": ["<List of string IDs representing the public agents>"]
        }
        """

        # Generate reaction using the instruction and observation
        result = await self.generate_reaction(instruction, information_content)

        # Extract modified information and target public agents from the result
        modified_information = result.get('modified_information', "")
        target_public_agents = result.get('target_public_agents', [])

        # Ensure target_public_agents is a list
        if not isinstance(target_public_agents, list):
            target_public_agents = [target_public_agents]
        self.profile.update_data("target_public_agents", target_public_agents)
        self.profile.update_data("modified_information", modified_information)

        # Prepare and send InformationModifiedEvent to each target public agent
        events = []
        for target_id in target_public_agents:
            modified_event = InformationModifiedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                original_information=information_content,
                modified_information=modified_information,
                opinion_leader_id=self.profile_id,
                target_public_agents=target_public_agents
            )
            events.append(modified_event)

        return events