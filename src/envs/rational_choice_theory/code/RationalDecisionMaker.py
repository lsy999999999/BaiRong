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

class RationalDecisionMaker(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_choices")
        self.register_event("UtilityCalculatedEvent", "make_decision")

    async def evaluate_choices(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "StartEvent":
            return []

        decision_options = await self.get_env_data("decision_options", [])
        personal_goals = self.profile.get_data("personal_goals", {})
        resource_status = self.profile.get_data("resource_status", {})

        instruction = """
        Evaluate the provided decision options based on personal goals and resource status.
        Return the evaluated choices and the criteria used in the following JSON format:
        {
            "evaluated_choices": ["<List of evaluated choices>"],
            "evaluation_criteria": {
                "personal_goals": "<Personal goals influencing the evaluation>",
                "risk_factors": "<Risk factors considered during evaluation>"
            },
            "target_ids": ["<The string ID(s) of the UtilityEvaluator agent(s)>"]
        }
        """
        observation = f"Decision options: {decision_options}, Personal goals: {personal_goals}, Resource status: {resource_status}"
        result = await self.generate_reaction(instruction, observation)

        evaluated_choices = result.get('evaluated_choices', [])
        evaluation_criteria = result.get('evaluation_criteria', {})
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("evaluated_choices", evaluated_choices)

        events = []
        for target_id in target_ids:
            choices_evaluated_event = ChoicesEvaluatedEvent(
                self.profile_id,
                target_id,
                evaluated_choices,
                evaluation_criteria
            )
            events.append(choices_evaluated_event)

        return events

    async def make_decision(self, event: Event) -> List[Event]:
        if not hasattr(event, 'utility_value') or not hasattr(event, 'calculation_details'):
            return []

        utility_value = event.utility_value
        calculation_details = event.calculation_details

        instruction = f"""
        You are tasked with making a decision based on calculated utility values from a UtilityEvaluator.
        The goal is to select the decision that maximizes utility. Consider the following details:
        - Utility Value: {utility_value}
        - Calculation Details: {calculation_details}

        Please return the decision made and the influencing factors in the following JSON format:
        {{
            "decision": "<The decision made>",
            "influencing_factors": ["<List of factors influencing the decision>"],
            "target_ids": ["<The string ID of the SocialNetworkInteractor agent>"]
        }}
        """

        result = await self.generate_reaction(instruction)

        decision = result.get('decision', '')
        influencing_factors = result.get('influencing_factors', [])
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("selected_decision", decision)

        events = []
        for target_id in target_ids:
            decision_event = DecisionMadeEvent(self.profile_id, target_id, decision=decision, influencing_factors=influencing_factors)
            events.append(decision_event)

        return events;
