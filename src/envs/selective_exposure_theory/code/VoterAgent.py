from typing import Any, List
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

class VoterAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "select_media_source")
        self.register_event("ContentDeliveryEvent", "adjust_political_preference")

    async def select_media_source(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "StartEvent":
            return []

        current_political_preference = self.profile.get_data("current_political_preference", 0.0)
        available_media_sources = await self.get_env_data("available_media_sources", [])

        if not available_media_sources:
            logger.warning("No available media sources for selection.")
            return []

        candidate_ids = await self.env.get_agent_data_by_type("MediaAgent", "id")

        instruction = """
        Analyze the voter's current political preference against the available media sources.
        Select the media source that most closely aligns with the voter's preferences.
        Please return the information in the following JSON format:

        {
        "selected_media_id": "<The ID of the selected media source>",
        "voter_id": "<Unique identifier for the voter>",
        "bias_alignment_score": "<Score representing the alignment of media bias with voter's preferences>",
        "target_ids": ["<The string ID of the MediaAgent>"]
        }
        """

        observation = f"Current political preference: {current_political_preference}, Available media sources: {available_media_sources}, Candidate IDs of MediaAgent: {candidate_ids} "

        result = await self.generate_reaction(instruction, observation)

        selected_media_id = result.get('selected_media_id', -1)
        voter_id = self.profile_id
        bias_alignment_score = result.get('bias_alignment_score', 0.0)
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("selected_media_id", selected_media_id)

        events = []
        for target_id in target_ids:
            media_selection_event = MediaSelectionEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                voter_id=voter_id,
                selected_media_id=selected_media_id,
                bias_alignment_score=bias_alignment_score
            )
            events.append(media_selection_event)

        return events

    async def adjust_political_preference(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "ContentDeliveryEvent":
            return []

        content_bias_score = event.fields['content_bias_score']
        current_political_preference = self.profile.get_data("current_political_preference", 0.0)

        observation = f"Current political preference: {current_political_preference}, Content bias score: {content_bias_score}"
        instruction = """Adjust the voter's political preference based on the media content bias score and current preference.
        Return the updated adjusted_political_preference and specify target_ids as either a single string ID or a list of IDs.
        Use the following JSON format:

        {
        "adjusted_political_preference": <The updated political preference score as a float>,
        "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        adjusted_political_preference = result.get('adjusted_political_preference', current_political_preference)
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("adjusted_political_preference", adjusted_political_preference)

        events = []
        for target_id in target_ids:
            preference_adjustment_event = PreferenceAdjustmentEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                voter_id=self.profile_id,
                adjusted_preference_score=adjusted_political_preference
            )
            events.append(preference_adjustment_event)

        return events