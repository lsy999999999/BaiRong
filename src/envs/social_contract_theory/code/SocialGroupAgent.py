
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


class SocialGroupAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("ContractProposalEvent", "evaluate_collective_interests")

    async def evaluate_collective_interests(self, event: Event) -> List[Event]:
        # Condition check: Reception of ContractProposalEvent
        if event.__class__.__name__ != "ContractProposalEvent":
            return []
    
        # Access required variables
        collective_interests = event.individual_interests
        evaluation_criteria = self.profile.get_data("evaluation_criteria", "")
    
        # Decision making using generate_reaction
        instruction = """
        Evaluate the collective interests against the agent's evaluation criteria.
        Please return the information in the following JSON format:
    
        {
        "evaluation_status": "<Status of the evaluation process>",
        "target_ids": ["<The string ID(s) of the GovernmentAgent(s) to review the social contract>"]
        }
        """
        observation = f"Collective interests: {collective_interests}, Evaluation criteria: {evaluation_criteria}"
        result = await self.generate_reaction(instruction, observation)
    
        # Process the LLM's returned results
        evaluation_status = result.get('evaluation_status', "Pending")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile data
        self.profile.update_data("evaluation_status", evaluation_status)
    
        # Prepare and send CollectiveInterestEvent to each target
        events = []
        for target_id in target_ids:
            collective_interest_event = CollectiveInterestEvent(self.profile_id, target_id, collective_interests, evaluation_criteria)
            events.append(collective_interest_event)
    
        return events
