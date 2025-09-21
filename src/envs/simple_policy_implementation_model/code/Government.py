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

class Government(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "execute_policy")
        self.register_event("PolicyExecutedEvent", "adjust_policy_strength")

    async def execute_policy(self, event: Event) -> List[Event]:
        # Retrieve necessary data from agent profile
        policy_id = self.profile.get_data("policy_id", "")
        current_strength = self.profile.get_data("current_strength", 0.0)

        # Generate efficiency metrics based on current policy strength
        observation = f"Policy ID: {policy_id}, Current Strength: {current_strength}"
        instruction = """
        Please calculate the efficiency metrics for the policy execution based on the current strength.
        Return the information in the following JSON format:
        {
            "efficiency_metrics": "<Calculated efficiency metrics ranging from 0 to 1>",
            "policy_id": "<The string ID of the executed policy>",
            "target_ids": ["<The string ID(s) of the Government agent(s) for next action>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        efficiency_metrics = result.get('efficiency_metrics', None)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Check if efficiency_metrics is valid before updating
        if efficiency_metrics is None:
            return []

        # Update agent profile with new efficiency metrics
        self.profile.update_data("efficiency_metrics", efficiency_metrics)

        # Prepare and send PolicyExecutedEvent to the next action
        events = []
        for target_id in target_ids:
            policy_executed_event = PolicyExecutedEvent(self.profile_id, target_id, efficiency_metrics=efficiency_metrics, policy_id=policy_id)
            events.append(policy_executed_event)

        return events

    async def adjust_policy_strength(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if event.__class__.__name__ != "PolicyExecutedEvent":
            return []

        efficiency_metrics = event.efficiency_metrics
        policy_id = event.policy_id

        # Generate reaction using LLM
        observation = f"Efficiency metrics: {efficiency_metrics}, Policy ID: {policy_id}"
        instruction = """Adjust the strength of the policy based on the efficiency metrics.
        The efficiency metrics range from 0 to 1, where higher values indicate better efficiency.
        If efficiency is high, increase policy strength; if low, decrease it.
        Please return the information in the following JSON format:
        {
            "new_strength": <Updated strength of the policy>,
            "adjustment_reason": "<Reason for the adjustment>",
            "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        new_strength = result.get('new_strength', None)
        adjustment_reason = result.get('adjustment_reason', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Check if new_strength and adjustment_reason are valid before updating
        if new_strength is None or adjustment_reason is None:
            return []

        # Update agent's state
        self.profile.update_data("efficiency_metrics", new_strength)
        self.profile.update_data("adjustment_reason", adjustment_reason)

        # Prepare and send PolicyStrengthAdjustedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            adjusted_event = PolicyStrengthAdjustedEvent(self.profile_id, target_id, new_strength, adjustment_reason)
            events.append(adjusted_event)

        return events