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

class EarlyMajority(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("AdoptionEvent", "consider_adoption")

    async def consider_adoption(self, event: Event) -> List[Event]:
        # Check if the event is an 'AdoptionEvent' and retrieve necessary fields
        if event.__class__.__name__ == "AdoptionEvent":
            innovation_id = event.innovation_id
            adoption_rate = event.adoption_rate
            social_pressure = event.social_pressure
            
            # Condition check: Significant acceptance among early adopters
            acceptance_threshold = self.profile.get_data("acceptance_threshold", 0.5)
            # if adoption_rate < acceptance_threshold:
            #     return []
            
            # Generate reaction using LLM
            observation = f"Innovation ID: {innovation_id}, Adoption Rate: {adoption_rate}, Social Pressure: {social_pressure}"
            instruction = """Please determine if the early majority should consider adopting the innovation based on the given adoption rate and social pressure.
            Return the information in the following JSON format:
            
            {
                "consideration_status": <true if considering adoption, false otherwise>,
                "target_ids": ["<The string ID(s) of the LateMajority agent(s)>"]
            }
            """
            
            result = await self.generate_reaction(instruction, observation)
            
            consideration_status = result.get('consideration_status', False)
            target_ids = result.get('target_ids', None)
            
            if not isinstance(target_ids, list):
                target_ids = [target_ids]
            
            # Update the agent's consideration status
            self.profile.update_data("consideration_status", consideration_status)
            
            # Prepare and send the EarlyMajorityAdoptionEvent if consideration_status is true
            events = []
            if consideration_status:
                acceptance_threshold = 0.7  # Example threshold for late majority consideration
                for target_id in target_ids:
                    early_majority_adoption_event = EarlyMajorityAdoptionEvent(
                        self.profile_id, target_id, innovation_id=innovation_id, acceptance_threshold=acceptance_threshold
                    )
                    events.append(early_majority_adoption_event)
            
            return events
        return []