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

class CaseAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "define_legal_context")
        self.register_event("PrecedentInterpretedEvent", "apply_interpretation")

    async def define_legal_context(self, event: Event) -> List[Event]:
        # No condition check required as the condition is 'null'
    
        # Retrieve the legal context from the environment
        legal_context = await self.get_env_data("legal_context", "")
    
        # Prepare observation and instruction for generate_reaction
        observation = f"Legal context: {legal_context}"
        instruction = """Define the legal context for the case and determine the appropriate target_id(s) for sending the legal context to precedent agents.
        The response should be in the following JSON format:
        {
            "case_context": "<Updated legal context for the case>",
            "target_ids": ["<List of string IDs of PrecedentAgent(s)>"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's response
        case_context = result.get('case_context', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the agent's case context
        self.profile.update_data("case_context", case_context)
    
        # Prepare and send the LegalContextDefinedEvent to PrecedentAgent(s)
        events = []
        for target_id in target_ids:
            legal_context_event = LegalContextDefinedEvent(self.profile_id, target_id, case_context, "")
            events.append(legal_context_event)
    
        return events

    async def apply_interpretation(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if event.__class__.__name__ != "PrecedentInterpretedEvent" or not event.precedent_details:
            return []
    
        # Data Access
        interpreted_precedents = event.precedent_details
        case_context = self.profile.get_data("case_context", "")
    
        # Decision Making
        observation = f"Interpreted precedents: {interpreted_precedents}, Case context: {case_context}"
        instruction = """Please apply the interpreted precedents to the case context and determine the target agent(s) for the next event.
        Return the information in the following JSON format:
        {
        "applied_interpretation": "<Details of how the interpreted precedents are applied to the case context>",
        "target_ids": ["<The string ID(s) of the LegalExpertAgent(s)>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
    
        # Response Processing
        applied_interpretation = result.get('applied_interpretation', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile
        self.profile.update_data("applied_interpretation", applied_interpretation)
    
        # Prepare and send the InterpretationAppliedEvent to LegalExpertAgent(s)
        events = []
        for target_id in target_ids:
            interpretation_event = InterpretationAppliedEvent(self.profile_id, target_id, applied_interpretation, "")
            events.append(interpretation_event)
    
        return events