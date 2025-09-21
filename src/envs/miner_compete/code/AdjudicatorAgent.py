from typing import Any, List, Optional
import json
import asyncio
from loguru import logger
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import *

class AdjudicatorAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_resolution")
        self.register_event("InvestmentStrategyEvent", "resolve_investment_outcome")

    async def initiate_resolution(self, event: Event) -> List[Event]:
        if event.__class__.__name__ == "StartEvent":
            instruction = f"""
            The AdjudicatorAgent has received a 'StartEvent' to initiate the resolution process for contested land.
            The resolution process determines the outcome of land ownership disputes among miners.
            Please provide the necessary information in the following JSON format:
            
            {{
                "target_ids": ["<The string ID of the ResourceMiner agent(s) to receive the resolution outcome>"]
            }}
            
            Ensure that 'target_ids' can be a single ID or a list of IDs.
            """
            result = await self.generate_reaction(instruction)
            
            target_ids = result.get('target_ids', [])
            if not isinstance(target_ids, list):
                target_ids = [target_ids]
            
            events = []
            for target_id in target_ids:
                resolution_event = ResolutionOutcomeEvent(self.profile_id, target_id)
                events.append(resolution_event)
            
            return events
        else:
            return []

    async def resolve_investment_outcome(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "InvestmentStrategyEvent":
            return []
    
        miner_id = event.miner_id
        grid_cell_id = event.grid_cell_id
        investment_amount = event.investment_amount
    
        instruction = f"""
        Resolve the investment competition for the grid cell {grid_cell_id} contested by the miner {miner_id}.
        The investment amount is {investment_amount}. Determine the winner based on the highest investment.
        In case of a tie, randomly select a winner. Return the resolution outcome in the following JSON format:
        
        {{
            "resolution_outcome": {{
                "winner_id": "<The string ID of the winning miner>",
                "grid_cell_id": "<The string ID of the contested grid cell>",
                "investment_amount": "<The investment amount of the winning miner>",
                "tie_resolution": "<True if the outcome was resolved due to a tie, False otherwise>"
            }},
            "target_ids": ["<The string ID of the ResourceMiner to send the outcome to>"]
        }}
        """
        
        result = await self.generate_reaction(instruction)
        resolution_outcome = result.get('resolution_outcome', {})
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        events = []
        for target_id in target_ids:
            winner_id = resolution_outcome.get('winner_id', '')
            investment_amount = resolution_outcome.get('investment_amount', 0)
            tie_resolution = resolution_outcome.get('tie_resolution', False)
            resolution_event = ResolutionOutcomeEvent(self.profile_id, target_id, winner_id, grid_cell_id, investment_amount, tie_resolution)
            events.append(resolution_event)
        
        return events