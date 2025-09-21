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


class EnvironmentAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InformationGatheredEvent", "simulate_external_factors")

    async def simulate_external_factors(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "InformationGatheredEvent":
            return []

        # Extract necessary information from InformationGatheredEvent
        information_content = event.information_content

        instruction = f"""Simulate external factors impacting decision-making based on the gathered information.
        The factors should be derived from the information content. Please provide the simulated factors details and return the information in the following JSON format:

        {{
            "simulated_factors": {{
                "factor_type": "<Derived Factor Type>",
                "impact_level": "<Derived Impact Level>"
            }},
            "target_ids": ["<The string ID of the Decision Maker agent>"]
        }}
        """

        observation = f"Information content: {information_content}"
        result = await self.generate_reaction(instruction, observation)

        simulated_factors = result.get('simulated_factors', {})
        factor_type = simulated_factors.get('factor_type', "")
        impact_level = simulated_factors.get('impact_level', "0")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            external_factors_event = ExternalFactorsSimulatedEvent(self.profile_id, target_id, factor_type, impact_level)
            events.append(external_factors_event)

        return events