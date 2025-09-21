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
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "establish_norms")
        self.register_event("HealthThreatEvaluatedEvent", "establish_norms")
        self.register_event("PolicyImplementedEvent", "establish_norms")

    async def establish_norms(self, event: Event) -> List[Event]:
        # Check if all required events have been received
        required_events = {"HealthThreatEvaluatedEvent", "PolicyImplementedEvent"}
        event_received = event.__class__.__name__
        self.profile.update_data(f"{event_received}_received", True)

        # Check if all events have been received
        all_events_received = all(self.profile.get_data(f"{e}_received", False) for e in required_events)
        if not all_events_received:
            return []

        # Access necessary data from agent profile and event
        community_health_data = self.profile.get_data("community_health_data", {})
        threat_level = getattr(event, "threat_level", 0.0)
        susceptibility = getattr(event, "susceptibility", 0.0)
        severity = getattr(event, "severity", 0.0)
        government_policy = getattr(event, "policy_name", "unknown")

        # Prepare observation and instruction for LLM
        observation = f"Community health data: {community_health_data}, Threat level: {threat_level}, Susceptibility: {susceptibility}, Severity: {severity}, Government policy: {government_policy}"
        instruction = """Based on the community health data, threat level, susceptibility, severity, and the government policy, 
        generate a list of community norms that support health behaviors. 
        Please return the information in the following JSON format:

        {
        "community_norms": ["<List of norms established by the community>"],
        "target_ids": ["<List of IDs of IndividualAgents that should be notified>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Update agent's state with new community norms
        community_norms = result.get("community_norms", [])
        self.profile.update_data("community_norms", community_norms)

        # Prepare outgoing events
        target_ids = result.get("target_ids", [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            norm_description = ", ".join(community_norms)
            norms_event = NormsEstablishedEvent(self.profile_id, target_id, norm_description=norm_description, acceptance_level=1.0)
            events.append(norms_event)

        return events