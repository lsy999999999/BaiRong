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

class EmployeeAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("ChangeExecutionEvent", "respond_to_change")

    async def respond_to_change(self, event: Event) -> List[Event]:
        # Retrieve required variables from the event
        manager_id = event.manager_id
        execution_plan = event.execution_plan

        # Prepare observation and instruction for LLM
        observation = f"Manager ID: {manager_id}, Execution plan: {execution_plan}, Employee role: {self.profile.role}"
        instruction = """Please generate feedback and emotional response from the employee regarding the change process.
        The response should include feedback on the change implementation and the emotional impact on the employee.
        Also, provide target_ids of managers to whom this feedback should be sent.
        Return the information in the following JSON format:
        {
            "feedback": "<Feedback on the change process>",
            "emotional_response": "<Emotional response to the change>",
            "target_ids": ["<Manager ID(s) to receive feedback>"]
        }
        Note that "target_ids" should only include ManagerAgent IDs, should not include LeaderAgent IDs.
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract feedback and emotional response
        feedback = result.get('feedback', None)
        emotional_response = result.get('emotional_response', None)
        target_ids = result.get('target_ids', None)
        if not target_ids:
            return []  # Return empty list if no target_ids are provided
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's profile with feedback and emotional response
        self.profile.update_data("feedback", feedback)
        self.profile.update_data("emotional_response", emotional_response)

        # Prepare and send FeedbackEvent to the specified managers
        events = []
        for target_id in target_ids:
            feedback_event = FeedbackEvent(self.profile_id, target_id, self.profile_id, feedback, emotional_response)
            events.append(feedback_event)

        return events