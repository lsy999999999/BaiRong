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
        self.register_event("StartEvent", "evaluate_health_threat")
        self.register_event("SupportProvidedEvent", "adopt_health_behavior")
        self.register_event("NormsEstablishedEvent", "adopt_health_behavior")
        self.register_event("PolicyImplementedEvent", "adopt_health_behavior")

    async def evaluate_health_threat(self, event: Event) -> List[Event]:
        personal_health_data = self.profile.get_data("personal_health_data", {})
        environmental_cues = await self.get_env_data("environmental_cues", [])
        
        observation = f"Personal health data: {personal_health_data}, Environmental cues: {environmental_cues}"
        instruction = """
        Assess the perceived threat of a health issue based on personal health data and environmental cues.
        Return the perceived threat level, susceptibility, severity, and target_ids for event recipients.
        Use the following JSON format:
        {
            "perceived_threat_level": <float>,
            "perceived_susceptibility": <float>,
            "perceived_severity": <float>,
            "target_ids": [<list of target CommunityAgent and FamilyAgent IDs>]
        }
        Note: "target_ids" should only include CommunityAgent and/or FamilyAgent IDs.
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        perceived_threat_level = result.get('perceived_threat_level', 0.0)
        perceived_susceptibility = result.get('perceived_susceptibility', 0.0)
        perceived_severity = result.get('perceived_severity', 0.0)
        target_ids = result.get('target_ids', [])
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        self.profile.update_data("perceived_threat_level", perceived_threat_level)
        self.profile.update_data("perceived_susceptibility", perceived_susceptibility)
        self.profile.update_data("perceived_severity", perceived_severity)
        
        events = []
        for target_id in target_ids:
            health_threat_event = HealthThreatEvaluatedEvent(
                self.profile_id,
                target_id,
                threat_level=perceived_threat_level,
                susceptibility=perceived_susceptibility,
                severity=perceived_severity
            )
            events.append(health_threat_event)
        
        received_events = set(self.profile.get_data("received_events", []))
        received_events.add("HealthThreatEvaluatedEvent")
        self.profile.update_data("received_events", list(received_events))
        
        return events

    async def adopt_health_behavior(self, event: Event) -> List[Event]:
        event_classes = {"SupportProvidedEvent", "NormsEstablishedEvent", "PolicyImplementedEvent"}
        received_events = set(self.profile.get_data("received_events", []))
        
        if not event_classes.issubset(received_events):
            return []

        perceived_benefits = self.profile.get_data("perceived_benefits", 0.0)
        perceived_barriers = self.profile.get_data("perceived_barriers", 0.0)
        self_efficacy = self.profile.get_data("self_efficacy", 0.0)
        
        if not (perceived_benefits > perceived_barriers and self_efficacy > 0.5):
            return []
        
        observation = f"Perceived benefits: {perceived_benefits}, Perceived barriers: {perceived_barriers}, Self-efficacy: {self_efficacy}, Received events: {received_events}"
        instruction = """Based on the current health belief model context, decide whether to adopt a health behavior. 
        Consider perceived benefits, barriers, self-efficacy, and received events. 
        Please return the information in the following JSON format:
        {
            "adopted_behavior": "<Type of health behavior adopted>",
            "adoption_success": <True/False>,
            "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        adopted_behavior = result.get('adopted_behavior', "unknown")
        adoption_success = result.get('adoption_success', False)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        self.profile.update_data("adopted_behavior", adopted_behavior)
        self.profile.update_data("adoption_success", adoption_success)
        
        events = []
        for target_id in target_ids:
            behavior_event = HealthBehaviorAdoptedEvent(
                self.profile_id, target_id, adopted_behavior, adoption_success, []
            )
            events.append(behavior_event)
        
        return events