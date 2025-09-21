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

class PrecedentAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("LegalContextDefinedEvent", "store_legal_principles")

    async def store_legal_principles(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ != "LegalContextDefinedEvent":
            return []

        # Data Access and Validation
        legal_context = event.legal_context
        if not legal_context or not isinstance(legal_context, str):
            return []

        # Decision Making
        instruction = """Store the legal principles derived from the event's legal context for future reference.
        Please return the information in the following JSON format:

        {
        "stored_principles": "<Legal principles derived from the legal context>",
        "target_ids": ["<The string ID(s) of the JudgeAgent(s) to notify>"]
        }
        """
        observation = f"Legal context: {legal_context}"
        result = await self.generate_reaction(instruction, observation)

        # Response Processing
        stored_principles = result.get('stored_principles', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Data Modification
        if stored_principles:
            self.profile.update_data("stored_principles", stored_principles)

        # Prepare and send the PrinciplesStoredEvent to JudgeAgents
        events = []
        for target_id in target_ids:
            if target_id:
                judge_request_id = f"request_{target_id}"
                principles_stored_event = PrinciplesStoredEvent(self.profile_id, target_id, stored_principles, judge_request_id)
                events.append(principles_stored_event)

        return events