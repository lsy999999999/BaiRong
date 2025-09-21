from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class HealthcareSystemAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "allocate_healthcare_resources")
        self.register_event("PolicyImplementationEvent", "allocate_healthcare_resources")
        self.register_event("HealthDecisionEvent", "request_healthcare_services")
        self.valid_services = ["general", "specialized", "emergency"]

    async def allocate_healthcare_resources(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        healthcare_capacity = self.profile.get_data("healthcare_capacity", 0.0)
        policy_directives = self.profile.get_data("policy_directives", "")
        if healthcare_capacity <= 0 or not policy_directives:
            return []
    
        # Retrieve required variables
        resource_availability = self.profile.get_data("resource_availability", 0.0)
        service_quality = self.profile.get_data("service_quality", "unknown")
        insurance_coverage = self.profile.get_data("insurance_coverage", "unknown")
    
        # Check if all required events have been received
        received_events = self.profile.get_data("received_events", set())
        required_events = {"StartEvent", "PolicyImplementationEvent"}
        if not required_events.issubset(received_events):
            return []
        
        # Update profile with received events
        received_events.update(required_events)
        self.profile.update_data("received_events", received_events)
    
        # Decision Making
        observation = f"Resource availability: {resource_availability}, Service quality: {service_quality}, Insurance coverage: {insurance_coverage}"
        instruction = """Allocate healthcare resources based on the current availability, service quality, and insurance coverage. 
        Ensure to provide the amount of resources allocated and the status of the allocation process.
        Return the response in the following JSON format:
    
        {
        "allocated_resources": "<Amount of resources allocated>",
        "allocation_status": "<Status of the allocation process>",
        "target_ids": ["<The string ID of the EnvAgent>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
    
        allocated_resources = result.get('allocated_resources', 0.0)
        allocation_status = result.get('allocation_status', "pending")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        if not target_ids:
            return []
    
        # Update agent profile with the allocated resources and allocation status
        self.profile.update_data("allocated_resources", allocated_resources)
        self.profile.update_data("allocation_status", allocation_status)
    
        # Prepare and send the HealthcareResourceAllocationEvent to the EnvAgent
        events = []
        for target_id in target_ids:
            healthcare_event = HealthcareResourceAllocationEvent(self.profile_id, target_id, allocation_status, allocated_resources)
            events.append(healthcare_event)
    
        return events

    async def request_healthcare_services(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if event.service_requested not in self.valid_services:
            return []
        
        # Update received events to include HealthDecisionEvent
        received_events = self.profile.get_data("received_events", set())
        received_events.add("HealthDecisionEvent")
        self.profile.update_data("received_events", received_events)
    
        # Data Access
        service_requested = event.service_requested
        priority_level = event.priority_level
        individual_health_status = self.profile.get_data("individual_health_status", "unknown")
    
        # Decision Making
        instruction = """
        Based on the individual's health status, requested service type, and priority level, 
        determine the healthcare service provision status. Return the decision in the following JSON format:
    
        {
        "service_provision_status": "<Status of healthcare service provision>",
        "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """
        observation = f"Service Requested: {service_requested}, Priority Level: {priority_level}, Health Status: {individual_health_status}"
        result = await self.generate_reaction(instruction, observation)
    
        # Response Processing
        service_provision_status = result.get('service_provision_status', "pending")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        if not target_ids:
            return []
    
        # Data Modification
        self.profile.update_data("service_provision_status", service_provision_status)
    
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            healthcare_event = HealthcareServiceProvidedEvent(self.profile_id, target_id, service_provision_status)
            events.append(healthcare_event)
    
        return events