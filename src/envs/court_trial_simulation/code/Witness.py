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

class Witness(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "prepare_testimony")
        self.register_event("WitnessCallEvent", "testify")

    async def prepare_testimony(self, event: Event) -> List[Event]:
        # Condition check: Witness must prepare for potential testimony
        if not self.profile.get_data("must_prepare_testimony", False):
            return []

        # Observation context for generating reaction
        observation = self.profile.get_data("testimony_content", "")

        # Generate reaction using LLM to prepare the testimony content
        instruction = """Please prepare the content for the witness's testimony. 
        The testimony should be finalized and ready for presentation during the trial.
        Ensure the response includes the target_ids for the Judge.
        Return the information in the following JSON format:

        {
        "prepared_testimony": "<Finalized testimony content>",
        "target_ids": ["<The string ID of the Judge>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
    
        # Extract prepared testimony and target_ids from the LLM's response
        prepared_testimony = result.get('prepared_testimony', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the prepared testimony
        self.profile.update_data("prepared_testimony", prepared_testimony)

        # Create and send the TestimonyPreparedEvent to the Judge
        events = []
        for target_id in target_ids:
            testimony_event = TestimonyPreparedEvent(self.profile_id, target_id, prepared_testimony)
            events.append(testimony_event)

        return events

    async def testify(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the action is called during trial proceedings
        trial_phase = self.profile.get_data("trial_phase", "ongoing")
        if trial_phase != "ongoing":
            return []

        # Access required event data
        witness_id = event.witness_id

        # Prepare instruction for the LLM
        instruction = """
        The Witness is called upon to testify during the trial proceedings. 
        Please generate the testimony details and specify the target IDs for sending the testimony event. 
        The response should be in the following JSON format:

        {
        "testimony_details": "<Details of the testimony provided by the witness>",
        "target_ids": ["<The string ID(s) of the Jury agent(s)>"]
        }
        """
        observation = f"Witness ID: {witness_id}, Trial Phase: {trial_phase}"

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        testimony_details = result.get('testimony_details', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent state to reflect testimony delivery
        self.profile.update_data("testimony_given", "yes")

        # Prepare and send TestimonyEvent to the Jury
        events = []
        for target_id in target_ids:
            testimony_event = TestimonyEvent(self.profile_id, target_id, testimony_details)
            events.append(testimony_event)

        return events