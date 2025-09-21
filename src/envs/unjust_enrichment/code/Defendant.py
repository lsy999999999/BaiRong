
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


class Defendant(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "prepare_defense")

    async def prepare_defense(self, event: Event) -> List[Event]:
        # No condition to check, proceed directly with the handler logic
    
        # Retrieve required variables
        defense_arguments = self.profile.get_data("defense_arguments", "")
        defendant_id = self.profile.get_data("defendant_id", "")
        case_id = await self.get_env_data("case_id", "")
    
        # Prepare instruction for LLM
        instruction = """
        You are preparing a defense for the Defendant in a legal case of unjust enrichment.
        Ensure that the defense arguments are comprehensive and address the Plaintiff's claims effectively.
        Return the information in the following JSON format:
    
        {
            "defense_arguments": "<Prepared defense arguments>",
            "target_ids": ["<The string ID(s) of the Judge agent(s)>"]
        }
        """
    
        # Generate reaction using LLM
        observation = f"Defense Arguments: {defense_arguments}, Defendant ID: {defendant_id}, Case ID: {case_id}"
        result = await self.generate_reaction(instruction, observation)
    
        # Extract and validate LLM's response
        defense_arguments = result.get('defense_arguments', defense_arguments)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state
        self.profile.update_data("defense_prepared", True)
    
        # Prepare and send DefensePreparedEvent to the Judge
        events = []
        for target_id in target_ids:
            defense_event = DefensePreparedEvent(
                self.profile_id, target_id,
                defense_arguments=defense_arguments,
                defendant_id=defendant_id,
                case_id=case_id
            )
            events.append(defense_event)
    
        return events
