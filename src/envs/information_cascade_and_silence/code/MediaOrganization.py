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

class MediaOrganization(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "select_content")
        self.register_event("ContentCreatedEvent", "select_content")
        self.register_event("InformationAmplifiedEvent", "select_content")
        self.register_event("ContentSelectedEvent", "publish_content")

    async def select_content(self, event: Event) -> List[Event]:
        content = None

        # Retrieve required variables based on event type
        if event.__class__.__name__ == "ContentCreatedEvent":
            content = event.content
            media_org_id = getattr(event, "media_org_id", None)
        elif event.__class__.__name__ == "InformationAmplifiedEvent":
            content = event.amplified_content
            media_org_id = getattr(event, "media_org_id", None)
        else:
            return []  # Ignore events that don't match the expected types

        # Validate the event's target media organization ID
        if media_org_id and media_org_id != self.profile_id:
            return []  # Ignore the event if it is not meant for this agent

        # Retrieve the media organization's editorial policy
        editorial_policy = self.profile.get_data("editorial_policy", "default")

        # Generate reaction to select content based on editorial policy
        observation = f"Content received: {content}. Editorial policy: {editorial_policy}."
        instruction = """Analyze the provided content and editorial policy to determine the selected content and criteria for selection.
        Please return the information in the following JSON format:
        {
            "selected_content": "<The content selected for publication>",
            "selection_criteria": "<The criteria used for selecting the content>",
            "target_ids": ["<The string ID or list of IDs of the target agents>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's response
        selected_content = result.get("selected_content", None)
        selection_criteria = result.get("selection_criteria", None)
        target_ids = result.get("target_ids", None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's state with the selected content and criteria
        self.profile.update_data("selected_content", selected_content)
        self.profile.update_data("selection_criteria", selection_criteria)

        # Prepare and send the ContentSelectedEvent to the target agents
        events = []
        for target_id in target_ids:
            content_selected_event = ContentSelectedEvent(
                self.profile_id, target_id, selected_content, selection_criteria
            )
            events.append(content_selected_event)

        return events

    async def publish_content(self, event: Event) -> List[Event]:
        # Condition Check: Ensure "Content selection complete"
        selected_content = self.profile.get_data("selected_content", "")
        if not selected_content:
            return []

        # Validate that selected_content aligns with incoming event data
        if event.__class__.__name__ == "ContentSelectedEvent":
            event_selected_content = getattr(event, "selected_content", None)
            if event_selected_content and event_selected_content != selected_content:
                return []  # Ignore if selected_content does not match the event data

        # Observation and Instruction for LLM
        observation = f"Selected content: {selected_content}"
        instruction = """You are tasked with publishing content selected by a media organization. 
        Use the selected content provided in the observation to generate a JSON response in the following format:
    
        {
            "published_content": "<The content to be published>",
            "target_ids": ["<The string ID(s) of the FactCheckOrganization agent(s)>"]
        }
    
        Ensure that 'published_content' is derived directly from the 'selected_content'. 
        'target_ids' can be a single ID or a list of IDs. Strategically decide which FactCheckOrganization(s) to target 
        based on the context provided in the observation."""

        # Generate reaction from LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract and validate response
        published_content = result.get("published_content", None)
        target_ids = result.get("target_ids", None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent profile with published content
        self.profile.update_data("published_content", published_content)

        # Prepare and send outgoing events
        events = []
        for target_id in target_ids:
            content_published_event = ContentPublishedEvent(
                self.profile_id, target_id, published_content, target_id
            )
            events.append(content_published_event)

        return events