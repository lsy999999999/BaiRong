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

class Citizen(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_grievance")
        self.register_event("GrievanceEvaluatedEvent", "decide_rebellion")

    async def evaluate_grievance(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "StartEvent":
            return []

        personal_experience = self.profile.get_data("personal_experience", 0.0)
        social_influence = await self.get_env_data("social_influence", 0.0)

        instruction = """Evaluate the citizen's grievance level based on their personal experience and social influence.
        Return the evaluation in the following JSON format:

        {
        "grievance_level": <Calculated grievance level as a float>,
        "target_ids": ["<The string ID(s) of the Citizen agent(s) to decide on rebellion>"]
        }
        """

        observation = f"Personal experience: {personal_experience}, Social influence: {social_influence}"

        result = await self.generate_reaction(instruction, observation)

        grievance_level = result.get('grievance_level', 0.0)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("grievance_level", grievance_level)

        events = []
        for target_id in target_ids:
            grievance_event = GrievanceEvaluatedEvent(self.profile_id, target_id, grievance_level=grievance_level, citizen_id=self.profile_id)
            events.append(grievance_event)

        return events

    async def decide_rebellion(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "GrievanceEvaluatedEvent":
            return []

        grievance_level = event.grievance_level
        citizen_id = event.citizen_id

        grievance_level = self.profile.get_data("grievance_level", grievance_level)

        observation = f"Grievance level: {grievance_level}, Citizen ID: {citizen_id}"
        instruction = """Based on the grievance level, decide whether to participate in rebellion.
        If grievance_level exceeds a predefined threshold, decide to rebel. Otherwise, decide not to rebel.
        Return the decision and target_ids in the following JSON format:
        
        {
        "rebellion_decision": "<True or False>",
        "target_ids": ["<The string ID(s) of the Government agent(s) or 'ENV'>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        rebellion_decision = result.get('rebellion_decision', False)
        if rebellion_decision.__class__.__name__ == "str":
            rebellion_decision = rebellion_decision.lower() == "true"
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("rebellion_decision", rebellion_decision)

        events = []
        if rebellion_decision:
            for target_id in target_ids:
                rebellion_event = RebellionDecisionEvent(citizen_id, target_id, citizen_id=citizen_id, decision=True)
                events.append(rebellion_event)
        else:
            for target_id in target_ids:
                no_rebellion_event = NoRebellionEvent(citizen_id, target_id, citizen_id=citizen_id, decision=False)
                events.append(no_rebellion_event)

        return events