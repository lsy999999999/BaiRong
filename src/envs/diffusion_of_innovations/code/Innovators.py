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

class Innovators(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_innovation_spread")

    async def initiate_innovation_spread(self, event: Event) -> List[Event]:
        # Check if the action condition is met
        if not event.__class__.__name__ == "StartEvent":
            return []

        # Retrieve required environment data
        innovation_id = await self.get_env_data("innovation_id", "")
        network_connections = await self.get_env_data("network_connections", [])
        relative_advantage = await self.get_env_data("relative_advantage", 0.0)

        # Check if network_connections is empty
        if not network_connections:
            logger.warning("No network connections available for innovation spread.")
            return []

        # Update agent data to indicate innovation spread initiation
        self.profile.update_data("spread_status", True)

        # Generate reaction to decide target_ids for spreading innovation
        instruction = """Initiate the spread of innovation by selecting target agents from the social network connections. 
        The innovation has the following attributes: 
        Innovation ID: {innovation_id}, Relative Advantage: {relative_advantage}. 
        Please return the information in the following JSON format:

        {{
        "target_ids": ["<The string ID of the EarlyAdopter agent(s)>"]
        }}
        """
        observation = f"Network Connections: {network_connections}"
        result = await self.generate_reaction(instruction.format(innovation_id=innovation_id, relative_advantage=relative_advantage), observation)

        # Extract target_ids from the LLM's response
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the InnovationSpreadEvent to EarlyAdopters
        events = []
        for target_id in target_ids:
            innovation_event = InnovationSpreadEvent(self.profile_id, target_id, innovation_id, network_connections, relative_advantage)
            events.append(innovation_event)

        return events