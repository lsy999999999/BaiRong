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

class LegalExpertAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InterpretationAppliedEvent", "analyze_outcomes")

    async def analyze_outcomes(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if not hasattr(event, 'interpretation_details') or not event.interpretation_details:
            return []

        # Data Access
        interpretation_details = event.interpretation_details

        # Decision Making
        observation = f"Interpretation details received: {interpretation_details}"
        instruction = """Analyze the outcomes of the provided legal interpretation details. 
        The analysis should consider the impact on legal precedents and socio-political influences.
        Return the information in the following JSON format:
        
        {
        "outcome_analysis": "<Detailed analysis of the interpretation outcomes>",
        "target_ids": ["<The string ID(s) of the agent(s) to send the results to>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        # Response Processing
        outcome_analysis = result.get('outcome_analysis', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Data Modification
        self.profile.update_data("outcome_analysis", outcome_analysis)

        # Prepare and send the OutcomesAnalyzedEvent to the specified targets
        events = []
        for target_id in target_ids:
            outcomes_event = OutcomesAnalyzedEvent(self.profile_id, target_id, outcome_analysis, "terminated")
            events.append(outcomes_event)

        return events