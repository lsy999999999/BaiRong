from typing import Any, List, Optional
import asyncio
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
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "assess_risk")
        self.register_event("PolicyImplementationEvent", "assess_risk")
        self.register_event("SocialContactPatternEvent", "change_health_state")

    async def assess_risk(self, event: Event) -> List[Event]:
        # No condition to check as it's 'null'
        
        # Access required data
        current_health_state = self.profile.get_data("current_health_state", "S")
        # social_contact_pattern = event.social_contact_pattern
        policy_effect = event.policy_effect
        risk_level = self.profile.get_data("risk_level", 0.0)  # Include risk_level in observation
        
        # Prepare observation and instruction for LLM
        observation = f"Health State: {current_health_state}, Policy Effect: {policy_effect}, Risk Level: {risk_level}"
        instruction = """Evaluate the risk of infection based on the current health state and government policies. 
        Determine the risk level and identify target group agents to inform about changes. 
        Please return the information in the following JSON format:
        
        {
        "risk_level": "<Calculated risk level as a float>",
        "target_ids": ["<The string ID(s) of the GroupAgent(s) to inform>"]
        }
        """
        
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        risk_level = result.get('risk_level', 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update agent's risk level
        self.profile.update_data("risk_level", risk_level)
        
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            risk_assessment_event = RiskAssessmentEvent(self.profile_id, target_id, individual_id=self.profile_id, risk_level=risk_level)
            events.append(risk_assessment_event)
        
        return events

    async def change_health_state(self, event: Event) -> List[Event]:
        # Extract necessary data from the event and self.profile
        contact_pattern = event.contact_pattern
        risk_level = event.risk_level
        current_health_state = self.profile.get_data("current_health_state", "S")
    
        # Check if all required events have been received (AND condition)
        if not (contact_pattern and risk_level):
            return []
    
        # Condition check: Contact with infected agent and probability threshold met
        infected_patterns = ["infected", "high_risk", "exposed"]  # Example list of known infected patterns
        if not any(pattern in contact_pattern for pattern in infected_patterns) or risk_level <= 0.5:
            return []
    
        # Update the previous health state
        self.profile.update_data("previous_health_state", current_health_state)
    
        # Decision-making using generate_reaction
        observation = f"Current health state: {current_health_state}, Risk level: {risk_level}"
        instruction = """Determine the new health state based on the current health state and risk level.
        Return the information in the following JSON format:
        {
            "new_health_state": "<The updated health state (S, I, R)>",
            "target_ids": ["<The string ID(s) of the HealthcareSystemAgent(s) if treatment is needed>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        new_health_state = result.get('new_health_state', current_health_state)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the current health state
        self.profile.update_data("current_health_state", new_health_state)
    
        # Prepare outgoing events if the health state change requires treatment
        events = []
        requires_treatment = new_health_state == "I"  # Assuming treatment is needed if infected
        for target_id in target_ids:
            health_state_change_event = HealthStateChangeEvent(
                self.profile_id, target_id,
                individual_id=self.profile_id,
                previous_health_state=current_health_state,
                current_health_state=new_health_state,
                requires_treatment=requires_treatment
            )
            events.append(health_state_change_event)
        
        return events