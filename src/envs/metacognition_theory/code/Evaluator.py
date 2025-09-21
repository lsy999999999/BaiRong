
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


class Evaluator(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StrategyAdjustmentEvent", "analyze_performance")

    async def analyze_performance(self, event: Event) -> List[Event]:
        # No condition to check, proceed directly to handling the event
    
        # Access the required variables from the event
        strategy_changes = event.strategy_changes
        adjustment_reason = event.adjustment_reason
    
        # Prepare the instruction for the LLM
        instruction = """Analyze the strategy changes and adjustment reasons provided. 
        Generate a performance summary and specify the completion status. 
        Return the information in the following JSON format:
    
        {
        "performance_summary": "<Summary of the performance analysis>",
        "completion_status": "<Status of the task completion>",
        "target_ids": ["ENV"]
        }
        """
    
        observation = f"Strategy changes: {strategy_changes}, Adjustment reason: {adjustment_reason}"
        
        # Generate the reaction using the LLM
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM's JSON response
        performance_summary = result.get('performance_summary', 'N/A')
        completion_status = result.get('completion_status', 'completed')
        target_ids = result.get('target_ids', 'ENV')
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state with the performance summary and completion status
        self.profile.update_data("performance_summary", performance_summary)
        self.profile.update_data("completion_status", completion_status)
    
        # Prepare and send the PerformanceAnalysisEvent to the EnvAgent
        events = []
        for target_id in target_ids:
            performance_event = PerformanceAnalysisEvent(self.profile_id, target_id, performance_summary, completion_status)
            events.append(performance_event)
        
        return events
