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


class CommunityAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "provide_community_resources")
        self.register_event("FamilyHealthImpactEvent", "provide_community_resources")

    async def provide_community_resources(self, event: Event) -> List[Event]:
        # Condition Check: Availability of social capital, public resources, and medical facilities
        social_capital = self.profile.get_data("social_capital", None)
        public_resources = self.profile.get_data("public_resources", None)
        medical_facilities = self.profile.get_data("medical_facilities", None)
        
        if social_capital is None or public_resources is None or medical_facilities is None:
            return []  # Condition not met
    
        # Event Tracking Strategy: Ensure all required events are received
        if isinstance(event, StartEvent):
            self.profile.update_data("start_event_received", True)
        elif isinstance(event, FamilyHealthImpactEvent):
            self.profile.update_data("family_health_event_received", True)
            self.profile.update_data("family_id", event.family_id)
            self.profile.update_data("impact_type", event.impact_type)
            self.profile.update_data("resource_change", event.resource_change)
    
        start_event_received = self.profile.get_data("start_event_received", False)
        family_health_event_received = self.profile.get_data("family_health_event_received", False)
    
        if not (start_event_received and family_health_event_received):
            return []  # Not all required events received
    
        # Decision Making: Use generate_reaction for decisions
        observation = f"Social Capital: {social_capital}, Public Resources: {public_resources}, Medical Facilities: {medical_facilities}, Family Impact: {self.profile.get_data('impact_type', 'unknown')}"
        instruction = """
        Based on the available social capital, public resources, and medical facilities, along with the family health impact,
        calculate the community health level and decide the target_ids for sending CommunityResourceEvent.
        Return the following JSON format:
        {
            "community_health_level": "<calculated health level>",
            "resource_needs": "<updated resource needs based on context>",
            "urgency_level": "<updated urgency level based on context>",
            "target_ids": ["<ID(s) of GovernmentAgent(s)>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
    
        community_health_level = result.get('community_health_level', "default")
        resource_needs = result.get('resource_needs', "none")
        urgency_level = result.get('urgency_level', 0)
        target_ids = result.get('target_ids', None)
        
        if not isinstance(target_ids, list) or not target_ids:
            return []  # Return empty list if target_ids are invalid
    
        # Update community health level
        self.profile.update_data("community_health_level", community_health_level)
        self.profile.update_data("resource_needs", resource_needs)
        self.profile.update_data("urgency_level", urgency_level)
    
        # Prepare and send CommunityResourceEvent
        events = []
        for target_id in target_ids:
            community_id = self.profile.get_data("community_id", -1)
            community_resource_event = CommunityResourceEvent(self.profile_id, target_id, community_id, resource_needs, urgency_level)
            events.append(community_resource_event)
    
        return events