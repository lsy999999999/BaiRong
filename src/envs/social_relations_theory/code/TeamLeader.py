from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class TeamLeader(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InteractionEvent", "provide_feedback")

    async def provide_feedback(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "InteractionEvent":
            return []

        interaction_type = event.interaction_type
        initiator_emotion = event.initiator_emotion
        receiver_role = event.receiver_role

        feedback_content = self.profile.get_data("feedback_content", "general")
        em_ids = await self.env.get_agent_data_by_type("EmotionalAnalyzer", "id")


        instruction = f"""Based on the interaction type '{interaction_type}' and initiator's emotion '{initiator_emotion}', 
            generate feedback that is contextually appropriate. Please return the feedback message and a list of target_ids 
            (which can be a single string ID or a list of IDs) choosen from Candidate Target IDs. 
            Return the information in the following JSON format:

            {{
            "feedback_message": "<The feedback message tailored to the interaction>",
            "target_ids": ["<The string ID of the target agent(s)>"]
            }}
            """

        observation = f"Initiator emotion: {initiator_emotion}, Interaction type: {interaction_type}, Candidate Target IDS: {em_ids}"
        result = await self.generate_reaction(instruction, observation)

        feedback_message = result.get('feedback_message', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("feedback_status", "delivered")

        events = []
        for target_id in target_ids:
            feedback_event = FeedbackEvent(self.profile_id, target_id, feedback_message)
            events.append(feedback_event)

        return events