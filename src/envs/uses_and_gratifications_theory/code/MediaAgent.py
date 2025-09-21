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

class MediaAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("MediaSelectedEvent", "provide_content")
        self.register_event("FeedbackProvidedEvent", "record_feedback")

    async def provide_content(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is from AudienceAgent and the action is 'select_media'
        # if not (event.from_agent_type == "AudienceAgent" and event.from_action_name == "select_media"):
        #     return []

        # Access event data
        audience_id = event.audience_id
        media_id = event.media_id
        need_type = event.need_type

        # Access agent data
        content_type = self.profile.get_data("content_type", "unknown")
        target_need = self.profile.get_data("target_need", "unknown")

        # Generate reaction using LLM
        observation = f"Audience ID: {audience_id}, Media ID: {media_id}, Need Type: {need_type}"
        instruction = """Please decide the appropriate content to provide based on the audience's need type and media selection. 
        Return the results in the following JSON format:
        {
            "target_ids": ["<List of audience agent IDs>"],
            "delivered_content": {
                "content_type": "<Type of content being provided>",
                "target_need": "<Need that the content aims to satisfy>"
            }
        }
        """

        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM's JSON response
        target_ids = result.get('target_ids', [])
        delivered_content = result.get('delivered_content', {})
        if not isinstance(delivered_content, dict):
            return []  # Validate delivered_content structure
        content_type = delivered_content.get('content_type', None)
        target_need = delivered_content.get('target_need', None)
        if not content_type or not target_need:
            return []  # Ensure both fields are extracted correctly

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and send ContentProvidedEvent to each target
        events = []
        for target_id in target_ids:
            content_event = ContentProvidedEvent(
                self.profile_id, target_id,
                media_id=media_id,
                content_type=content_type,
                target_need=target_need
            )
            events.append(content_event)

        return events

    async def record_feedback(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is from AudienceAgent
        # if event.from_agent_type != "AudienceAgent":
        #     return []

        # Access feedback data from event
        audience_id = event.audience_id
        media_id = event.media_id
        satisfaction_level = event.satisfaction_level

        # Update feedback_records in agent profile
        feedback_data = {
            "audience_id": audience_id,
            "media_id": media_id,
            "satisfaction_level": satisfaction_level
        }
        feedback_records = self.profile.get_data("feedback_records", [])
        if not isinstance(feedback_records, list):
            feedback_records = []  # Reset feedback_records if not a list
        feedback_records.append(feedback_data)
        self.profile.update_data("feedback_records", feedback_records)

        # Decision Making: Generate reaction for target_ids selection
        instruction = """Record the feedback provided by the audience agent to adjust future content offerings.
        Please return the information in the following JSON format:
        {
        "target_ids": ["ENV"]
        }
        """
        observation = f"Feedback recorded for media_id {media_id} with satisfaction level {satisfaction_level}"
        result = await self.generate_reaction(instruction, observation)

        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send FeedbackRecordedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            feedback_recorded_event = FeedbackRecordedEvent(
                self.profile_id, target_id, media_id=media_id, completion_status="completed"
            )
            events.append(feedback_recorded_event)

        return events