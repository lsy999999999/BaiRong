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


class HealthcareFacility(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("BehaviorAdjustedEvent", "provide_healthcare_services")
        self.register_event("InterventionDeployedEvent", "allocate_resources")

    async def provide_healthcare_services(self, event: Event) -> List[Event]:
        # Ensure the event is of type 'BehaviorAdjustedEvent'
        if not isinstance(event, BehaviorAdjustedEvent):
            return []

        # Access required variables from the event
        individual_id = event.individual_id
        behavior_changes = event.behavior_changes

        # Access and update agent's current occupancy
        current_occupancy = self.profile.get_data("current_occupancy", 0)
        capacity = self.profile.get_data("capacity", 0)
        if current_occupancy < capacity:
            new_occupancy = current_occupancy + 1
            self.profile.update_data("current_occupancy", new_occupancy)
        else:
            return []

        # Prepare instruction for the LLM to decide on target_ids and service type
        observation = f"Healthcare facility current occupancy: {new_occupancy}, behavior changes: {behavior_changes}"
        instruction = """You are managing a healthcare facility providing services to individuals. 
        Based on the current occupancy and behavior changes, determine the type of healthcare service provided. 
        Also, decide the target_ids for sending the HealthcareServiceProvidedEvent. 
        The target_ids should be a single string ID or a list of IDs, with 'ENV' as the target_id for terminal events.
        Please return the information in the following JSON format:

        {
        "service_type": "<Type of healthcare service provided>",
        "target_ids": ["<The string ID of the target agent(s)>"]
        }
        """

        # Generate reaction from the LLM
        result = await self.generate_reaction(instruction, observation)
        service_type = result.get('service_type', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and send the HealthcareServiceProvidedEvent to each target_id
        events = []
        for target_id in target_ids:
            healthcare_event = HealthcareServiceProvidedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                healthcare_facility_id=self.profile_id,
                service_type=service_type,
                completion_status="completed"
            )
            events.append(healthcare_event)

        return events

    async def allocate_resources(self, event: Event) -> List[Event]:
        if not isinstance(event, InterventionDeployedEvent):
            return []

        intervention_type = event.intervention_type
        targeted_healthcare_facility_id = event.healthcare_facility_id

        # Generate reaction to decide on resource allocation and target healthcare facilities
        instruction = f"""
        The healthcare facility needs to allocate resources based on the intervention type received.
        The intervention type is: {intervention_type}
        
        Please return the target_ids, which can be a single ID or a list of IDs, indicating which healthcare facilities should respond to the intervention.
        Additionally, provide the resources_allocated dictionary detailing the allocation of resources and the completion_status of the resource allocation process.
        The JSON response should be in the following format:
        {{
            "target_ids": ["<Healthcare facility ID(s)>"],
            "resources_allocated": {{<Resource allocation details as a dictionary>}},
            "completion_status": "<Status of the resource allocation process>"
        }}
        """

        result = await self.generate_reaction(instruction)
        target_ids = result.get('target_ids', [])
        resources_allocated = result.get('resources_allocated', {})
        completion_status = result.get('completion_status', 'completed')

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            if target_id:
                # Update the resource level for the targeted healthcare facility
                targeted_profile = self.relationship_manager.get_agent_by_id(target_id)
                if targeted_profile:
                    targeted_profile.update_data("resource_level", resources_allocated)

                    # Send ResourcesAllocatedEvent to the environment agent
                    resources_allocated_event = ResourcesAllocatedEvent(
                        from_agent_id=self.profile_id,
                        to_agent_id=target_id,
                        healthcare_facility_id=targeted_healthcare_facility_id,
                        resources_allocated=resources_allocated,
                        completion_status=completion_status
                    )
                    events.append(resources_allocated_event)

        return events