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

class Media(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "set_agenda")
        self.register_event("MediaInfluencedEvent", "set_agenda")

    async def set_agenda(self, event: Event) -> List[Event]:
        # Retrieve necessary data from agent and environment
        media_ideology_bias = self.profile.get_data("media_ideology_bias", "neutral")
        agenda_setting_power = self.profile.get_data("agenda_setting_power", 0.0)
        current_issues = await self.get_env_data("current_issues", [])

        voter_ids = await self.env.get_agent_data_by_type("Voter", 'id')

        # Construct the observation and instruction for the LLM
        observation = f"Media Ideology Bias: {media_ideology_bias}, Agenda Setting Power: {agenda_setting_power}, Current Issues: {current_issues}, Candidate Voter IDs: {voter_ids}"
        instruction = """Based on the media's ideology bias and agenda setting power, select and prioritize issues from the current issues list to set the agenda. If there is no current issue, you should propose an issue yourself and  send them to some Voters.
        Please return the information in the following JSON format:
    
        {
        "agenda_topics": ["<List of selected agenda topics>"],
        "framing_strategy": "<The strategy used by the media to frame issues>",
        "target_ids": ["<The string ID(s) of the Voter agent(s)>"]
        }
        """

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's response
        agenda_topics = result.get('agenda_topics', [])
        framing_strategy = result.get('framing_strategy', "")
        target_ids = result.get('target_ids', None)
        
        # Check if target_ids is None before converting it to a list
        if target_ids is None:
            logger.warning("No target_ids provided, returning empty event list.")
            return []  # Return empty list if target_ids is None

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state with new agenda topics
        self.profile.update_data("agenda_topics", agenda_topics)

        # Prepare and send the AgendaSetEvent to each target
        events = []
        for target_id in target_ids:
            agenda_set_event = AgendaSetEvent(self.profile_id, target_id, agenda_topics=agenda_topics, framing_strategy=framing_strategy)
            events.append(agenda_set_event)

        return events