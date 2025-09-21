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

class EmotionalAnalyzer(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("FeedbackEvent", "analyze_emotion")

    async def analyze_emotion(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if event.__class__.__name__ != "FeedbackEvent":
            return []


        # Data Access
        feedback_content = event.feedback_content

        # Decision Making using LLM
        instruction = """Analyze the feedback_content to determine the emotional state of the employee.
        Include observation context for generate_reaction. Return the analysis result and status in the following JSON format:
        {
        "emotion_analysis_result": "<Result of the emotional analysis>",
        "analysis_status": "<Status of the analysis process>",
        "target_ids": ["ENV"]
        }
        """
        observation = f"Feedback Content: {feedback_content}"
        result = await self.generate_reaction(instruction, observation)
        
        # Response Processing
        emotion_analysis_result = result.get('emotion_analysis_result', None)
        analysis_status = result.get('analysis_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Data Modification
        self.profile.update_data("emotion_analysis_result", emotion_analysis_result)
        self.profile.update_data("analysis_status", analysis_status)

        # Prepare and send EmotionAnalyzedEvent(s)
        events = []
        for target_id in target_ids:
            emotion_event = EmotionAnalyzedEvent(self.profile_id, target_id, emotion_analysis_result, analysis_status)
            events.append(emotion_event)

        return events