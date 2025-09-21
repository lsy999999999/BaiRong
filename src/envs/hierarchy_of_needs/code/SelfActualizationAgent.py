from typing import Any, List, Optional
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

class SelfActualizationAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "identify_self_actualization_goals")

    async def identify_self_actualization_goals(self, event: Event) -> List[Event]:
        # Since there is no condition, proceed directly with the handler logic

        # Construct the observation context
        observation = f"Current state of agent: {self.profile.get_data('current_state')}"

        # Construct the instruction for generate_reaction
        instruction = """
        Identify self-actualization goals based on the agent's current state and aspirations. 
        Please return the information in the following JSON format:
        {
            "self_actualization_goals": ["<List of goals identified for the agent's self-actualization>"],
            "self_actualization_status": "<Updated status of the agent's progress towards self-actualization>",
            "target_ids": ["<The string ID(s) of the FeedbackAgent(s) to notify>"]
        }
        Note: The target_ids should be the IDs of the FeedbackAgent(s) to notify.
        """

        # Generate the reaction using the instruction and observation
        result = await self.generate_reaction(instruction, observation)

        # Extract the results from the LLM's response
        self_actualization_goals = result.get('self_actualization_goals', [])
        self_actualization_status = result.get('self_actualization_status', '')
        target_ids = result.get('target_ids', None)

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with new goals and status
        self.profile.update_data("self_actualization_goals", self_actualization_goals)
        self.profile.update_data("self_actualization_status", self_actualization_status)

        # Prepare and send the SelfActualizationAchievedEvent to each target
        events = []
        for target_id in target_ids:
            self_actualization_event = SelfActualizationAchievedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                agent_id=self.profile_id,
                goals_achieved=self_actualization_goals,
                satisfaction_level=1.0  # Assume full satisfaction for demonstration
            )
            events.append(self_actualization_event)

        return events