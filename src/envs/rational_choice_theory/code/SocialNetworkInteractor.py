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

class SocialNetworkInteractor(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("DecisionMadeEvent", "observe_and_adjust")

    async def observe_and_adjust(self, event: Event) -> List[Event]:
        # Check if the event is an instance of DecisionMadeEvent
        if not isinstance(event, DecisionMadeEvent):
            return []  # Return empty list if condition not met

        # Extracting event data
        decision = event.decision
        influencing_factors = event.influencing_factors
    
        # Observation and instruction for LLM
        observation = f"Decision: {decision}, Influencing Factors: {influencing_factors}"
        instruction = """
        Based on the observed decision and influencing factors, determine the necessary adjustment in strategy for the agent.
        Please return the information in the following JSON format:
    
        {
        "adjustment_status": "<Status of the adjustment>",
        "target_ids": ["<The string ID of the EnvAgent, use 'ENV' for terminal events>"],
        "results_summary": {"<Key results and observations after adjustment>"}
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Extracting results from LLM response
        adjustment_status = result.get('adjustment_status', 'no_adjustment')
        target_ids = result.get('target_ids', None)
        results_summary = result.get('results_summary', {})
    
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state
        self.profile.update_data("adjustment_status", adjustment_status)
    
        # Prepare and send AdjustmentObservedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            adjustment_event = AdjustmentObservedEvent(self.profile_id, target_id, adjustment_status, results_summary)
            events.append(adjustment_event)
    
        return events