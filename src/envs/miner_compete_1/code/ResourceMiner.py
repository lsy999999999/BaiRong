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

class ResourceMiner(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "observe_global_map")
        self.register_event("MapObservedEvent", "decide_action")
        self.register_event("OccupyLandDecisionEvent", "execute_occupy_or_maintain")
        self.register_event("CompeteLandDecisionEvent", "execute_compete")
        self.register_event("OccupyMaintainSuccessEvent", "exploit_resources")
        self.register_event("CompeteSuccessEvent", "exploit_resources")

    async def observe_global_map(self, event: Event) -> List[Event]:
        instruction = """As a ResourceMiner agent, observe the global map to assess the current state 
        of resources on the grid. After observing, prepare for the strategic action phase. 
        Please provide a JSON response including the updated 'map_state' with resource visibility on the grid 
        and 'target_ids' for agents to initiate the 'decide_action' phase. 
        Make sure to select target agent(s) based on optimal strategic workflow.
        
        Expected JSON response format:
        {
        "map_state": "<A list representing the current state of the grid map>",
        "target_ids": ["<List of agent IDs or a single agent ID>"]
        }
        """
    
        observation = "Observing the current state of the grid and resource availability."
        result = await self.generate_reaction(instruction, observation)
        
        new_map_state = result.get('map_state', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        await self.profile.update_data("map_state", new_map_state)
        
        events = []
        for target_id in target_ids:
            map_observed_event = MapObservedEvent(self.profile_id, target_id)
            events.append(map_observed_event)
    
        return events

    async def decide_action(self, event: Event) -> List[Event]:
        map_state = self.profile.get_data("map_state", None)
        if map_state is None:
            return []
        
        observation = f"Map state: {map_state}"
        instruction = """
        Considering the current map state, generate an action decision to either occupy, maintain, or compete for land ownership. 
        The decision should include the action type (occupy, maintain, compete), energy investment, target cell coordinates, 
        and target_ids for the outgoing action. Output must be in the JSON format:
    
        {
            "action_type": "<occupy/maintain/compete>",
            "energy_investment": <int>,
            "cell_coordinates": "(x,y)",
            "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)
        
        action_type = result.get('action_type')
        energy_investment = result.get('energy_investment', 0)
        cell_coordinates = result.get('cell_coordinates', "(0,0)")
        target_ids = result.get('target_ids', [])
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        events = []
        if action_type in ["occupy", "maintain", "compete"]:
            for target_id in target_ids:
                if action_type in ["occupy", "maintain"]:
                    event = OccupyLandDecisionEvent(
                        self.profile_id,
                        target_id,
                        energy_investment=energy_investment,
                        cell_coordinates=cell_coordinates,
                        previous_owner=self.profile.get_data("previous_owner", "None")
                    )
                elif action_type == "compete":
                    event = CompeteLandDecisionEvent(
                        self.profile_id,
                        target_id,
                        energy_investment=energy_investment,
                        cell_coordinates=cell_coordinates,
                        current_owner=self.profile.get_data("current_owner", "None")
                    )
                
                events.append(event)
        
        return events

    async def execute_occupy_or_maintain(self, event: Event) -> List[Event]:
        cell_coordinates = event.cell_coordinates
        action_executed = self.profile.get_data(f"action_executed_{cell_coordinates}", False)
        if action_executed or not (event.energy_investment and event.cell_coordinates):
            return []
    
        energy_investment = event.energy_investment
        previous_owner = event.previous_owner
    
        observation = f"Energy Investment: {energy_investment}, Cell Coordinates: {cell_coordinates}, Previous Owner: {previous_owner}"
        instruction = """Given the decision to occupy or maintain land ownership:
        If the agent's energy investment exceeds any prior claims, it should occupy or maintain the land. Determine if the occupation/maintenance can be successful based on the current context.
        Return the information in JSON format:
        {
            "success": <true|false>,
            "target_ids": ["<resource agent ID(s)>"]
        }"""
        
        result = await self.generate_reaction(instruction, observation)
        
        success = result.get('success', False)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        self.profile.update_data(f"action_executed_{cell_coordinates}", True)
    
        events = []
        
        if success:
            new_land_status = {"owner": self.profile_id, "cell": cell_coordinates}
            await self.env.update_data("new_land_status", new_land_status)
            
            for target_id in target_ids:
                success_event = OccupyMaintainSuccessEvent(self.profile_id, target_id, self.profile_id, cell_coordinates)
                events.append(success_event)
        
        return events

    async def execute_compete(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "CompeteLandDecisionEvent":
            return []
    
        energy_investment = event.energy_investment
        cell_coordinates = event.cell_coordinates
        current_owner = event.current_owner
        
        if current_owner == self.profile_id:
            return []
    
        already_competed = self.profile.get_data(f"compete_triggered_{cell_coordinates}", False)
        if already_competed:
            return []
    
        observation = f"Competing for cell at {cell_coordinates} with current owner {current_owner}. Energy investment is {energy_investment}."
        instruction = """
        You are about to compete for land ownership. Please decide the outcome of competition based on the current observation.
        Return the outcome in the following JSON format:
    
        {
        "competition_result": {"result": "success" | "failure", "new_owner": "<Agent ID of new owner>"},
        "target_ids": ["<ID of the agent(s) to notify>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)
    
        competition_result = result.get('competition_result', {})
        new_owner = competition_result.get('new_owner', None)
        result_status = competition_result.get('result', None)
        target_ids = result.get('target_ids', [])
    
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        events = []
        self.profile.update_data(f"compete_triggered_{cell_coordinates}", True)
        self.env.update_data("competition_result", competition_result)
    
        if result_status == "success":
            for target_id in target_ids:
                compete_success_event = CompeteSuccessEvent(new_owner, target_id, cell_coordinates)
                events.append(compete_success_event)
    
        return events

    async def exploit_resources(self, event: Event) -> List[Event]:
        new_owner = event.new_owner
        if new_owner != self.profile_id:
            return []

        cell_coordinates = event.cell_coordinates
    
        occupy_maintain_success_received = self.profile.get_data("OccupyMaintainSuccessEvent", False)
        compete_success_received = self.profile.get_data("CompeteSuccessEvent", False)
    
        if not (occupy_maintain_success_received or compete_success_received):
            return []
        
        resource_count = self.profile.get_data("resource_count", 0)
        
        instruction = """You are required to exploit resources from a land where you have secured ownership.
        Based on the secured ownership of land, determine the target to send the ResourceExploitedEvent. 
        Ensure the format is as follows:
        {
            "target_ids": ["<String ID of the EnvAgent or other agents>"]
        }
        """
        
        observation = f"Successfully exploited resources: {resource_count} units from cell at {cell_coordinates}."
        
        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        events = []
        for target_id in target_ids:
            exploit_event = ResourceExploitedEvent(self.profile_id, target_id, resource_count, cell_coordinates, True)
            events.append(exploit_event)
        
        return events