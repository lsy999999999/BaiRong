from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import EmotionalStateInitializedEvent, EmotionTransmittedEvent

class CommunicationAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("EmotionalStateInitializedEvent", "transmit_emotion")

    async def transmit_emotion(self, event: Event) -> List[Event]:
        # Condition check: Ensure the event is of type 'EmotionalStateInitializedEvent'
        if not isinstance(event, EmotionalStateInitializedEvent):
            return []

        # Retrieve required variables from the event
        emotional_state = event.emotional_state
        intensity = 1.0  # Default value as per event definition
        frequency_of_contact = 1  # Default value as per event definition

        # Craft the instruction for generate_reaction
        instruction = """
        The agent needs to transmit its current emotional state to other agents. 
        Please determine the target agent(s) for this transmission based on the current context. 
        Ensure to return the response in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """

        # Observation context for the LLM
        observation = f"Emotional State: {emotional_state}, Intensity: {intensity}, Frequency of Contact: {frequency_of_contact}"

        # Generate reaction to determine target_ids
        result = await self.generate_reaction(instruction, observation)

        # Extract target_ids from the result
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send EmotionTransmittedEvent to each target
        events = []
        for target_id in target_ids:
            emotion_event = EmotionTransmittedEvent(self.profile_id, target_id, emotion_type=emotional_state, intensity=intensity, frequency_of_contact=frequency_of_contact)
            events.append(emotion_event)

        return events