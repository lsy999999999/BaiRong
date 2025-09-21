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

class FeedbackAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("PhysiologicalNeedsMetEvent", "collect_feedback")
        self.register_event("SocialNeedsSatisfiedEvent", "collect_feedback")
        self.register_event("SelfActualizationAchievedEvent", "collect_feedback")

    async def collect_feedback(self, event: Event) -> List[Event]:
        event_type = event.__class__.__name__

        # Condition Check Implementation
        if event_type not in ["PhysiologicalNeedsMetEvent", "SocialNeedsSatisfiedEvent", "SelfActualizationAchievedEvent"]:
            return []  # Return empty list if the condition is not met

        # Data Access
        agent_id = event.agent_id
        satisfaction_level = event.satisfaction_level
        feedback_data = await self.get_env_data("feedback_data", [])

        # Decision Making
        observation = f"Agent ID: {agent_id}, Satisfaction Level: {satisfaction_level}, Event Type: {event_type}"
        instruction = """Compile feedback based on the satisfaction levels from various events. 
        Please return the information in the following JSON format:
        
        {
        "feedback_id": "<Unique identifier for the feedback>",
        "completion_status": "completed",
        "results": "<Summary of the feedback processing results>",
        "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        feedback_id = result.get('feedback_id', "")
        completion_status = result.get('completion_status', "pending")
        results = result.get('results', "")
        target_ids = result.get('target_ids', None)

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update environment data
        feedback_data.append({
            "agent_id": agent_id,
            "satisfaction_level": satisfaction_level,
            "event_type": event_type
        })
        self.env.update_data("feedback_data", feedback_data)

        # Prepare and send the FeedbackProcessedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            feedback_event = FeedbackProcessedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                feedback_id=feedback_id,
                completion_status=completion_status,
                results=results
            )
            events.append(feedback_event)

        return events