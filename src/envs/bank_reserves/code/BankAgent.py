from typing import Any, List, Optional
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

class BankAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("LoanApplicationEvent", "evaluate_loan_application")
        self.register_event("ReserveAdjustmentEvent", "manage_reserves")

    async def evaluate_loan_application(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "LoanApplicationEvent":
            return []

        customer_id = event.customer_id
        loan_amount = event.loan_amount
        reserve_level = self.profile.get_data("reserve_level", 0.0)
        reserve_requirement = await self.get_env_data("reserve_requirement", 0.0)

        observation = f"Loan Amount: {loan_amount}, Reserve Level: {reserve_level}, Reserve Requirement: {reserve_requirement}"
        instruction = """Evaluate the loan application based on the current reserve levels compared to reserve requirements. 
        Approve the loan if the reserve level is above the reserve requirement. Reject the loan if reserves are insufficient. 
        Consider partial approval if reserves are marginally below the requirement. 
        Please return the decision status ('approved' or 'rejected') and the target_ids in the following JSON format:

        {
        "decision_status": "<approved/rejected>",
        "target_ids": ["<CustomerAgent ID>", "<BankAgent ID for reserve adjustment if needed>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        decision_status = result.get('decision_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("decision_status", decision_status)

        events = []
        for target_id in target_ids:
            if decision_status == "rejected":
                rejection_reason = "insufficient_reserves"
                loan_rejection_event = LoanRejectionEvent(self.profile_id, target_id, customer_id, rejection_reason)
                events.append(loan_rejection_event)
            
            if target_id == self.profile_id:
                adjustment_amount = -min(loan_amount, reserve_level) if decision_status == "approved" else 0
                new_reserve_level = reserve_level + adjustment_amount
                reserve_adjustment_event = ReserveAdjustmentEvent(self.profile_id, target_id, self.profile_id, adjustment_amount, new_reserve_level)
                events.append(reserve_adjustment_event)

        return events

    async def manage_reserves(self, event: Event) -> List[Event]:
        loan_decision_completed = self.profile.get_data("decision_status", None) in ["approved", "rejected"]
        if not loan_decision_completed:
            return []

        bank_id = event.bank_id
        if bank_id != self.profile_id:
            return []

        adjustment_amount = event.adjustment_amount
        new_reserve_level = event.new_reserve_level

        self.profile.update_data("reserve_level", new_reserve_level)

        instruction = """
        The bank has adjusted its reserves post loan decision. 
        Please determine the target_id(s) for sending the ReserveManagementCompletedEvent.
        Ensure the response format is JSON with a 'target_ids' field containing the ID(s) as a list.
        """
        observation = f"Bank ID: {bank_id}, New Reserve Level: {new_reserve_level}"
        result = await self.generate_reaction(instruction, observation)

        # target_ids = result.get('target_ids', None)
        # if not isinstance(target_ids, list):
        #     target_ids = [target_ids]

        target_ids = ["ENV"]

        events = []
        for target_id in target_ids:
            completion_event = ReserveManagementCompletedEvent(
                self.profile_id, target_id, bank_id=bank_id, completion_status="success"
            )
            events.append(completion_event)

        return events