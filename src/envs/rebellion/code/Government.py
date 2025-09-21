from typing import Any, List, Optional
import json
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class Government(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "assess_rebellion")
        self.register_event("RebellionDecisionEvent", "implement_repression")
        self.register_event("RebellionAssessedEvent", "implement_repression")

    async def assess_rebellion(self, event: Event) -> List[Event]:
        # Retrieve required environmental data
        public_discontent = await self.get_env_data("public_discontent", 0.0)
        reported_incidents = await self.get_env_data("reported_incidents", 0)

        # Prepare observation and instruction for the LLM
        observation = f"Public discontent: {public_discontent}, Reported incidents: {reported_incidents}"
        instruction = """
        Calculate the rebellion level based on public discontent and reported incidents.
        Please return the information in the following JSON format:
        
        {
        "rebellion_level": <Calculated rebellion level as a float>,
        "target_ids": ["<The string ID of the Government agent(s) to receive the RebellionAssessedEvent>"]
        }
        """

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract results from the LLM's response
        rebellion_level = result.get('rebellion_level', 0.0)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the RebellionAssessedEvent to the specified target_ids
        events = []
        for target_id in target_ids:
            rebellion_assessed_event = RebellionAssessedEvent(
                self.profile_id,
                target_id,
                rebellion_level=rebellion_level,
                government_id=self.profile_id
            )
            events.append(rebellion_assessed_event)

        return events

    async def implement_repression(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ not in ["RebellionAssessedEvent", "RebellionDecisionEvent"]:
            return []

        # Retrieve required variables
        rebellion_level = getattr(event, 'rebellion_level', self.profile.get_data("rebellion_level", 0.0))
        available_resources = await self.get_env_data("available_resources", 0.0)

        # Generate decision using LLM
        observation = f"Rebellion Level: {rebellion_level}, Available Resources: {available_resources}"
        instruction = """Decide on a repression strategy to manage rebellion based on the rebellion level and available resources. 
        Please return the information in the following JSON format:
    
        {
        "repression_strategy": "<The strategy implemented by the government>",
        "effectiveness": <The effectiveness of the strategy as a float>,
        "target_ids": ["ENV"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)

        # Parse response
        repression_strategy = result.get('repression_strategy', "none")
        effectiveness = result.get('effectiveness', 0.0)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent state
        self.profile.update_data("repression_strategy", repression_strategy)
        self.profile.update_data("effectiveness", effectiveness)

        # Create and send events
        events = []
        for target_id in target_ids:
            repression_event = RepressionImplementedEvent(self.profile_id, target_id, repression_strategy, effectiveness, self.profile_id)
            events.append(repression_event)

        return events