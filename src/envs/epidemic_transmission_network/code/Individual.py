from typing import Any, List, Optional
import json
import asyncio
from loguru import logger
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.relationship import RelationshipManager
from onesim.events import *
from .events import *

class Individual(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InterventionDeployedEvent", "perceive_risk")
        self.register_event("StartEvent", "perceive_risk")
        self.register_event("RiskPerceptionUpdatedEvent", "adjust_behavior")

    async def perceive_risk(self, event: Event) -> List[Event]:
        # No specific condition for perceive_risk action, always proceed
        information_sources = self.profile.get_data("information_sources", [])
        personal_experiences = self.profile.get_data("personal_experiences", {})
    
        instruction = f"""
        The individual with ID {self.profile_id} is assessing their risk of infection based on personal experiences and external information sources.
        Please update their risk perception value based on the provided information_sources and personal_experiences.
        Please return the updated risk perception value and the target_ids in the following JSON format:
    
        {{
        "risk_perception": "<Updated risk perception value>",
        "target_ids": ["<The string ID of the individual>"]
        }}
        """
        result = await self.generate_reaction(instruction, observation=None)
        
        risk_perception = result.get('risk_perception', None)
        target_ids = result.get('target_ids', [self.profile_id])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        self.profile.update_data("risk_perception", risk_perception)
    
        events = []
        for target_id in target_ids:
            risk_perception_event = RiskPerceptionUpdatedEvent(self.profile_id, target_id, risk_perception=risk_perception, information_sources=information_sources)
            events.append(risk_perception_event)
    
        return events

    async def adjust_behavior(self, event: Event) -> List[Event]:
        if not isinstance(event, RiskPerceptionUpdatedEvent):
            return []
        
        risk_perception = event.risk_perception
        individual_id = event.individual_id
        information_sources = event.information_sources
        
        instruction = f"""
        An individual with ID {individual_id} has updated their risk perception to {risk_perception} based on the information sources: {information_sources}.
        Adjust their behavior accordingly and provide a list of behavior changes.
        Return the behavior changes in the following JSON format:
    
        {{
            "target_ids": ["<The string ID of the affected entities>"],
            "behavior_changes": ["<List of behavior changes made by the individual>"]
        }}
        """
        
        result = await self.generate_reaction(instruction)
        target_ids = result.get('target_ids', [])
        behavior_changes = result.get('behavior_changes', [])
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        events = []
        for target_id in target_ids:
            if target_id == "ENV":
                continue
            event_data = {
                "individual_id": individual_id,
                "healthcare_facility_id": self.profile.get_data("healthcare_facility_id", 0),
                "household_id": self.profile.get_data("household_id", 0),
                "behavior_changes": behavior_changes
            }
            if target_id.startswith("HH"):
                events.append(BehaviorAdjustedEvent(self.profile_id, target_id, **event_data))
            elif target_id.startswith("HF"):
                events.append(BehaviorAdjustedEvent(self.profile_id, target_id, **event_data))
            else:
                events.append(BehaviorAdjustedEvent(self.profile_id, target_id, **event_data))
        
        return events