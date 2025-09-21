
from typing import Any, List,Optional
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


class EnvironmentalAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("BehavioralIntentionCalculatedEvent", "assess_environmental_constraints")

    async def assess_environmental_constraints(self, event: Event) -> List[Event]:
        # Check if the event is of the required type
        if event.__class__.__name__ != "BehavioralIntentionCalculatedEvent":
            return []
    
        # Retrieve necessary environmental and agent data
        resource_availability = await self.get_env_data("resource_availability", 1.0)
        situational_factors = await self.get_env_data("situational_factors", {})
        candidate_ids = await self.env.get_agent_data_by_type("CognitiveAgent", "id")
        
        # Prepare the observation and instruction for generate_reaction
        observation = f"Resource availability: {resource_availability}, Situational factors: {situational_factors}, Candidate IDs of Target Agents: {candidate_ids}"
        instruction = """
        Assess the environmental constraints based on the provided resource availability and situational factors. 
        Determine the impact of these constraints on the intended behavior and provide updated values. 
        Additionally, decide on the target_ids for sending the ConstraintsAssessedEvent. 
        Please return the information in the following JSON format:
    
        {
        "resource_availability": "<Updated float value>",
        "situational_constraints": "<Updated dict value>",
        "target_ids": ["<List of target agent IDs>"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the result
        updated_resource_availability = result.get('resource_availability', resource_availability)
        situational_constraints = result.get('situational_constraints', situational_factors)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state with new data
        self.profile.update_data("resource_availability", updated_resource_availability)
        self.profile.update_data("situational_constraints", situational_constraints)
    
        # Prepare and send ConstraintsAssessedEvent to each target
        events = []
        for target_id in target_ids:
            constraints_event = ConstraintsAssessedEvent(
                self.profile_id, target_id, 
                updated_resource_availability, situational_constraints
            )
            events.append(constraints_event)
    
        return events
