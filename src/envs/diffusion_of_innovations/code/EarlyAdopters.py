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

class EarlyAdopters(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InnovationSpreadEvent", "evaluate_and_adopt_innovation")

    async def evaluate_and_adopt_innovation(self, event: Event) -> List[Event]:
        # Condition check: Innovation has relative advantage and compatibility
        # Use a dynamic threshold based on context or profile data
        dynamic_threshold = self.profile.get_data("relative_advantage_threshold", 0.5)
        if event.relative_advantage <= dynamic_threshold:
            return []

        # Retrieve necessary data from the event
        innovation_id = event.innovation_id
        relative_advantage = event.relative_advantage
        network_connections = event.network_connections

        # Generate reaction for decision making
        observation = f"Innovation ID: {innovation_id}, Relative Advantage: {relative_advantage}, Network Connections: {len(network_connections)}"
        instruction = """
        Evaluate the innovation based on its attributes and decide whether to adopt and further disseminate it.
        The decision should consider the innovation's relative advantage and compatibility.
        Please return the information in the following JSON format:

        {
        "adoption_decision": <true if adopting, false otherwise>,
        "target_ids": ["<The string ID(s) of the EarlyMajority agent(s)>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        adoption_decision = result.get('adoption_decision', False)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state with the adoption decision
        self.profile.update_data("adoption_decision", adoption_decision)

        # If adopted, prepare and send AdoptionEvent to EarlyMajority
        events = []
        if adoption_decision:
            for target_id in target_ids:
                adoption_event = AdoptionEvent(
                    self.profile_id, target_id, innovation_id, adoption_rate=relative_advantage, social_pressure=0.5
                )
                events.append(adoption_event)

        return events