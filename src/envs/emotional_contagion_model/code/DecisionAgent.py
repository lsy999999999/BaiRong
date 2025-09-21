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

class DecisionAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("EmotionTransmittedEvent", "evaluate_emotional_influence")

    async def evaluate_emotional_influence(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if not isinstance(event, EmotionTransmittedEvent):
            return []

        # Data Access
        emotion_type = event.emotion_type
        intensity = event.intensity
        frequency_of_contact = event.frequency_of_contact

        # Decision Making
        instruction = """
        Evaluate the emotional influence based on the following parameters:
        - Emotion Type: {emotion_type}
        - Intensity: {intensity}
        - Frequency of Contact: {frequency_of_contact}

        Please return the evaluation result and adjustment factor in the following JSON format:
        {{
            "evaluation_result": "<Result of the emotional influence evaluation>",
            "adjustment_factor": <Factor by which emotional state needs adjustment>,
            "target_ids": ["<The ID or list of IDs of the target agents>"]
        }}
        """.format(emotion_type=emotion_type, intensity=intensity, frequency_of_contact=frequency_of_contact)

        observation = f"Emotion Type: {emotion_type}, Intensity: {intensity}, Frequency of Contact: {frequency_of_contact}"

        result = await self.generate_reaction(instruction, observation)

        # Response Processing
        evaluation_result = result.get('evaluation_result', "neutral")
        adjustment_factor = result.get('adjustment_factor', 0.0)
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send EmotionalInfluenceEvaluatedEvent to the target(s)
        events = []
        for target_id in target_ids:
            emotional_influence_event = EmotionalInfluenceEvaluatedEvent(
                self.profile_id, target_id, evaluation_result, adjustment_factor
            )
            events.append(emotional_influence_event)

        return events