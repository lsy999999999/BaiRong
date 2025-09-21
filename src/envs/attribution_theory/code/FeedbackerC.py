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

class FeedbackerC(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("AttributionDecisionEvent", "evaluate_attribution")

    async def evaluate_attribution(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ != "AttributionDecisionEvent":
            return []

        # Access event data
        attribution_type = event.attribution_type
        reasoning = event.reasoning

        # Observation and instruction for generate_reaction
        observation = f"Attribution Type: {attribution_type}, Reasoning: {reasoning}"
        instruction = """
        Evaluate the attribution decision made by Participant A for any biases.
        Please return the evaluation results in the following JSON format:
        {
            "bias_detected": <true/false indicating if bias is detected>,
            "feedback_message": "<Feedback message regarding the attribution decision>",
            "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """

        # Generate reaction
        result = await self.generate_reaction(instruction, observation)

        # Parse results
        bias_detected = result.get('bias_detected', False)
        feedback_message = result.get('feedback_message', "")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent state
        self.profile.update_data("bias_detected", bias_detected)
        self.profile.update_data("feedback_message", feedback_message)

        # Create and return events
        events = []
        for target_id in target_ids:
            feedback_event = AttributionFeedbackEvent(self.profile_id, target_id, bias_detected=bias_detected, feedback_message=feedback_message)
            events.append(feedback_event)

        return events