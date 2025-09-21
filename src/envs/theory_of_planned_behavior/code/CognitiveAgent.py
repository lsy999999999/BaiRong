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

class CognitiveAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initialize_intentions")
        self.register_event("SocialNormsEvaluatedEvent", "calculate_behavioral_intentions")
        self.register_event("SubjectiveNormsAdjustedEvent", "calculate_behavioral_intentions")
        self.register_event("ConstraintsAssessedEvent", "finalize_behavior")

    async def initialize_intentions(self, event: Event) -> List[Event]:
        # Retrieve required variables from agent profile
        attitude = self.profile.get_data("attitude", 0.0)
        subjective_norm = self.profile.get_data("subjective_norm", 0.0)
        perceived_behavioral_control = self.profile.get_data("perceived_behavioral_control", 0.0)
    
        # Calculate behavioral intentions using TPB components
        behavioral_intentions = attitude + subjective_norm + perceived_behavioral_control
        self.profile.update_data("behavioral_intentions", behavioral_intentions)
    
        # Define instruction for LLM to determine target_ids for outgoing events
        instruction = """
        The CognitiveAgent has initialized its behavioral intentions based on the Theory of Planned Behavior components.
        Please determine the appropriate target_ids for sending the IntentionInitializedEvent.
        Ensure the response is in the following JSON format:
    
        {
        "target_ids": ["<The string ID(s) of the SocialNormAgent(s)>"]
        }
        """
    
        # Generate reaction to determine target_ids for outgoing event
        observation = f"Behavioral Intentions: {behavioral_intentions}"
        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', None)
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare and send IntentionInitializedEvent to each target_id
        events = []
        for target_id in target_ids:
            intention_initialized_event = IntentionInitializedEvent(self.profile_id, target_id)
            events.append(intention_initialized_event)
    
        return events

    async def calculate_behavioral_intentions(self, event: Event) -> List[Event]:
        # Check if the event contains required data
        if event.__class__.__name__ == "SocialNormsEvaluatedEvent":
            social_norms_score = event.social_norms_score
            self.profile.update_data("social_norms_score", social_norms_score)
        elif event.__class__.__name__ == "SubjectiveNormsAdjustedEvent":
            adjusted_subjective_norms = event.adjusted_subjective_norms
            self.profile.update_data("adjusted_subjective_norms", adjusted_subjective_norms)
        
        # Ensure both required data are available in profile
        social_norms_score = self.profile.get_data("social_norms_score", 0.0)
        adjusted_subjective_norms = self.profile.get_data("adjusted_subjective_norms", {})
        candidate_ids = await self.env.get_agent_data_by_type("EnvironmentalAgent", "id")
        
        # Generate reaction using LLM
        observation = f"Social Norms Score: {social_norms_score}, Adjusted Subjective Norms: {adjusted_subjective_norms}, Candidate Target Agent IDs: {candidate_ids}"
        instruction = """Calculate the behavioral intentions using the Theory of Planned Behavior components.
        Return the results in the following JSON format:
        {
            "behavioral_intentions": <calculated_float_value>,
            "target_ids": ["<target_agent_id(s)>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)

        
        # Parse the LLM's JSON response
        behavioral_intentions = result.get('behavioral_intentions', 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update agent's profile with the new behavioral intentions
        self.profile.update_data("behavioral_intentions", behavioral_intentions)
        
        # Prepare the event to send the calculated intentions
        events = []
        for target_id in target_ids:
            tpb_components = {
                "attitude": self.profile.get_data("attitude", 0.0),
                "subjective_norm": social_norms_score,
                "perceived_behavioral_control": self.profile.get_data("perceived_behavioral_control", 0.0)
            }
            intention_event = BehavioralIntentionCalculatedEvent(
                self.profile_id, target_id, behavioral_intentions, tpb_components
            )
            events.append(intention_event)
        
        return events


    async def finalize_behavior(self, event: Event) -> List[Event]:
        # Check if the condition "Requires ConstraintsAssessedEvent" is met
        if event.__class__.__name__ != "ConstraintsAssessedEvent":
            return []
        
        # Retrieve required variables from the event
        resource_availability = event.resource_availability
        situational_constraints = event.situational_constraints
    
        # Ensure all required event data is present
        if resource_availability is None or situational_constraints is None:
            return []
    
        # Update agent's profile with the received data
        self.profile.update_data("resource_availability", resource_availability)
        self.profile.update_data("situational_constraints", situational_constraints)
    
        # Create observation context
        observation = f"Resource availability: {resource_availability}, Situational constraints: {situational_constraints}"
    
        # Craft instruction for generating the reaction
        instruction = """Please finalize the behavior based on the calculated intentions and the provided environmental constraints.
        Ensure to return the finalized behavior and completion status in the following JSON format:
        {
            "final_behavior": "<The finalized behavior outcome>",
            "completion_status": "<Status indicating completion of the behavior determination process>",
            "target_ids": ["ENV"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Extract results from the LLM response
        final_behavior = result.get('final_behavior', "undetermined")
        completion_status = result.get('completion_status', "pending")
        target_ids = result.get('target_ids', [])
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile with the results
        self.profile.update_data("final_behavior", final_behavior)
        self.profile.update_data("completion_status", completion_status)
    
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            behavior_finalized_event = BehaviorFinalizedEvent(self.profile_id, target_id, final_behavior, completion_status)
            events.append(behavior_finalized_event)
    
        return events