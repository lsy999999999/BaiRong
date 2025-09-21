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

class ResourceMiner(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "start_workflow")
        self.register_event("ResourceAvailabilityEvent", "observe_environment")
        self.register_event("LandOwnershipEvent", "decide_investment_strategy")
        self.register_event("ResolutionOutcomeEvent", "process_resolution_outcome")

    async def start_workflow(self, event: Event) -> List[Event]:
        # Condition check implementation
        if self.action_condition is not None and not self.action_condition:
            return []
    
        # Data access
        miner_id = self.profile.agent_id
    
        # Decision Making
        instruction = f"""
        The ResourceMiner with ID {miner_id} is initializing its workflow. 
        Please generate the next step for the ResourceMiner, which involves transitioning to the 'observe_environment' state.
        Please return the information in the following JSON format:
    
        {{
        "target_ids": ["{miner_id}"]
        }}
        """
        result = await self.generate_reaction(instruction)
        target_ids = result.get('target_ids', [miner_id])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Response Processing
        events = []
        for target_id in target_ids:
            resource_availability_event = ResourceAvailabilityEvent(self.profile_id, target_id)
            events.append(resource_availability_event)
        
        return events

    async def observe_environment(self, event: Event) -> List[Event]:
        # No condition check required as the condition is null
    
        # Retrieve the global map state from the environment
        global_map_state = await self.get_env_data("global_map_state", {})
    
        # Update the agent's observed state with the current global map state
        self.profile.update_data("observed_state", global_map_state)
    
        # Generate a reaction to decide the next action based on the observed state
        instruction = f"""
        The ResourceMiner has observed the current state of the environment, including resource availability and land ownership.
        Please decide the next action for the ResourceMiner based on the observed state.
        The observed state is: {global_map_state}.
        Please return the information in the following JSON format:
    
        {{
            "target_ids": ["{self.profile.agent_id}"],
            "action": "decide_investment_strategy"
        }}
        """
        result = await self.generate_reaction(instruction, observation=str(global_map_state))
        
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare and send the LandOwnershipEvent to the ResourceMiner
        events = []
        for target_id in target_ids:
            land_ownership_event = LandOwnershipEvent(self.profile_id, target_id)
            events.append(land_ownership_event)
        
        return events

    async def process_resolution_outcome(self, event: Event) -> List[Event]:
        if event.__class__.__name__ == "ResolutionOutcomeEvent":
            winner_id = event.winner_id
            grid_cell_id = event.grid_cell_id
            investment_amount = event.investment_amount
            tie_resolution = event.tie_resolution
            miner_id = event.miner_id
    
            instruction = f"""
            Process the outcome of the resolution process for the ResourceMiner with ID {miner_id} based on the event details:
            - Winner ID: {winner_id}
            - Grid Cell ID: {grid_cell_id}
            - Investment Amount: {investment_amount}
            - Tie Resolution: {tie_resolution}
            Update the current state of the ResourceMiner accordingly.
            Please return the updated state in the following JSON format:
            {{
                "current_state": "<Updated state of the ResourceMiner>",
                "target_ids": ["ENV"]
            }}
            """
            result = await self.generate_reaction(instruction)
            current_state = result.get('current_state', None)
            target_ids = result.get('target_ids', None)
            if not isinstance(target_ids, list):
                target_ids = [target_ids]
    
            self.profile.update_data("current_state", current_state)
            events = []
            for target_id in target_ids:
                completion_status = "success" if current_state == "won" else "failure"
                activities_completed = "process_resolution_outcome"
                activity_completion_event = ActivityCompletionEvent(self.profile_id, target_id, completion_status, miner_id, activities_completed)
                events.append(activity_completion_event)
            return events
        else:
            return []

    async def decide_investment_strategy(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "LandOwnershipEvent":
            return []
        
        observed_state = self.profile.get_data("observed_state", None)
        if observed_state is None:
            return []
        
        instruction = f"""
        Based on the observed environment state: {observed_state}, 
        decide the investment strategy for the ResourceMiner agent. 
        The strategy should include target grid cells and investment amounts.
        Please return the information in the following JSON format:
    
        {{
        "investment_strategy": "<Decided investment strategy>",
        "target_ids": ["<The string ID of the grid cell(s) being contested or maintained>"],
        "miner_id": "{self.profile.agent_id}",
        "grid_cell_id": "<The string ID of the grid cell being contested or maintained>",
        "investment_amount": "<The amount of energy invested>"
        }}
        """
        
        result = await self.generate_reaction(instruction)
        investment_strategy = result.get('investment_strategy', None)
        target_ids = result.get('target_ids', None)
        miner_id = result.get('miner_id', None)
        grid_cell_id = result.get('grid_cell_id', None)
        investment_amount = result.get('investment_amount', 0)
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        events = []
        for target_id in target_ids:
            investment_strategy_event = InvestmentStrategyEvent(self.profile_id, target_id, miner_id=miner_id, grid_cell_id=grid_cell_id, investment_amount=investment_amount)
            events.append(investment_strategy_event)
        
        return events