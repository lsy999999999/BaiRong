from typing import Any, List
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

class LateMajority(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("EarlyMajorityAdoptionEvent", "evaluate_broad_acceptance")

    async def evaluate_broad_acceptance(self, event: Event) -> List[Event]:
        # Check if the event is of type EarlyMajorityAdoptionEvent
        if not isinstance(event, EarlyMajorityAdoptionEvent):
            return []
    
        # Retrieve necessary event data
        innovation_id = event.innovation_id
        acceptance_threshold = event.acceptance_threshold
    
        # Access agent profile data to evaluate broad acceptance
        current_acceptance = self.profile.get_data("current_acceptance", 0.0)
        social_pressure = self.profile.get_data("social_pressure", 0.0)
    
        # Condition check: Broad acceptance and social pressure
        # if current_acceptance < acceptance_threshold or social_pressure <= 0.0:
        #     return []
    
        # Instruction for the LLM to evaluate broad acceptance and decide on adoption
        instruction = """
        Evaluate the broad acceptance of the innovation. 
        Determine if broad acceptance is met and decide on adoption based on acceptance thresholds.
        Return the evaluation result and target_ids for subsequent actions in the following JSON format:
    
        {
        "broad_acceptance_evaluation": "<True if broad acceptance is met, otherwise False>",
        "target_ids": ["<The string ID(s) of the Laggards agent(s)>"]
        }
        """
        observation = f"Innovation ID: {innovation_id}, Current Acceptance: {current_acceptance}, Acceptance Threshold: {acceptance_threshold}, Social Pressure: {social_pressure}"
    
        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the result
        broad_acceptance_evaluation = result.get('broad_acceptance_evaluation', False)
        target_ids = result.get('target_ids', [])
    
        # Update agent profile with the evaluation result
        self.profile.update_data("broad_acceptance_evaluation", broad_acceptance_evaluation)
    
        # If target_ids is not a list, convert it to a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            late_majority_event = LateMajorityAdoptionEvent(self.profile_id, target_id, innovation_id)
            events.append(late_majority_event)
    
        return events