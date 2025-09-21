from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import MediaSelectionEvent, ContentDeliveryEvent

class MediaAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("MediaSelectionEvent", "provide_content")

    async def provide_content(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is a MediaSelectionEvent
        if not isinstance(event, MediaSelectionEvent):
            return []

        # Access required variables from the event and agent profile
        voter_id = event.voter_id
        media_id = self.profile_id
        media_bias_score = self.profile.get_data("media_bias_score", 0.0)

        # Decision Making using generate_reaction
        instruction = """
        The 'provide_content' action is triggered by the 'MediaSelectionEvent'. 
        The media entity should provide political content to the voter based on the voter's media selection.
        Access the 'voter_id' from the event and 'media_bias_score' from the agent's profile.
        You must give a new media bias score that is different from previous one.
        Please return the result in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the VoterAgent(s) receiving the content>"],
        "new_media_bias_score": <The updated media bias score>
        }
        """
        observation = f"Voter ID: {voter_id}, Previous Media Bias Score: {media_bias_score}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        target_ids = result.get('target_ids', [])
        content_bias_score = result.get('new_media_bias_score', media_bias_score)
        self.profile.update_data("media_bias_score", content_bias_score)

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and send ContentDeliveryEvent(s) to each target VoterAgent
        events = []
        for target_id in target_ids:
            content_delivery_event = ContentDeliveryEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                media_id=media_id,
                voter_id=voter_id,
                content_bias_score=content_bias_score
            )
            events.append(content_delivery_event)

        return events