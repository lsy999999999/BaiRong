
from typing import Any, List,Optional
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


class Plaintiff(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "submit_compensation_request")

    async def submit_compensation_request(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ != "StartEvent":
            return []
        
        # Data Access
        compensation_amount = self.profile.get_data("compensation_amount", 0.0)
        damage_description = self.profile.get_data("damage_description", "")
        evidence_list = self.profile.get_data("evidence_list", [])
        
        # Decision Making
        instruction = """Context: The Plaintiff is submitting a compensation request in a tort law case. 
        The request includes the compensation amount, damage description, and supporting evidence. 
        The Plaintiff needs to determine the target Judge(s) for evaluating the request.
        Please return the information in the following JSON format:
        {
        "compensation_amount": "<Requested amount for compensation>",
        "damage_description": "<Description of the damages incurred>",
        "evidence_list": <List of evidence supporting the compensation request>,
        "target_ids": ["<The string ID(s) of the Judge agent(s)>"]
        }
        Note: The target_ids should be a list of Judge IDs.
        """
        
        observation = f"Compensation Amount: {compensation_amount}, Damage Description: {damage_description}, Evidence List: {evidence_list}"
        result = await self.generate_reaction(instruction, observation)
        
        # Response Processing
        compensation_amount = result.get('compensation_amount', compensation_amount)
        damage_description = result.get('damage_description', damage_description)
        evidence_list = result.get('evidence_list', evidence_list)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Prepare and send the CompensationRequestEvent to the Judge(s)
        events = []
        for target_id in target_ids:
            compensation_event = CompensationRequestEvent(self.profile_id, target_id, compensation_amount, damage_description, evidence_list)
            events.append(compensation_event)
        
        # Update agent profile
        self.profile.update_data("compensation_request_submitted", True)
        
        return events
