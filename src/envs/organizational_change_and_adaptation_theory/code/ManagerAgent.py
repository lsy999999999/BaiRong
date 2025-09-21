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


class ManagerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("ChangeInitiatedEvent", "execute_change_plan")
        self.register_event("FeedbackEvent", "adjust_change_strategy")

    async def execute_change_plan(self, event: Event) -> List[Event]:
        # Check for the receipt of ChangeInitiatedEvent
        if not isinstance(event, ChangeInitiatedEvent):
            return []

        # Access required event data
        change_type = event.change_type
        change_goals = event.change_goals
        leader_id = event.leader_id

        # Derive execution plan directly from event data
        execution_plan = f"Executing {change_type} change with goals: {change_goals} (initiated by Leader ID: {leader_id})"

        # Generate instruction for LLM
        instruction = """
        The manager is executing the change plan. Coordinate resources and ensure the plan is followed.
        Please return the information in the following JSON format:
        {
            "execution_status": "<Status of the change plan execution>",
            "target_ids": ["<The string ID of the Employee agent(s)>"]
        }
        """

        observation = f"Change Type: {change_type}, Change Goals: {change_goals}, Leader ID: {leader_id}"

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        execution_status = result.get('execution_status', "Execution in progress")
        target_ids = result.get('target_ids', None)

        if not target_ids:
            return []

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update execution status
        self.profile.update_data("execution_status", execution_status)

        # Prepare and send ChangeExecutionEvent to EmployeeAgent(s)
        events = []
        for target_id in target_ids:
            change_execution_event = ChangeExecutionEvent(
                self.profile_id,
                target_id,
                manager_id=self.profile_id,
                execution_plan=execution_plan
            )
            events.append(change_execution_event)

        return events

    async def adjust_change_strategy(self, event: Event) -> List[Event]:
        # Check if the event is a FeedbackEvent
        if not isinstance(event, FeedbackEvent):
            return []

        # Retrieve required variables from the event
        feedback = event.feedback
        emotional_response = event.emotional_response

        # Prepare instruction for generate_reaction
        instruction = """
        Based on the feedback and emotional response from the employee, adjust the change strategy.
        Return the adjusted strategy details and determine the target_ids, which can be a single ID or a list of IDs.
        The response should be in the following JSON format:

        {
            "adjusted_strategy": "<Details of the adjusted strategy>",
            "target_ids": ["<The ID of the LeaderAgent(s) to notify>"]
        }
        """

        # Observation context for the LLM
        observation = f"Feedback: {feedback}, Emotional Response: {emotional_response}"

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        adjusted_strategy = result.get('adjusted_strategy', None)
        target_ids = result.get('target_ids', None)

        if not target_ids:
            return []

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the adjusted strategy
        self.profile.update_data("adjusted_strategy", adjusted_strategy)

        # Prepare and send StrategyAdjustedEvent to each target_id
        events = []
        for target_id in target_ids:
            strategy_adjusted_event = StrategyAdjustedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                manager_id=self.profile_id,
                adjusted_strategy=adjusted_strategy
            )
            events.append(strategy_adjusted_event)

        return events