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

class Party(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "position_policy")
        self.register_event("AttitudesUpdatedEvent", "adapt_strategy")

    async def position_policy(self, event: Event) -> List[Event]:
        # Retrieve required variables
        voter_issue_positions = await self.get_env_data("voter_issue_positions", {})
        party_ideology = self.profile.get_data("party_ideology", "")

        # Generate reaction with instruction
        instruction = """
        Formulate and adjust policy positions to align with voter preferences and differentiate from competitors.
        Please return the information in the following JSON format:

        {
        "policy_positions": "<Updated policy positions of the party>",
        "target_voter_demographics": "<Demographics of voters targeted by the party's policy positions>",
        "target_ids": "<The string ID or list of string IDs of the Voter agent(s)>"
        }
        """
    
        observation = f"Voter Issue Positions: {voter_issue_positions}, Party Ideology: {party_ideology}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        policy_positions = result.get('policy_positions', {})
        target_voter_demographics = result.get('target_voter_demographics', [])
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids] if target_ids is not None else []

        # Update agent's policy positions
        self.profile.update_data("policy_positions", policy_positions)

        # Prepare and send PolicyPositionedEvent to each target
        events = []
        for target_id in target_ids:
            event = PolicyPositionedEvent(
                self.profile_id,
                target_id,
                policy_positions=policy_positions,
                target_voter_demographics=target_voter_demographics
            )
            events.append(event)

        return events

    async def adapt_strategy(self, event: Event) -> List[Event]:
        # Condition Check: Feedback from election results
        feedback_data = event.updated_attitudes if hasattr(event, 'updated_attitudes') else {}
        if not feedback_data:
            return []

        # Retrieve current strategy from agent's profile
        current_strategy = self.profile.get_data("current_strategy", "")
        voter_ids = await self.env.get_agent_data_by_type("Voter", "id")

        # Generate reaction for strategy adaptation
        observation = f"Current strategy: {current_strategy}, Feedback data: {feedback_data}, Candidate Voter IDs: {voter_ids}"
        instruction = """Please adapt the party's strategy based on the given feedback data from election results.
        Provide the new strategy and the target voters to whom this strategy should be communicated.
        Return the information in the following JSON format:
        {
            "new_strategy": "<Description of the new strategy>",
            "target_ids": ["<List of target voter IDs>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)

        # Parse the response
        new_strategy = result.get('new_strategy', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids] if target_ids is not None else []

        # Update agent's profile with new strategy
        self.profile.update_data("new_strategy", new_strategy)

        # Prepare and send StrategyAdaptedEvent to the target voters
        events = []
        for target_id in target_ids:
            strategy_event = StrategyAdaptedEvent(self.profile_id, target_id, feedback_data=feedback_data, new_strategy=new_strategy)
            events.append(strategy_event)

        return events