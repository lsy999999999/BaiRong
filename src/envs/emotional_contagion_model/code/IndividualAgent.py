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

class IndividualAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initialize_emotional_state")
        self.register_event("EmotionalInfluenceEvaluatedEvent", "adjust_emotional_state")

    async def initialize_emotional_state(self, event: Event) -> List[Event]:
        # Retrieve initial emotional state from environment settings
        initial_emotional_state = await self.get_env_data("initial_emotional_state", "neutral")
    
        # Update agent's emotional state based on the initial value
        self.profile.update_data("emotional_state", initial_emotional_state)
        
        # Prepare instruction for generating reaction
        instruction = """
        You are tasked with initializing the emotional state of an agent based on predefined or random values.
        The agent's initial emotional state has been set to: {initial_emotional_state}.
        Please return the information in the following JSON format:
    
        {{
        "target_ids": ["<The string ID(s) of the CommunicationAgent(s) that will be shared with your emotional state>"],
        "emotional_state": "<The emotional state initialized>"
        }}

        Note: The target_ids should only include the IDs of the CommunicationAgent(s), not IndividualAgent(s), not empty list.
        """
        
        # Generate reaction using the instruction and current context
        observation = f"Initial emotional state: {initial_emotional_state}"
        result = await self.generate_reaction(instruction.format(initial_emotional_state=initial_emotional_state), observation)
    
        # Extract target_ids and emotional_state from the result
        target_ids = result.get('target_ids', [])
        emotional_state = result.get('emotional_state', initial_emotional_state)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Create and send EmotionalStateInitializedEvent to each target_id
        events = []
        for target_id in target_ids:
            emotional_event = EmotionalStateInitializedEvent(self.profile_id, target_id, emotional_state)
            events.append(emotional_event)
        
        return events

    async def adjust_emotional_state(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is of type EmotionalInfluenceEvaluatedEvent
        if not isinstance(event, EmotionalInfluenceEvaluatedEvent):
            return []
    
        # Retrieve necessary data from the event
        evaluation_result = event.evaluation_result
        adjustment_factor = event.adjustment_factor
    
        # Access current emotional state from agent's profile
        current_emotional_state = self.profile.get_data("emotional_state", "neutral")
    
        # Decision Making: Generate reaction based on evaluation result
        observation = f"Current emotional state: {current_emotional_state}, Evaluation result: {evaluation_result}, Adjustment factor: {adjustment_factor}"
        instruction = """Based on the evaluation result and adjustment factor, decide the new emotional state. 
        If 'evaluation_result' is 'positive', increase emotional state by 'adjustment_factor'. 
        If 'negative', decrease it. Otherwise, maintain current state. 
        Return the updated emotional state and target_ids in the following JSON format:
        {
            "emotional_state": "<Updated emotional state>",
            "completion_status": "<Status indicating successful adjustment>",
            "target_ids": ["ENV"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's response
        updated_emotional_state = result.get('emotional_state', current_emotional_state)
        completion_status = result.get('completion_status', "success")
        target_ids = result.get('target_ids', "ENV")
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the agent's emotional state in the profile
        self.profile.update_data("emotional_state", updated_emotional_state)
    
        # Prepare and send EmotionalStateAdjustedEvent to the target(s)
        events = []
        for target_id in target_ids:
            adjusted_event = EmotionalStateAdjustedEvent(self.profile_id, target_id, completion_status, updated_emotional_state)
            events.append(adjusted_event)
    
        return events