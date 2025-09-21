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


class Citizens(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "decide_compliance")
        self.register_event("ComplianceDecisionEvent", "adjust_satisfaction")

    async def decide_compliance(self, event: Event) -> List[Event]:
        # Retrieve required agent variables
        policy_id = self.profile.get_data("policy_id", "")
        acceptance_level = self.profile.get_data("acceptance_level", 0.0)

        # Prepare instruction for LLM
        instruction = """Based on the acceptance level of the policy, generate a compliance decision for the citizens.
        The compliance level should be a float between 0 and 1, reflecting how much the citizens comply with the policy.
        Additionally, determine the target_ids, which can be a single ID or a list of IDs, for agents to receive the compliance decision.
        Please return the information in the following JSON format:

        {
        "compliance_level": <A float between 0 and 1>,
        "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """

        observation = f"Policy ID: {policy_id}, Acceptance Level: {acceptance_level}"

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        compliance_level = result.get('compliance_level', None)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's compliance level only if valid
        if compliance_level is not None and 0 <= compliance_level <= 1:
            self.profile.update_data("compliance_level", compliance_level)

        # Prepare and send ComplianceDecisionEvent to target agents
        events = []
        for target_id in target_ids:
            compliance_event = ComplianceDecisionEvent(self.profile_id, target_id, compliance_level=compliance_level, policy_id=policy_id)
            events.append(compliance_event)

        return events

    async def adjust_satisfaction(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if event.__class__.__name__ != "ComplianceDecisionEvent":
            return []

        # Data Access
        compliance_level = event.compliance_level
        policy_id = event.policy_id

        # Decision Making
        observation = f"Compliance Level: {compliance_level}, Policy ID: {policy_id}"
        instruction = """Based on the compliance level, adjust the citizen's satisfaction level. 
        If compliance is high, increase satisfaction; if low, decrease satisfaction. 
        Determine the 'adjustment_reason' accordingly.
        Please return the information in the following JSON format:

        {
        "satisfaction_level": <Updated satisfaction level ranging from 0 to 1>,
        "adjustment_reason": "<Reason for the satisfaction level adjustment>",
        "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        satisfaction_level = result.get('satisfaction_level', None)
        adjustment_reason = result.get('adjustment_reason', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Data Modification only if valid
        if satisfaction_level is not None:
            self.profile.update_data("satisfaction_level", satisfaction_level)
        if adjustment_reason is not None:
            self.profile.update_data("adjustment_reason", adjustment_reason)

        # Prepare and send SatisfactionAdjustedEvent to the EnvAgent
        events = []
        for target_id in target_ids:
            satisfaction_event = SatisfactionAdjustedEvent(self.profile_id, target_id, satisfaction_level, adjustment_reason)
            events.append(satisfaction_event)

        return events