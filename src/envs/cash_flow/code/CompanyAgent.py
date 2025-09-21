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

class CompanyAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_cash_flow")
        self.register_event("CreditRatingAssessedEvent", "apply_for_loan")
        self.register_event("LoanApprovedEvent", "manage_expenses")
        self.register_event("RevenueGeneratedEvent", "manage_expenses")

    async def evaluate_cash_flow(self, event: Event) -> List[Event]:
        # Condition Check: Company has cash reserves to evaluate
        cash_reserves = self.profile.get_data("cash_reserves", 0.0)
        if cash_reserves <= 0:
            return []
    
        # Access required agent data
        debt_levels = self.profile.get_data("debt_levels", 0.0)
        credit_rating = self.profile.get_data("credit_rating", "unrated")
    
        # Generate reaction using LLM
        observation = f"Cash reserves: {cash_reserves}, Debt levels: {debt_levels}, Credit rating: {credit_rating}"
        instruction = """Evaluate the company's cash flow status and determine its readiness for loan applications. 
        Provide the updated cash_flow_status and any changes to the credit_rating. 
        Additionally, specify the target_ids for the BankAgent(s) to send the CashFlowEvaluatedEvent. 
        Return the information in the following JSON format:
        
        {
        "cash_flow_status": "<Updated cash flow status>",
        "credit_rating": "<Updated credit rating>",
        "target_ids": ["<List of BankAgent IDs>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM's JSON response
        cash_flow_status = result.get('cash_flow_status', 'unknown')
        updated_credit_rating = result.get('credit_rating', credit_rating)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile
        self.profile.update_data("cash_flow_status", cash_flow_status)
        self.profile.update_data("credit_rating", updated_credit_rating)
    
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            cash_flow_event = CashFlowEvaluatedEvent(
                self.profile_id,
                target_id,
                company_id=self.profile_id,
                cash_flow_status=cash_flow_status,
                credit_rating=updated_credit_rating
            )
            events.append(cash_flow_event)
    
        return events

    async def manage_expenses(self, event: Event) -> List[Event]:
        # Condition check: Ensure company has revenue from consumer spending
        incoming_revenue = event.revenue_amount if event.__class__.__name__ == "RevenueGeneratedEvent" else 0.0
        if incoming_revenue <= 0:
            return []
    
        # Access required data
        total_expenses = self.profile.get_data("total_expenses", 0.0)
        cash_reserves = self.profile.get_data("cash_reserves", 0.0)
        
        # Prepare observation and instruction for decision making
        observation = f"Incoming revenue: {incoming_revenue}, Total expenses: {total_expenses}, Cash reserves: {cash_reserves}"
        instruction = """Handle the company's expenses including debts and taxes to ensure financial stability. 
        Based on the incoming revenue and current financial status, decide the updated cash reserves and completion status.
        Return the information in the following JSON format:
    
        {
        "cash_reserves": <Updated cash reserves after managing expenses>,
        "completion_status": "<Status indicating completion of expense management>",
        "target_ids": ["ENV"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM response
        updated_cash_reserves = result.get('cash_reserves', cash_reserves)
        completion_status = result.get('completion_status', "completed")
        target_ids = result.get('target_ids', "ENV")
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent data
        self.profile.update_data("cash_reserves", updated_cash_reserves)
        self.profile.update_data("completion_status", completion_status)
    
        # Prepare and send ExpensesManagedEvent to EnvAgent
        events = []
        for target_id in target_ids:
            expenses_event = ExpensesManagedEvent(
                self.profile_id, target_id, 
                company_id=self.profile_id,
                total_expenses=total_expenses,
                completion_status=completion_status
            )
            events.append(expenses_event)
        
        return events

    async def apply_for_loan(self, event: Event) -> List[Event]:
        # Check if the condition to apply for a loan is met
        credit_rating = event.credit_rating
        if credit_rating == "unrated":
            return []
    
        # Retrieve necessary data from the agent's profile and event
        company_id = event.company_id
        loan_amount = self.profile.get_data("loan_amount", 0.0)
    
        # Generate reaction for decision making with instructions for target_ids
        instruction = """
        Please determine the target bank agent(s) for the loan application based on the company's assessed credit rating and financial needs.
        Return the result in the following JSON format:
        {
            "loan_application_status": "<Status of the loan application>",
            "target_ids": ["<The string ID(s) of the BankAgent(s)>"]
        }
        """
        observation = f"Company ID: {company_id}, Credit Rating: {credit_rating}, Loan Amount: {loan_amount}"
        result = await self.generate_reaction(instruction, observation)
    
        # Extract results from the LLM's response
        loan_application_status = result.get('loan_application_status', "pending")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the loan application status in the agent's profile
        self.profile.update_data("loan_application_status", loan_application_status)
    
        # Prepare and send LoanApplicationEvent to each target bank agent
        events = []
        for target_id in target_ids:
            loan_application_event = LoanApplicationEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                company_id=company_id,
                loan_amount=loan_amount,
                credit_rating=credit_rating
            )
            events.append(loan_application_event)
    
        return events