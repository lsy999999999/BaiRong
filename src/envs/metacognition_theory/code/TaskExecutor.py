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

class TaskExecutor(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_task")
        self.register_event("ObservationEvent", "reflect_on_process")
        self.register_event("FeedbackEvent", "adjust_strategy")

    async def initiate_task(self, event: Event) -> List[Event]:
        # No condition specified, proceed directly

        # Retrieve required variables from the environment
        task_id = await self.get_env_data("task_id", "")
        task_details = await self.get_env_data("task_details", "N/A")

        # Update agent data for task status
        self.profile.update_data("task_status", "in_progress")

        # Generate reaction to determine target_ids for the outgoing event
        instruction = """The TaskExecutor has initiated a task with the following details:
        - Task ID: {task_id}
        - Task Details: {task_details}

        Please identify the target agent IDs for monitoring the task execution.
        Return the information in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the Monitor agent>"]
        }
        """
        observation = f"Task ID: {task_id}, Task Details: {task_details}"
        result = await self.generate_reaction(instruction, observation)

        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the TaskExecutionEvent to the Monitor
        events = []
        for target_id in target_ids:
            task_execution_event = TaskExecutionEvent(self.profile_id, target_id, task_id=task_id, task_details=task_details)
            events.append(task_execution_event)

        return events

    async def reflect_on_process(self, event: Event) -> List[Event]:
        # No condition specified, proceed directly

        # Access the observation_data from the event
        candidate_ids = await self.env.get_agent_data_by_type("Monitor", "id")
        observation_data = event.observation_data + f"\nCandidate IDs of Monitor Agent: {candidate_ids}"

        # Generate the instruction for reflection
        instruction = """The TaskExecutor needs to reflect on its cognitive processes during task execution.
        Analyze the given observation data to identify cognitive strengths and weaknesses.
        Please return the information in the following JSON format:

        {
        "reflection_summary": "<Summary of the reflection on cognitive processes>",
        "target_ids": ["<The string ID(s) of the Monitor agent>"]
        }
        """
        
        # Generate the reflection using LLM
        result = await self.generate_reaction(instruction, observation_data)

        # Extract reflection summary and target_ids
        reflection_summary = result.get('reflection_summary', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update reflection_summary in the agent profile
        self.profile.update_data("reflection_summary", reflection_summary)

        # Prepare and send the ReflectionEvent to the Monitor
        events = []
        for target_id in target_ids:
            reflection_event = ReflectionEvent(self.profile_id, target_id, reflection_summary, feedback_requested=True)
            events.append(reflection_event)

        return events

    async def adjust_strategy(self, event: Event) -> List[Event]:
        # Check if the event has necessary attributes
        if not hasattr(event, 'feedback_details') or not hasattr(event, 'recommendations'):
            return []

        # Retrieve feedback details and recommendations from the event
        feedback_details = event.feedback_details
        recommendations = event.recommendations
        candidate_ids = await self.env.get_agent_data_by_type("Evaluator", "id")

        # Prepare the observation and instruction for the LLM
        observation = f"Feedback details: {feedback_details}, Recommendations: {recommendations}, Candidate IDs of Evaluator agent(s): {candidate_ids}"
        instruction = """Based on the feedback and recommendations provided, adjust the TaskExecutor's strategy.
        Please return the information in the following JSON format:
        
        {
        "strategy_changes": "<Description of the adjustments made to the strategy>",
        "adjustment_reason": "<Reason for the strategy adjustment based on feedback>",
        "target_ids": ["<The string ID(s) of the Evaluator agent(s)>"]
        }
        """

        # Generate the reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract strategy changes and adjustment reason from the result
        strategy_changes = result.get('strategy_changes', None)
        adjustment_reason = result.get('adjustment_reason', None)
        target_ids = result.get('target_ids', None)

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with strategy changes and adjustment reason
        self.profile.update_data("strategy_changes", strategy_changes)
        self.profile.update_data("adjustment_reason", adjustment_reason)

        # Prepare and send the StrategyAdjustmentEvent to each Evaluator
        events = []
        for target_id in target_ids:
            strategy_adjustment_event = StrategyAdjustmentEvent(self.profile_id, target_id, strategy_changes, adjustment_reason)
            events.append(strategy_adjustment_event)

        return events