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

class UtilityEvaluator(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("ChoicesEvaluatedEvent", "calculate_utility")

    async def calculate_utility(self, event: Event) -> List[Event]:
        # Condition Check
        if not isinstance(event, ChoicesEvaluatedEvent):
            return []

        # Data Access
        evaluated_choices = event.choices_list
        evaluation_criteria = event.evaluation_criteria
        candidate_ids = await self.env.get_agent_data_by_type("RationalDecisionMaker", "id")

        # Decision Making
        instruction = """
        Calculate the utility for the given evaluated choices based on the evaluation criteria.
        Please return the information in the following JSON format:

        {
        "utility_value": "<The calculated utility value as a float>",
        "calculation_details": "<A dictionary detailing the calculation including factors considered>",
        "target_ids": ["<The string ID(s) of the RationalDecisionMaker agent(s)>"]
        }
        """
        observation = f"Evaluated Choices: {evaluated_choices}, Evaluation Criteria: {evaluation_criteria}, Candidate IDs of RationalDecisionMaker agent(s): {candidate_ids}"
        result = await self.generate_reaction(instruction, observation)


        # Response Processing
        utility_value = result.get('utility_value', 0.0)
        calculation_details = result.get('calculation_details', {})
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent data
        self.profile.update_data("utility_value", utility_value)

        # Prepare and send UtilityCalculatedEvent to each target
        events = []
        for target_id in target_ids:
            utility_event = UtilityCalculatedEvent(self.profile_id, target_id, utility_value, calculation_details)
            events.append(utility_event)

        return events