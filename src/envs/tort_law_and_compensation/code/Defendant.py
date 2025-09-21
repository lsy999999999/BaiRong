
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
        # Condition check for 'null' condition
        if event.__class__.__name__ != "StartEvent":
            return []
    
        # Access required variables from agent context
        liability_reduction_argument = self.profile.get_data("liability_reduction_argument", "")
        counter_evidence_list = self.profile.get_data("counter_evidence_list", [])
    
        # Instruction for generating defense preparation reaction
        instruction = """Please prepare the defense argument for liability reduction, including counter-evidence.
        Return the information in the following JSON format:
    
        {
        "liability_reduction_argument": "<Argument prepared by the defendant for reducing liability>",
        "counter_evidence_list": <List of evidence countering the plaintiff's claims>,
        "target_ids": "<The string ID of the Judge agent>"
        }
        Note: The target_ids should be a list of Judge IDs.
        """
    
        # Generate the reaction using the LLM
        result = await self.generate_reaction(instruction)
    
        # Process the LLM's response
        liability_reduction_argument = result.get('liability_reduction_argument', liability_reduction_argument)
        counter_evidence_list = result.get('counter_evidence_list', counter_evidence_list)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state indicating defense has been prepared
        self.profile.update_data("defense_prepared", True)
    
        # Prepare and send DefensePreparedEvent to the Judge
        events = []
        for target_id in target_ids:
            defense_event = DefensePreparedEvent(
                self.profile_id, target_id,
                liability_reduction_argument=liability_reduction_argument,
                counter_evidence_list=counter_evidence_list
            )
            events.append(defense_event)
    
        return events
