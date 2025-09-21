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

class SocioPoliticalAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "analyze_environmental_influences")

    async def analyze_environmental_influences(self, event: Event) -> List[Event]:
        # No condition specified, proceed with handler logic
        
        # Retrieve socio-political data from the environment
        socio_political_data = await self.get_env_data("socio_political_data", "")
        
        # Craft instruction for LLM to analyze socio-political influences
        instruction = """Analyze the given socio-political data to determine influences on legal judgments.
        Please return the information in the following JSON format:
        
        {
        "socio_political_influences": "<Analyzed socio-political influences>",
        "target_ids": ["<The string ID(s) of the Judge agent(s)>"]
        }
        """
        
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, socio_political_data)
        
        # Extract results from LLM response
        influences = result.get('socio_political_influences', "")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update agent's profile with analyzed influences
        self.profile.update_data("socio_political_influences", influences)
        
        # Prepare and send InfluencesAnalyzedEvent to JudgeAgent(s)
        events = []
        for target_id in target_ids:
            influence_event = InfluencesAnalyzedEvent(self.profile_id, target_id, influences, judgment_id="")
            events.append(influence_event)
        
        return events