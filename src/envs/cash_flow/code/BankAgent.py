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


class BankAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("CashFlowEvaluatedEvent", "assess_credit_rating")
        self.register_event("LoanApplicationEvent", "process_loan_application")

    async def assess_credit_rating(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ != "CashFlowEvaluatedEvent":
            return []

        # Retrieve required variables from the event
        company_id = event.company_id
        cash_flow_status = event.cash_flow_status

        # Generate reaction to assess credit rating
        observation = f"Company ID: {company_id}, Cash Flow Status: {cash_flow_status}"
        instruction = """
        Assess the creditworthiness of the company based on its cash flow status.
        Determine the appropriate credit rating and identify the company or companies to notify.
        Please return the information in the following JSON format:

        {
        "credit_rating": "<Determined credit rating>",
        "target_ids": ["<The string ID(s) of the CompanyAgent(s)>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        # Extract results from the LLM's response
        credit_rating = result.get('credit_rating', 'unrated')
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the CreditRatingAssessedEvent to the relevant CompanyAgent(s)
        events = []
        for target_id in target_ids:
            credit_rating_event = CreditRatingAssessedEvent(self.profile_id, target_id, company_id=company_id, credit_rating=credit_rating)
            events.append(credit_rating_event)

        return events

    async def process_loan_application(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ != "LoanApplicationEvent":
            return []

        # Extract required variables from the event
        company_id = event.company_id
        loan_amount = event.loan_amount
        credit_rating = event.credit_rating

        # Construct observation for the LLM
        observation = f"Company ID: {company_id}, Loan Amount: {loan_amount}, Credit Rating: {credit_rating}"

        # Instruction for the LLM
        instruction = """Review the loan application details and decide whether to approve or reject the loan based on the credit rating and financial health assessment. 
        Please return the decision in the following JSON format:

        {
        "loan_decision": "<approved or rejected>",
        "approved_loan_amount": "<float value of approved loan amount if applicable>",
        "interest_rate": "<float value of interest rate if loan is approved>",
        "rejection_reason": "<reason for rejection if applicable>",
        "target_ids": ["<The string ID of the CompanyAgent or 'ENV' for terminal events>"]
        }
        """

        # Generate reaction from LLM
        result = await self.generate_reaction(instruction, observation)

        loan_decision = result.get('loan_decision', None)
        approved_loan_amount = result.get('approved_loan_amount', 0.0)
        interest_rate = result.get('interest_rate', 0.0)
        rejection_reason = result.get('rejection_reason', "unknown")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state based on the decision
        self.profile.update_data("loan_decision", loan_decision)
        self.profile.update_data("approved_loan_amount", approved_loan_amount)

        # Prepare outgoing events
        events = []
        if loan_decision == "approved":
            for target_id in target_ids:
                loan_approved_event = LoanApprovedEvent(self.profile_id, target_id, company_id, approved_loan_amount, interest_rate)
                events.append(loan_approved_event)
        elif loan_decision == "rejected":
            for target_id in target_ids:
                loan_rejected_event = LoanRejectedEvent(self.profile_id, "ENV", company_id, rejection_reason)
                events.append(loan_rejected_event)

        return events