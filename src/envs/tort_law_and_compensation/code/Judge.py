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

class Judge(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("CompensationRequestEvent", "evaluate_request")
        self.register_event("DefensePreparedEvent", "evaluate_defense")
        self.register_event("RequestEvaluationEvent", "make_decision")
        self.register_event("DefenseEvaluationEvent", "make_decision")

    async def evaluate_request(self, event: Event) -> List[Event]:
        # Mark event as received
        received_events = self.profile.get_data('received_events', [])
        if "CompensationRequestEvent" not in received_events:
            received_events.append("CompensationRequestEvent")
        self.profile.update_data('received_events', received_events)

        # Check if both CompensationRequestEvent and DefensePreparedEvent have been received
        if "DefensePreparedEvent" not in received_events:
            return []  # Return an empty list if the condition is not met

        # Retrieve event data
        compensation_amount = event.compensation_amount
        damage_description = event.damage_description
        evidence_list = event.evidence_list

        # Construct observation and instruction for decision making
        observation = f"Compensation Amount: {compensation_amount}, Damage Description: {damage_description}, Evidence List: {evidence_list}"
        instruction = """Evaluate the compensation request based on the provided evidence and damage description. 
        Consider legal principles and precedents to determine the evaluation status and notes.
        Return the information in the following JSON format:

        {
        "evaluation_status": "<Status of the evaluation process, can be 'pending', 'completed', 'failed'>",
        "evaluation_notes": "<Notes and observations made during the evaluation>"
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract evaluation results and target_ids
        evaluation_status = result.get('evaluation_status', None)
        evaluation_notes = result.get('evaluation_notes', None)

        # Update agent's state with evaluation results
        self.profile.update_data("evaluation_status_request", "completed")
        self.profile.update_data("evaluation_notes_request", evaluation_notes)

        # Prepare and send RequestEvaluationEvent to specified targets
        events = []
        evaluation_event = RequestEvaluationEvent(self.profile_id, self.profile_id, evaluation_status, evaluation_notes)
        events.append(evaluation_event)

        return events

    async def evaluate_defense(self, event: Event) -> List[Event]:
        # Mark event as received
        received_events = self.profile.get_data('received_events', [])
        if "DefensePreparedEvent" not in received_events:
            received_events.append("DefensePreparedEvent")
        self.profile.update_data('received_events', received_events)

        # Check if both CompensationRequestEvent and DefensePreparedEvent have been received
        if "CompensationRequestEvent" not in received_events:
            return []

        # Retrieve required variables from the event
        liability_reduction_argument = getattr(event, "liability_reduction_argument", "")
        counter_evidence_list = getattr(event, "counter_evidence_list", [])

        # Prepare the observation for the LLM
        observation = (
            f"Liability Reduction Argument: {liability_reduction_argument}\n"
            f"Counter Evidence List: {counter_evidence_list}"
        )

        # Instruction for generating a reaction to the event
        instruction = """Evaluate the defense arguments using the provided liability_reduction_argument and counter_evidence_list.
        Based on the evaluation, return the evaluation_status and evaluation_notes.
        Also, specify the target_ids for the next action, which can be a single ID or a list of IDs.
        Please return the information in the following JSON format:
        
        {
        "evaluation_status": "<Status of the defense evaluation process, can be 'pending', 'completed', 'failed'>",
        "evaluation_notes": "<Notes and observations made during the defense evaluation>"
        }
        """

        # Generate a reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Update agent profile with evaluation results
        evaluation_status = result.get("evaluation_status", "completed")
        evaluation_notes = result.get("evaluation_notes", "")
        self.profile.update_data("evaluation_status_defense", "completed")
        self.profile.update_data("evaluation_notes_defense", evaluation_notes)

        # Prepare and send DefenseEvaluationEvent to the specified target(s)
        events = []
        defense_evaluation_event = DefenseEvaluationEvent(self.profile_id, self.profile_id, evaluation_status, evaluation_notes)
        events.append(defense_evaluation_event)

        return events

    async def make_decision(self, event: Event) -> List[Event]:
        # Retrieve evaluation statuses from agent profile
        evaluation_status_request = self.profile.get_data("evaluation_status_request", "pending")
        evaluation_status_defense = self.profile.get_data("evaluation_status_defense", "pending")

        # Ensure both evaluation statuses are marked as 'completed'
        if evaluation_status_request != "completed" or evaluation_status_defense != "completed":
            return []

        # Prepare observation and instruction for decision making
        observation = f"Evaluation status request: {evaluation_status_request}, Evaluation status defense: {evaluation_status_defense}"
        instruction = """Please make a decision based on the completed evaluations of both the compensation request and the defense arguments.
        Return the outcome of the decision, amount of compensation awarded, and completion status in the following JSON format:

        {
        "decision_outcome": "<Outcome of the case decision>",
        "compensation_awarded": <Amount of compensation awarded to the plaintiff>,
        "completion_status": "<Status indicating completion of the case>",
        "target_ids": ["ENV"]
        }
        """

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        decision_outcome = result.get("decision_outcome", "")
        compensation_awarded = result.get("compensation_awarded", 0.0)
        completion_status = result.get("completion_status", "completed")
        target_ids = result.get("target_ids", ["ENV"])

        # Create and dispatch DecisionMadeEvent
        events = []
        for target_id in target_ids:
            decision_event = DecisionMadeEvent(self.profile_id, target_id, decision_outcome, compensation_awarded, completion_status)
            events.append(decision_event)

        return events