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
        self.register_event("StartEvent", "make_health_decision")

    async def make_health_decision(self, event: Event) -> List[Event]:
        # Condition Check
        income_level = self.profile.get_data("income_level", 0.0)
        education_level = self.profile.get_data("education_level", "")
        social_support = self.profile.get_data("social_support", "")
        
        if income_level <= 0 and not education_level and not social_support:
            return []
    
        # Decision Making
        instruction = """
        You are tasked with making health decisions based on socioeconomic status, education, and social support. 
        Consider the individual's income level, education attainment, and available social support networks. 
        Determine the health decision outcome and identify target_ids for sending events. 
        Return the information in the following JSON format:
    
        {
        "health_decision": "<The decision made regarding the individual's health>",
        "target_ids": ["<The ID(s) of the target agent(s)>"]
        }
        """
        observation = f"Income Level: {income_level}, Education Level: {education_level}, Social Support: {social_support}"
        
        result = await self.generate_reaction(instruction, observation)
        
        health_decision = result.get('health_decision', None)
        target_ids = result.get('target_ids', None)
        if not target_ids:
            return []
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent data
        self.profile.update_data("health_decision", health_decision)
    
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            if target_id.startswith("FamilyAgent"):
                event_to_family = HealthDecisionEvent(self.profile_id, target_id, individual_id=self.profile_id,
                                                      service_requested=health_decision, priority_level=income_level)
                events.append(event_to_family)
            elif target_id.startswith("HealthcareSystemAgent"):
                event_to_healthcare = HealthDecisionEvent(self.profile_id, target_id, individual_id=self.profile_id,
                                                          service_requested=health_decision, priority_level=income_level)
                events.append(event_to_healthcare)
    
        return events