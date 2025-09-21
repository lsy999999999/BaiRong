
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


class PublicAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("TopicEmphasizedEvent", "adjust_focus")

    async def adjust_focus(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is of type 'TopicEmphasizedEvent'
        if event.__class__.__name__ != "TopicEmphasizedEvent":
            return []
    
        # Access event data
        emphasized_topic = event.topic_id
        reporting_frequency = event.reporting_frequency
        emotional_tone = event.emotional_tone
    
        # Access agent data
        current_focus_value = self.profile.get_data("focus_value", 0.0)
    
        # Generate reaction for decision making
        instruction = f"""
        Adjust the focus value for the topic '{emphasized_topic}' based on the reporting frequency '{reporting_frequency}' and emotional tone '{emotional_tone}'.
        Please provide the updated focus value and specify the target_ids, which can be a single ID or a list of IDs. Target should be 'ENV' for terminal events.
    
        Return the information in the following JSON format:
        {{
            "new_focus_value": <Updated focus value as a float>,
            "target_ids": ["ENV"]
        }}
        """
        observation = f"Current focus value: {current_focus_value}, Reporting frequency: {reporting_frequency}, Emotional tone: {emotional_tone}"
        result = await self.generate_reaction(instruction, observation)
    
        # Parse LLM response
        new_focus_value = result.get('new_focus_value', current_focus_value)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent data
        self.profile.update_data("focus_value", new_focus_value)
    
        # Prepare and send FocusAdjustedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            focus_adjusted_event = FocusAdjustedEvent(
                self.profile_id, target_id,
                public_agent_id=self.profile_id,
                topic_id=emphasized_topic,
                new_focus_value=new_focus_value
            )
            events.append(focus_adjusted_event)
    
        return events
