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

class Monitor(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("TaskExecutionEvent", "observe_task")
        self.register_event("ReflectionEvent", "provide_feedback")

    async def observe_task(self, event: Event) -> List[Event]:
        task_id = event.task_id
        
        instruction = """
        You are observing the TaskExecutor's performance on a task. Your goal is to collect observation data that can be used for feedback and reflection.
        Please return the information in the following JSON format:
        
        {
        "observation_data": "<Data collected during the task observation>",
        "target_ids": ["<The string ID(s) of the TaskExecutor(s) to receive the feedback>"]
        }
        """
        
        observation = f"Observing task with ID: {task_id}"
        result = await self.generate_reaction(instruction, observation)
        
        observation_data = result.get('observation_data', "N/A")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        self.profile.update_data("observation_data", observation_data)
        
        events = []
        for target_id in target_ids:
            observation_event = ObservationEvent(self.profile_id, target_id, observation_data)
            events.append(observation_event)
        
        return events

    async def provide_feedback(self, event: Event) -> List[Event]:
        reflection_summary = event.reflection_summary
        feedback_requested = event.feedback_requested
        
        if not reflection_summary or not feedback_requested:
            return []

        candidate_ids = await self.env.get_agent_data_by_type("TaskExecutor", "id")
        observation = f"Reflection summary: {reflection_summary}, Feedback requested: {feedback_requested}, Candidate IDs of TaskExecutor agent: {candidate_ids}"
        instruction = """Please generate feedback content based on the reflection summary and indicate recommendations for strategy adjustments.
        Return the information in the following JSON format:
    
        {
        "feedback_details": "<Details of the feedback>",
        "recommendations": "<Recommendations for strategy adjustments>",
        "target_ids": ["<The string ID(s) of the TaskExecutor agent>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        feedback_details = result.get('feedback_details', "N/A")
        recommendations = result.get('recommendations', "N/A")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        self.profile.update_data("feedback_details", feedback_details)
        self.profile.update_data("recommendations", recommendations)
    
        events = []
        for target_id in target_ids:
            feedback_event = FeedbackEvent(self.profile_id, target_id, feedback_details, recommendations)
            events.append(feedback_event)
    
        return events