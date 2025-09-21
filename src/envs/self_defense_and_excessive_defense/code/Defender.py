from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class Defender(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("ThreatEvent", "react_to_threat")

    async def react_to_threat(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        threat_level = event.threat_level
        if threat_level <= 0:
            return []  # Condition not met, return empty list
    
        # Extract required variables from the event
        aggressor_id = event.aggressor_id
        defender_id = event.defender_id
    
        # Decision Making using generate_reaction
        instruction = """You are tasked with determining an appropriate defensive action in response to a threat.
        Consider the 'threat_level' and decide on the type and intensity of the defensive action.
        Please return the information in the following JSON format:
        {
          "defensive_action_type": "<Type of defensive action>",
          "defense_intensity": <Intensity of the action>,
          "target_ids": ["<The string ID of the judge agent>"]
        }
        """
        observation = f"Threat Level: {threat_level}, Aggressor ID: {aggressor_id}, Defender ID: {defender_id}"
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's JSON response
        defensive_action_type = result.get('defensive_action_type', 'basic')
        defense_intensity = result.get('defense_intensity', 1)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list) or not target_ids:
            target_ids = []  # Ensure target_ids is a list, may need actual logic to determine judge_id
    
        # Update agent profile with the defensive action details
        self.profile.update_data("defensive_action_type", defensive_action_type)
        self.profile.update_data("defense_intensity", defense_intensity)
        # self.profile.update_data("evidence_collected", event.evidence_collected if event.evidence_collected else [])
    
        # Prepare and send DefenseActionEvent to the Judge
        events = []
        for target_id in target_ids:
            defense_action_event = DefenseActionEvent(
                self.profile_id, target_id,
                defensive_action_type=defensive_action_type,
                defense_intensity=defense_intensity,
                evidence_collected=self.profile.get_data("evidence_collected"),
                defender_id=defender_id,
                judge_id=target_id  # Assuming target_id is judge_id
            )
            events.append(defense_action_event)
    
        return events