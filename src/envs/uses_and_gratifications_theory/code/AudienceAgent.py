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

class AudienceAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "select_media")
        self.register_event("ContentProvidedEvent", "provide_feedback")

    async def select_media(self, event: Event) -> List[Event]:
        # Condition check
        if event.__class__.__name__ != "StartEvent":
            return []

        # Retrieve necessary data
        current_needs = self.profile.get_data("current_needs", [])
        available_media = await self.get_env_data("available_media", [])

        # Generate reaction to decide on media selection
        instruction = """Based on the current needs and available media, select the media type that best satisfies the audience agent's needs. 
        Ensure to return the selected media ID and target IDs in the following JSON format:

        {
        "selected_media": "<The ID of the media chosen>",
        "target_ids": ["<The string ID of the MediaAgent>"]
        }
        """

        observation = f"Current needs: {current_needs}, Available media: {available_media}"
        result = await self.generate_reaction(instruction, observation)

        # Process the LLM's response
        selected_media = result.get('selected_media', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Validate selected_media before updating profile
        if selected_media is None:
            return []

        self.profile.update_data("selected_media", selected_media)

        # Prepare and send MediaSelectedEvent to the MediaAgent(s)
        events = []
        need_type = current_needs[0] if current_needs else "unknown"
        for target_id in target_ids:
            media_selected_event = MediaSelectedEvent(self.profile_id, target_id, audience_id=self.profile_id, media_id=selected_media, need_type=need_type)
            events.append(media_selected_event)

        return events

    async def provide_feedback(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "ContentProvidedEvent":
            return []

        selected_media = self.profile.get_data("selected_media", 0)
        satisfaction_level = self.profile.get_data("satisfaction_level", 0)

        instruction = """Please determine the target MediaAgent(s) that should receive feedback based on the provided satisfaction level and selected media.
        Ensure to return the information in the following JSON format:
        {
        "target_ids": ["<The string ID(s) of the MediaAgent(s)>"],
        "satisfaction_level": <The integer satisfaction level>,
        "selected_media": <The integer identifier for the selected media>
        }
        """
        
        observation = f"Selected media: {selected_media}, Satisfaction level: {satisfaction_level}"
        result = await self.generate_reaction(instruction, observation)

        target_ids = result.get('target_ids', None)
        satisfaction_level = result.get('satisfaction_level', satisfaction_level)
        selected_media = result.get('selected_media', selected_media)

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Validate satisfaction_level and selected_media before updating profile
        if satisfaction_level is None or selected_media is None:
            return []

        feedback_history = self.profile.get_data("feedback_history", [])
        feedback_history.append({"media_id": selected_media, "satisfaction_level": satisfaction_level})
        self.profile.update_data("feedback_history", feedback_history)

        events = []
        for target_id in target_ids:
            feedback_event = FeedbackProvidedEvent(self.profile_id, target_id, audience_id=self.profile_id, media_id=selected_media, satisfaction_level=satisfaction_level)
            events.append(feedback_event)

        return events