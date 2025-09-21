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

class DecisionMakerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "gather_information")
        self.register_event("ExternalFactorsSimulatedEvent", "evaluate_options")
        self.register_event("AlternativesPresentedEvent", "make_decision")

    async def gather_information(self, event: Event) -> List[Event]:
        # Since the condition is 'null', proceed without condition check

        # Access event data
        # source = event.fields.get('source', 'EnvironmentAgent')
        # information_content = event.fields.get('information_content', "")

        # Update agent's profile with collected information
        # collected_information = f"Source: ENV, Content: {information_content}"
        # self.profile.update_data("collected_information", collected_information)
        self.profile.update_data("InformationGatheredEvent_received", True)

        # Prepare instruction for LLM to generate reaction
        # observation = f"Collected Information: {collected_information}"
        instruction = """
        Assume that you received information from the environment.
        Please process the collected information and decide on the target agents to communicate this information to. 
        Your response should be in the following JSON format:

        {
        "collected_information": "<Collected information content>",
        "processed_information": "<Processed information content>",
        "target_ids": ["<The string ID(s) of the target agents>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction)

        # Parse LLM response
        collected_information = result.get('collected_information', "")
        self.profile.update_data("collected_information", collected_information)
        processed_information = result.get('processed_information', "")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and send InformationGatheredEvent to each target
        events = []
        for target_id in target_ids:
            information_event = InformationGatheredEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                source=self.profile_id,
                information_content=processed_information,
                collected_information=collected_information
            )
            events.append(information_event)

        return events

    async def evaluate_options(self, event: Event) -> List[Event]:
        # Check if the InformationGatheredEvent has been received
        if not self.profile.get_data("InformationGatheredEvent_received", False):
            return []

        # Retrieve necessary data from the agent and event
        collected_information = self.profile.get_data("collected_information", "")
        factor_type = event.get('factor_type', "")
        impact_level = event.get('impact_level', "0")

        # Craft the instruction for the LLM
        instruction = f"""
        Evaluate the options based on the following criteria: cost, utility, and risk. 
        Use the collected information: '{collected_information}' to inform your decision. 
        Please return the results in the following JSON format:

        {{
            "evaluation_criteria": "<The criteria used for evaluation>",
            "evaluation_result": "<Result of the evaluation process>",
            "target_ids": ["<The string ID(s) of the AlternativeOptionsAgent(s)>"]
        }}
        """

        # Generate reaction using LLM
        observation = f"Factor type: {factor_type}, Impact level: {impact_level}"
        result = await self.generate_reaction(instruction, observation)

        # Extract the evaluation result and target_ids from the LLM response
        evaluation_result = result.get('evaluation_result', "pending")
        evaluation_criteria = result.get('evaluation_criteria', {})
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the evaluation result
        self.profile.update_data("evaluation_result", evaluation_result)
        self.profile.update_data("OptionsEvaluatedEvent_received", True)

        # Prepare and send OptionsEvaluatedEvent to the appropriate AlternativeOptionsAgent(s)
        events = []
        for target_id in target_ids:
            options_evaluated_event = OptionsEvaluatedEvent(
                from_agent_id=self.profile_id, 
                to_agent_id=target_id, 
                option_id=target_id, 
                evaluation_criteria=evaluation_criteria, 
                evaluation_result=evaluation_result
            )
            events.append(options_evaluated_event)

        return events

    async def make_decision(self, event: Event) -> List[Event]:
        # Ensure all required events have been received
        if not self.profile.get_data("OptionsEvaluatedEvent_received", False):
            return []

        # Access required data
        evaluation_result = self.profile.get_data("evaluation_result", "default")
        alternative_id = event.get('alternative_id', "")
        alternative_details = event.get('alternative_details', {})

        # Generate decision using LLM
        instruction = """
        The Decision Maker Agent is making a final decision based on the evaluation of options.
        Consider the costs, utilities, and risks associated with each alternative. 
        Please provide the decision outcome and specify target_ids for the next action. 
        Return the information in the following JSON format:

        {
        "decision_id": "<Unique identifier for the decision made>",
        "decision_result": "<Outcome of the decision-making process>",
        "target_ids": ["ENV"]
        }
        """
        observation = f"Evaluation result: {evaluation_result}, Alternative ID: {alternative_id}, Alternative details: {alternative_details}"
        result = await self.generate_reaction(instruction, observation)

        # Extract results from LLM response
        decision_id = result.get('decision_id', None)
        decision_result = result.get('decision_result', None)
        target_ids = ["ENV"]

        # Update agent profile with decision details
        self.profile.update_data("decision_id", decision_id)
        self.profile.update_data("decision_result", decision_result)

        # Prepare and send DecisionMadeEvent
        events = []
        for target_id in target_ids:
            decision_event = DecisionMadeEvent(self.profile_id, target_id, decision_id, decision_result)
            events.append(decision_event)

        return events