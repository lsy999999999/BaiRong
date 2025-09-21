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

class ParticipantB(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "display_behavior")

    async def display_behavior(self, event: Event) -> List[Event]:
        # Since there is no condition, proceed directly with the handler logic

        # Access necessary data from the agent's profile
        behavior_type = self.profile.get_data("behavior_type", "default")
        intended_outcome = self.profile.get_data("intended_outcome", "default")

        # Prepare the instruction for generating a reaction
        instruction = """
        Participant B is displaying a behavior intended for observation by Participant A.
        Please generate the type of behavior and the intended outcome in the following JSON format:

        {
        "behavior_type": "<Type of behavior displayed>",
        "intended_outcome": "<Intended outcome of the behavior>",
        "target_ids": ["<The string ID of Participant A>"]
        }
        """

        # Generate the reaction using the instruction
        observation = f"Behavior type: {behavior_type}, Intended outcome: {intended_outcome}"
        result = await self.generate_reaction(instruction, observation)

        # Extract behavior_type, intended_outcome, and target_ids from the result
        behavior_type = result.get('behavior_type', behavior_type)
        intended_outcome = result.get('intended_outcome', intended_outcome)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's profile with new behavior information
        self.profile.update_data("behavior_type", behavior_type)
        self.profile.update_data("intended_outcome", intended_outcome)

        # Prepare and send the BehaviorDisplayedEvent to Participant A
        events = []
        for target_id in target_ids:
            behavior_event = BehaviorDisplayedEvent(self.profile_id, target_id, behavior_type, intended_outcome)
            events.append(behavior_event)

        return events