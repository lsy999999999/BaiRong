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

class PhysiologicalAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "assess_physiological_needs")

    async def assess_physiological_needs(self, event: Event) -> List[Event]:
        # Validate event type
        if event.__class__.__name__ != "StartEvent":
            return []

        # Generate reaction to assess physiological needs
        instruction = """
        Please assess the physiological needs of the agent and determine the necessary resources required. 
        Return the information in the following JSON format:
        {
            "physiological_needs_status": "<Status of physiological needs>",
            "resources_required": ["<List of resources required>"],
            "target_ids": ["<The string ID(s) of the FeedbackAgent(s) to notify>"]
        }
        Note: The target_ids should be the IDs of the FeedbackAgent(s) to notify.
        """
        observation = "Initial trigger for physiological needs assessment."
        result = await self.generate_reaction(instruction, observation)

        # Extract results from the LLM response
        physiological_needs_status = result.get('physiological_needs_status', 'Unknown')
        resources_required = result.get('resources_required', [])
        target_ids = result.get('target_ids', [])

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's profile with the LLM's assessment results
        self.profile.update_data("physiological_needs_status", physiological_needs_status)
        self.profile.update_data("resources_required", resources_required)

        # Prepare and send PhysiologicalNeedsMetEvent to each target
        events = []
        for target_id in target_ids:
            physiological_event = PhysiologicalNeedsMetEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                agent_id=self.profile_id,
                resources_provided=resources_required,
                satisfaction_level=1.0  # Assuming full satisfaction for simplicity
            )
            events.append(physiological_event)

        return events