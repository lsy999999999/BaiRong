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


class FeedbackerC(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StrategyDecidedEvent", "evaluate_outcome")

    async def evaluate_outcome(self, event: Event) -> List[Event]:
        # Condition check for StrategyDecidedEvent received from Actor A
        if not isinstance(event, StrategyDecidedEvent):
            return []

        # Extract required variables from the event
        strategy_type = event.strategy_type
        expected_outcome = event.expected_outcome

        # Construct observation and instruction for LLM decision making
        observation = f"Strategy Type: {strategy_type}, Expected Outcome: {expected_outcome}"
        instruction = """Evaluate the effectiveness of Actor A's chosen strategy in reducing cognitive dissonance. 
Provide an evaluation result and completion status. 
Decide the target_ids for sending the EvaluationCompletedEvent. 
Return the information in the following JSON format:

{
"evaluation_result": "<The result of the evaluation>",
"completion_status": "<The status of the evaluation process>",
"target_ids": ["ENV"]
}
"""

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        evaluation_result = result.get('evaluation_result', None)
        completion_status = result.get('completion_status', None)
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent state with evaluation result and completion status
        self.profile.update_data("evaluation_result", evaluation_result)
        self.profile.update_data("completion_status", completion_status)

        # Prepare and send EvaluationCompletedEvent to target agent(s)
        events = []
        for target_id in target_ids:
            evaluation_event = EvaluationCompletedEvent(self.profile_id, target_id, evaluation_result, completion_status)
            events.append(evaluation_event)

        return events