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
        self.register_event("EvidenceSubmittedEvent", "evaluate_evidence")
        self.register_event("DefensePreparedEvent", "evaluate_defense")
        self.register_event("EvidenceEvaluationEvent", "make_decision")
        self.register_event("DefenseEvaluationEvent", "make_decision")

    async def evaluate_evidence(self, event: Event) -> List[Event]:
        if not isinstance(event, EvidenceSubmittedEvent):
            return []

        evidence_details = event.evidence_details
        plaintiff_id = event.plaintiff_id
        case_id = event.case_id

        observation = f"Evaluating evidence for case {case_id} submitted by plaintiff {plaintiff_id}."
        instruction = """
        You are a Judge evaluating evidence in a legal case of unjust enrichment. Analyze the evidence details provided and determine the validity and relevance of the evidence. 
        Based on your evaluation, decide on the result of the evidence evaluation. 
        Please return the information in the following JSON format:

        {
        "evidence_evaluation_result": "<Result of the evaluation>",
        "target_ids": ["<The string ID of the Judge agent for the next action>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        evidence_evaluation_result = result.get('evidence_evaluation_result', "pending")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        if target_ids:
            self.profile.update_data("evidence_evaluation_result", evidence_evaluation_result)
            for target_id in target_ids:
                evaluation_event = EvidenceEvaluationEvent(self.profile_id, target_id, evidence_evaluation_result, self.profile_id, case_id)
                events.append(evaluation_event)

        return events

    async def evaluate_defense(self, event: Event) -> List[Event]:
        if not isinstance(event, DefensePreparedEvent):
            return []

        defense_arguments = event.defense_arguments
        defendant_id = event.defendant_id
        case_id = event.case_id

        observation = f"Defense Arguments: {defense_arguments}, Defendant ID: {defendant_id}, Case ID: {case_id}"
        instruction = """
        Evaluate the defense arguments provided by the Defendant in the context of the legal case of unjust enrichment.
        Determine the validity and relevance of these arguments in response to the Plaintiff's claims.
        Please return the evaluation result and the target IDs for the next action in the following JSON format:

        {
        "evaluation_result": "<Result of the defense evaluation>",
        "target_ids": ["<The string ID(s) of the next target agent(s)>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        evaluation_result = result.get('evaluation_result', "pending")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        if target_ids:
            self.profile.update_data("defense_evaluation_result", evaluation_result)
            for target_id in target_ids:
                defense_evaluation_event = DefenseEvaluationEvent(
                    self.profile_id,
                    target_id,
                    evaluation_result=evaluation_result,
                    judge_id=self.profile_id,
                    case_id=case_id
                )
                events.append(defense_evaluation_event)

        return events

    async def make_decision(self, event: Event) -> List[Event]:
        if isinstance(event, EvidenceEvaluationEvent):
            self.profile.update_data("evidence_evaluation_result", event.evaluation_result)

        if isinstance(event, DefenseEvaluationEvent):
            self.profile.update_data("defense_evaluation_result", event.evaluation_result)

        evidence_evaluation_result = self.profile.get_data("evidence_evaluation_result", "pending")
        defense_evaluation_result = self.profile.get_data("defense_evaluation_result", "pending")

        if evidence_evaluation_result == "pending" or defense_evaluation_result == "pending":
            return []

        judge_id = self.profile.get_data("judge_id", "")
        case_id = event.case_id  # Retrieve case_id from the event

        observation = f"Evidence Result: {evidence_evaluation_result}, Defense Result: {defense_evaluation_result}"
        instruction = """Evaluate the case of unjust enrichment based on the provided evidence and defense results.
        Determine whether unjust enrichment occurred and decide on restitution or compensation.
        Return the information in the following JSON format:

        {
        "judgment_result": "<Final decision on the case>",
        "completion_status": "<Status indicating the conclusion of the simulation>",
        "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        judgment_result = result.get('judgment_result', "undecided")
        completion_status = result.get('completion_status', "incomplete")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            judgment_event = JudgmentEvent(self.profile_id, target_id, judgment_result, judge_id, case_id, completion_status)
            events.append(judgment_event)

        return events