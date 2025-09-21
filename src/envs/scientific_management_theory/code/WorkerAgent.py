from typing import Any, List, Optional
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

class WorkerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("TasksAllocatedEvent", "execute_tasks")
        self.register_event("FeedbackAndIncentivesProvidedEvent", "adjust_performance")

    async def execute_tasks(self, event: TasksAllocatedEvent) -> List[Event]:
        # Extract necessary data from the event
        task_list = event.task_list
        worker_ids = event.worker_ids

        # Check if the required fields are present in the event
        if not task_list or self.profile_id not in worker_ids:
            return []

        # Create an observation string for the current context
        observation = f"Received tasks: {task_list} for worker: {self.profile_id}"

        # Craft the instruction for the LLM
        instruction = """Execute the tasks assigned by the manager according to the standardized workflow.
        Please ensure that the tasks are completed efficiently and return the task completion status.
        Provide the response in the following JSON format:
        {
            "task_completion_status": "<Status indicating the completion of tasks>",
            "target_ids": ["<The string ID of the Manager agent>"]
        }
        """

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        task_completion_status = result.get('task_completion_status', None)
        target_ids = result.get('target_ids', None)
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the task completion status
        self.profile.update_data("task_completion_status", task_completion_status)

        # Prepare and send the TasksExecutedEvent to the ManagerAgent
        events = []
        for target_id in target_ids:
            tasks_executed_event = TasksExecutedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                task_results=task_list,
                worker_ids=[self.profile_id]
            )
            events.append(tasks_executed_event)

        return events

    async def adjust_performance(self, event: FeedbackAndIncentivesProvidedEvent) -> List[Event]:
        # Extract required variables from the event
        feedback = event.feedback
        incentives = event.incentives
        worker_ids = event.worker_ids

        # Check if the required fields are present in the event
        if not feedback or not incentives or self.profile_id not in worker_ids:
            return []

        # Create an observation string for the current context
        observation = f"Feedback: {feedback}, Incentives: {incentives}, Worker ID: {self.profile_id}"

        # Craft the instruction for the LLM
        instruction = f"""
        You are tasked with adjusting your performance based on the feedback and incentives provided.
        Please analyze the feedback: '{feedback}' and incentives: {incentives}.
        Generate a performance adjustment strategy and specify which ManagerAgent(s) (target_ids) should be sent the PerformanceAdjustedEvent.
        Return the information in the following JSON format:

        {{
        "adjustments": "<Details of performance adjustments>",
        "target_ids": ["<The string ID(s) of ManagerAgent(s) who should receive the PerformanceAdjustedEvent>"]
        }}
        Note that the target_ids should only include the ManagerAgent(s).
        """
    
        # Generate reaction using the instruction
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's response
        adjustments = result.get('adjustments', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the agent's state with performance adjustment details
        self.profile.update_data("performance_adjustment_status", "Adjusted based on feedback and incentives")
    
        # Prepare and send the PerformanceAdjustedEvent to the ManagerAgent
        events = []
        for target_id in target_ids:
            performance_adjusted_event = PerformanceAdjustedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                adjustments=adjustments,
                worker_ids=[self.profile_id]
            )
            events.append(performance_adjusted_event)
    
        return events