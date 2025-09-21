from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import *

class LeaderAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_change_process")
        self.register_event("StrategyAdjustedEvent", "finalize_change_process")

    async def initiate_change_process(self, event: Event) -> List[Event]:
        # Retrieve required variables from environment and agent profile
        change_type = await self.get_env_data("change_type", "incremental")
        change_goals = self.profile.get_data("change_goals", "")

        # Update the environment's change status
        self.env.update_data("change_status", "Change process initiated")

        # Generate LLM reaction to decide on target_ids
        instruction = f"""
        The LeaderAgent has initiated a change process. The following details are available:
        - Change type: {change_type}
        - Change goals: {change_goals}

        Please determine the appropriate ManagerAgent(s) to receive the next event. 
        Return the response in the following JSON format:
        {{
            "change_type": "<Type of change>",
            "change_goals": "<Goals of the change process>",
            "target_ids": ["<List of ManagerAgent IDs>"]
        }}
        """

        result = await self.generate_reaction(instruction)

        # Extract data from LLM response
        change_type = result.get("change_type", change_type)
        change_goals = result.get("change_goals", change_goals)
        target_ids = result.get("target_ids", [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send ChangeInitiatedEvent to each target ManagerAgent
        events = []
        for target_id in target_ids:
            change_event = ChangeInitiatedEvent(
                self.profile_id, target_id, change_type=change_type, change_goals=change_goals, leader_id=self.profile_id
            )
            events.append(change_event)

        return events

    async def finalize_change_process(self, event: Event) -> List[Event]:
        # Ensure the event is of correct type
        if not isinstance(event, StrategyAdjustedEvent):
            return []  # Return empty list if event is not valid

        # Access required event data
        adjusted_strategy = getattr(event, 'adjusted_strategy', '')
        manager_id = getattr(event, 'manager_id', '')

        # Prepare observation and instruction for LLM
        observation = f"Adjusted Strategy: {adjusted_strategy}, Manager ID: {manager_id}"
        instruction = """
        Evaluate the adjusted strategy and finalize the change process. Document the outcomes. 
        Please return the information in the following JSON format:

        {
            "final_report": "<A detailed report of the adjusted strategy and outcomes>",
            "target_ids": ["ENV"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract data from LLM response
        final_report = result.get('final_report', None)
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state with the final report
        self.profile.update_data("final_report", final_report)

        # Prepare and send ChangeFinalizedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            change_finalized_event = ChangeFinalizedEvent(
                self.profile_id, target_id, leader_id=self.profile_id, completion_status="success", results=final_report
            )
            events.append(change_finalized_event)

        return events