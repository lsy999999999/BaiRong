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

class ConsumerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "spend_money")

    async def spend_money(self, event: Event) -> List[Event]:
        # Check if the consumer has available funds to spend
        available_funds = self.profile.get_data("available_funds", 0.0)
        spending_amount = self.profile.get_data("spending_amount", 0.0)
    
        if available_funds < spending_amount:
            return []
    
        # Generate reaction to determine target_ids and revenue_amount
        observation = f"Consumer ID: {self.profile.get_data('consumer_id', '')}, Spending Amount: {spending_amount}"
        instruction = """Please analyze the consumer's spending behavior and determine which companies are affected by this spending.
        Return the data in the following JSON format:
        
        {
            "target_ids": ["<List of company IDs affected by the spending>"],
            "revenue_amount": <Amount of revenue generated from the consumer spending>
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
    
        target_ids = result.get('target_ids', [])
        revenue_amount = result.get('revenue_amount', 0.0)
    
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update consumer's available funds
        new_available_funds = available_funds - spending_amount
        self.profile.update_data("available_funds", new_available_funds)
    
        # Create events for each target company
        events = []
        consumer_id = self.profile.get_data("consumer_id", "")
        from_agent_id = self.profile.get_data("agent_id", "")  # Assuming agent_id is stored in profile
        for company_id in target_ids:
            revenue_event = RevenueGeneratedEvent(from_agent_id=from_agent_id, to_agent_id=company_id, consumer_id=consumer_id, company_id=company_id, revenue_amount=revenue_amount)
            events.append(revenue_event)
    
        return events