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

class SocialNormAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_social_norms")
        self.register_event("IntentionInitializedEvent", "adjust_subjective_norms")

    async def evaluate_social_norms(self, event: Event) -> List[Event]:
        candidate_ids = await self.env.get_agent_data_by_type("CognitiveAgent", "id")
        observation = f"Candidate IDs of CognitiveAgent(s): {candidate_ids}"
        instruction = """Evaluate the social norms affecting the agent and quantify their influence on the agent's intentions.
        Please return the information in the following JSON format:
        {
            "social_norms_score": "<A float representing the influence of social norms>",
            "target_ids": ["<The string ID(s) of the CognitiveAgent(s) to send the evaluation results>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)
        social_norms_score = result.get('social_norms_score', 0.0)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        self.profile.update_data("social_norms_score", social_norms_score)
        events = []
        for target_id in target_ids:
            social_norms_evaluated_event = SocialNormsEvaluatedEvent(self.profile_id, target_id, social_norms_score=social_norms_score)
            events.append(social_norms_evaluated_event)
        return events

    async def adjust_subjective_norms(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "IntentionInitializedEvent":
            return []
        social_norms_score = self.profile.get_data("social_norms_score", 0.0)
        candidate_ids = await self.env.get_agent_data_by_type("CognitiveAgent", "id")
        instruction = """
        Adjust the agent's subjective norms based on the evaluated social norms score.
        Please return the information in the following JSON format:
        
        {
        "adjusted_subjective_norms": {"<norm_name>": <adjusted_value>, ...},
        "target_ids": ["<The string ID of the CognitiveAgent>"]
        }
        """
        observation = f"Social norms score: {social_norms_score}, Candidate IDs of CognitiveAgent(s): {candidate_ids}"
        result = await self.generate_reaction(instruction, observation)
        adjusted_subjective_norms = result.get('adjusted_subjective_norms', {})
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        self.profile.update_data("adjusted_subjective_norms", adjusted_subjective_norms)
        events = []
        for target_id in target_ids:
            norms_adjusted_event = SubjectiveNormsAdjustedEvent(self.profile_id, target_id, adjusted_subjective_norms)
            events.append(norms_adjusted_event)
        return events