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

class CustomerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "apply_for_loan")
        self.register_event("LoanApprovalEvent", "receive_loan_decision")
        self.register_event("LoanRejectionEvent", "receive_loan_decision")

    async def apply_for_loan(self, event: Event) -> List[Event]:
        # Since the condition is None, proceed directly with the handler logic
        
        # Retrieve required variables
        customer_id = self.profile.get_data("customer_id", "")
        loan_amount = self.profile.get_data("loan_amount", 0.0)
        economic_conditions = await self.get_env_data("economic_conditions", "stable")
        
        # Prepare the instruction for the LLM
        instruction = """You are processing a loan application for a customer. 
        Please decide which bank(s) to send the loan application to based on the current economic conditions.
        Return the information in the following JSON format:
        
        {
        "target_ids": ["<The string ID of the Bank agent(s)>"]
        }
        
        Ensure that the target_ids can be a single ID or a list of IDs. Use the provided agent relationships to determine the appropriate target(s).
        """
        
        # Current context as observation
        observation = f"Customer ID: {customer_id}, Loan Amount: {loan_amount}, Economic Conditions: {economic_conditions}"
        
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM's JSON response
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Prepare and send LoanApplicationEvent to each BankAgent
        events = []
        for target_id in target_ids:
            loan_application_event = LoanApplicationEvent(
                self.profile_id, target_id, customer_id=customer_id, loan_amount=loan_amount, economic_conditions=economic_conditions
            )
            events.append(loan_application_event)
        
        return events

    async def receive_loan_decision(self, event: Event) -> List[Event]:
        # Condition Check
        if event.__class__.__name__ not in ["LoanApprovalEvent", "LoanRejectionEvent"]:
            return []
        
        # Data Access
        customer_id = event.customer_id
        loan_status = "approved" if event.__class__.__name__ == "LoanApprovalEvent" else "rejected"
        
        # Decision Making
        observation = f"Event: {event.__class__.__name__}, Customer ID: {customer_id}, Loan Status: {loan_status}"
        instruction = """The CustomerAgent should update its financial status based on the loan decision received.
        Please return the information in the following JSON format:
        
        {
        "financial_status": "<Updated financial status of the customer>",
        "target_ids": ["<The string ID of the EnvAgent or other target>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        # Data Modification
        financial_status = result.get('financial_status', None)
        if financial_status is not None:
            self.profile.update_data("financial_status", financial_status)
        
        # Response Processing
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Prepare and send the LoanDecisionProcessedEvent to the next target(s)
        events = []
        for target_id in target_ids:
            processed_event = LoanDecisionProcessedEvent(self.profile_id, target_id, customer_id, loan_status)
            events.append(processed_event)
        
        return events