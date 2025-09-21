
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
        self.register_event("StartEvent", "submit_evidence")

    async def submit_evidence(self, event: Event) -> List[Event]:
        # No condition to check as condition is None
    
        # Retrieve data from agent profile
        evidence_details = self.profile.get_data("evidence_details", "")
        plaintiff_id = self.profile.get_data("plaintiff_id", "")
        case_id = await self.get_env_data("case_id", "")
    
        # Update agent profile to indicate evidence has been submitted
        self.profile.update_data("evidence_submitted", True)
    
        # Prepare instruction for generate_reaction
        instruction = """
        The Plaintiff is submitting evidence of unjust enrichment. 
        Please determine the target_ids, which can be a single ID or a list of IDs, to which this evidence should be sent.
        The response should be in JSON format:
        {
            "target_ids": ["<The string ID(s) of the Judge agent>"]
        }
        """
    
        # Generate reaction to determine target_ids
        result = await self.generate_reaction(instruction)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Create and send EvidenceSubmittedEvent to each target_id
        events = []
        for target_id in target_ids:
            evidence_event = EvidenceSubmittedEvent(
                self.profile_id,
                target_id,
                evidence_details=evidence_details,
                plaintiff_id=plaintiff_id,
                case_id=case_id
            )
            events.append(evidence_event)
    
        return events
