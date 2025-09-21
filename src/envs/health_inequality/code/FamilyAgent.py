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


class FamilyAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "influence_family_health")
        self.register_event("HealthDecisionEvent", "influence_family_health")

    async def influence_family_health(self, event: Event) -> List[Event]:
        # Condition Check: Ensure family decisions on education, nutrition, and health behaviors
        family_income = self.profile.get_data("family_income", 0.0)
        nutrition_quality = self.profile.get_data("nutrition_quality", "unknown")
        education_investment = self.profile.get_data("education_investment", 0.0)

        # Logical change: Use 'OR' condition for each criterion
        if family_income <= 0 and nutrition_quality == "unknown" and education_investment <= 0:
            return []

        # Prepare observation and instruction for generate_reaction
        observation = f"""Family Income: {family_income}, 
                          Nutrition Quality: {nutrition_quality}, 
                          Education Investment: {education_investment}"""
        instruction = """Please assess the family decisions on education, nutrition, and health behaviors.
        Determine the overall family health status and select the appropriate community agents to send the FamilyHealthImpactEvent.
        Return the information in the following JSON format:
    
        {
        "family_health_status": "<Overall health status of the family>",
        "target_ids": ["<The string ID(s) of the CommunityAgent(s) impacted>"]
        }
        """
    
        # Generate reaction to determine family health status and target_ids
        result = await self.generate_reaction(instruction, observation)
    
        family_health_status = result.get('family_health_status', "unknown")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Validate target_ids for empty or null values
        if not target_ids:
            return []

        # Update the agent's profile with the new family health status
        self.profile.update_data("family_health_status", family_health_status)
    
        # Determine the actual resource change based on family health status
        resource_change = self.calculate_resource_change(family_health_status)
    
        # Prepare and send the FamilyHealthImpactEvent to the selected CommunityAgent(s)
        events = []
        for target_id in target_ids:
            family_health_event = FamilyHealthImpactEvent(
                self.profile_id,
                target_id,
                family_id=self.profile_id,
                impact_type="health_influence",
                resource_change=resource_change
            )
            events.append(family_health_event)
    
        return events

    def calculate_resource_change(self, family_health_status: str) -> float:
        # Logic to calculate resource change based on family health status
        if family_health_status == "excellent":
            return 1.0
        elif family_health_status == "good":
            return 0.5
        elif family_health_status == "poor":
            return -0.5
        else:
            return 0.0