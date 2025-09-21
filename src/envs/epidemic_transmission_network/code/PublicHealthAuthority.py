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

class PublicHealthAuthority(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_epidemiological_data")
        self.register_event("EpidemiologicalDataEvaluatedEvent", "deploy_interventions")

    async def evaluate_epidemiological_data(self, event: Event) -> List[Event]:
        # Retrieve epidemiological data from environment
        epidemiological_data = await self.get_env_data("epidemiological_data", {})
    
        # Generate reaction to determine intervention strategies
        instruction = f"""
        The public health authority needs to evaluate the current state of the epidemic based on the provided epidemiological data.
        Please return a list of potential intervention strategies in the following JSON format:
        
        {{
            "intervention_strategies": ["<List of intervention strategies>"],
            "target_ids": ["<The string ID of the PublicHealthAuthority agent>"]
        }}
        """
        result = await self.generate_reaction(instruction, observation=epidemiological_data)
        
        # Update agent's profile with intervention strategies
        intervention_strategies = result.get('intervention_strategies', [])
        self.profile.update_data("intervention_strategies", intervention_strategies)
        
        # Prepare target_ids for event sending
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Create and send EpidemiologicalDataEvaluatedEvent
        events = []
        for target_id in target_ids:
            evaluated_event = EpidemiologicalDataEvaluatedEvent(self.profile_id, target_id, public_health_authority_id=int(self.profile_id), epidemiological_data=epidemiological_data)
            events.append(evaluated_event)
        
        return events

    async def deploy_interventions(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "EpidemiologicalDataEvaluatedEvent":
            return []

        # Ensure intervention_type is not None before proceeding
        instruction = f"""
        The PublicHealthAuthority agent has received an EpidemiologicalDataEvaluatedEvent. 
        Based on the evaluated data, please determine and return the intervention strategies to be deployed. 
        The response should be in the following JSON format:
        
        {{
        "intervention_type": "<Type of intervention to be deployed>",
        "target_ids": ["<List of target IDs for the intervention>"]
        }}
        
        Ensure that the intervention types and target IDs are strategic and effective for controlling the disease spread.
        """
        result = await self.generate_reaction(instruction, observation=event.epidemiological_data)
        intervention_type = result.get('intervention_type', None)
        if not intervention_type:
            return []

        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        active_interventions = self.profile.get_data("active_interventions", [])
        active_interventions.extend([(intervention_type, target_id) for target_id in target_ids])
        self.profile.update_data("active_interventions", active_interventions)
    
        events = []
        for target_id in target_ids:
            intervention_deployed_event = InterventionDeployedEvent(
                self.profile_id, 
                target_id, 
                public_health_authority_id=int(self.profile_id), 
                intervention_type=intervention_type, 
                target_individual_id=target_id
            )
            events.append(intervention_deployed_event)
        
        return events