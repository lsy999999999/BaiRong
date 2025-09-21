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

class Pollster(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "select_voter")
        self.register_event("ExpressOpinionEvent", "record_opinion")

    async def select_voter(self, event: Event) -> List[Event]:
        # Generate the reaction to select a voter
        instruction = """
        You are a pollster initiating the polling process by selecting a voter. 
        Your task is to identify one or more voters to participate in the opinion poll.
        Please return the information in the following JSON format:

        {
        "selected_voter_id": ["<The string ID(s) of the selected Voter(s)>"]
        }
        """

        # Generate the reaction to select voter(s)
        result = await self.generate_reaction(instruction)

        # Retrieve the selected voter ID(s)
        selected_voter_ids = result.get('selected_voter_id', [])
        if not isinstance(selected_voter_ids, list):
            selected_voter_ids = [selected_voter_ids]

        # If no voters are selected, handle this explicitly
        if not selected_voter_ids:
            logger.warning("No voters were selected. Check the selection criteria or process.")
            return []

        # Prepare and send the VoterSelectedEvent to each selected voter
        events = []
        pollster_id = self.profile_id
        for voter_id in selected_voter_ids:
            voter_selected_event = VoterSelectedEvent(pollster_id, voter_id, voter_id=voter_id, pollster_id=pollster_id)
            events.append(voter_selected_event)

        return events

    async def record_opinion(self, event: Event) -> List[Event]:
        # Condition Check: Ensure voter has participated in the poll
        if not isinstance(event, ExpressOpinionEvent):
            return []

        # Access event data
        voter_id = event.voter_id
        policy_preferences = event.policy_preferences

        # Update agent's state with opinion_data and completion_status
        self.profile.update_data("opinion_data", policy_preferences)
        self.profile.update_data("completion_status", "completed")

        # Prepare instruction for generating reaction
        instruction = """
        Please prepare the opinion data for analysis. Ensure the data is formatted correctly and include the target_ids for sending the OpinionRecordedEvent. 
        The response should be in the following JSON format:

        {
        "opinion_data": "<Formatted opinion data>",
        "completion_status": "completed",
        "target_ids": ["ENV"]
        }
        """
        observation = f"Voter ID: {voter_id}, Policy Preferences: {policy_preferences}"

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract and validate response data
        opinion_data = result.get('opinion_data', policy_preferences)
        completion_status = result.get('completion_status', "completed")
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send OpinionRecordedEvent to target agents
        events = []
        pollster_id = self.profile_id
        for target_id in target_ids:
            opinion_event = OpinionRecordedEvent(pollster_id, target_id, pollster_id=pollster_id, opinion_data=opinion_data, completion_status=completion_status)
            events.append(opinion_event)

        return events