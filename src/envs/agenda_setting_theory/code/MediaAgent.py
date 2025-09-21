
from typing import Any, List,Optional
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
        self.register_event("StartEvent", "select_topic")
        self.register_event("TopicSelectedEvent", "emphasize_topic")

    async def select_topic(self, event: Event) -> List[Event]:
        # Condition Check: Access to topic library
        topic_library = await self.get_env_data("topic_library", [])
        if not topic_library:
            return []
    
        # Decision Making: Generate reaction to select a topic
        instruction = """
        You are a MediaAgent tasked with selecting a topic from the topic library to report on.
        Your goal is to influence public agenda by choosing a topic that will have significant impact.
        Please select a topic from the library and decide on the target IDs to send the 'TopicSelectedEvent'.
        Ensure the response is in the following JSON format:
    
        {
        "selected_topic": "<The topic selected from the topic library>",
        "target_ids": ["<The string ID(s) of the MediaAgent(s) to emphasize the topic>"]
        }
        """
        observation = f"Available topics: {topic_library}"
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's JSON response
        selected_topic = result.get('selected_topic', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile with the selected topic
        self.profile.update_data("selected_topic", selected_topic)
    
        # Prepare and send TopicSelectedEvent to the emphasize_topic action of MediaAgent(s)
        events = []
        for target_id in target_ids:
            topic_selected_event = TopicSelectedEvent(self.profile_id, target_id, topic_id=selected_topic, media_agent_id=self.profile_id)
            events.append(topic_selected_event)
    
        return events

    async def emphasize_topic(self, event: Event) -> List[Event]:
        # Check if the condition "Topic selected for reporting" is met
        selected_topic = self.profile.get_data("selected_topic", "")
        if not selected_topic:
            return []
    
        # Retrieve required variables
        reporting_frequency = self.profile.get_data("reporting_frequency", 0)
        emotional_tone = self.profile.get_data("emotional_tone", "neutral")
        media_agent_id = self.profile_id
    
        observation = f"Selected topic: {selected_topic}, Reporting frequency: {reporting_frequency}, Emotional tone: {emotional_tone}"
        instruction = """Emphasize the selected topic through increased reporting frequency and emotional language to influence public perception and attention. 
        Decide on the target PublicAgent(s) to send the TopicEmphasizedEvent. Return the information in the following JSON format:
    
        {
        "target_ids": ["<The string ID(s) of the PublicAgent(s)>"]
        }
        """
    
        # Generate reaction to decide on target_ids
        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare and send the TopicEmphasizedEvent to the PublicAgent(s)
        events = []
        for target_id in target_ids:
            topic_emphasized_event = TopicEmphasizedEvent(
                self.profile_id,
                target_id,
                topic_id=selected_topic,
                reporting_frequency=reporting_frequency,
                emotional_tone=emotional_tone,
                media_agent_id=media_agent_id
            )
            events.append(topic_emphasized_event)
    
        return events
