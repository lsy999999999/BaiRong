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

class IndividualAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "begin_life_stage")
        self.register_event("FamilySupportEvent", "receive_family_support")
        self.register_event("EducationOutcomeEvent", "adapt_to_education_outcome")
        self.register_event("HealthServiceOutcomeEvent", "integrate_health_outcome")
        self.register_event("PolicyImpactEvent", "adjust_to_policy_changes")

    async def begin_life_stage(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != 'StartEvent':
            return []

        socioeconomic_status = await self.get_env_data("socioeconomic_status", "unknown")
        initial_health_status = await self.get_env_data("initial_health_status", "unknown")

        current_life_stage = self.profile.get_data("current_life_stage", "unknown")
        instruction_stage = """
        Determine the new life stage based on the current life stage and socioeconomic factors.
        Please return the information in the following JSON format:

        {
        "new_stage": "<The new life stage>"
        }
        """
        observation_stage = f"Socioeconomic Status: {socioeconomic_status}, Current Life Stage: {current_life_stage}"
        result_stage = await self.generate_reaction(instruction_stage, observation_stage)
        new_stage = result_stage.get('new_stage', "unknown_stage")
        self.profile.update_data("current_life_stage", new_stage)

        instruction = """
        Initiate the 'begin_life_stage' process by assessing the impact of socioeconomic and health factors.
        Please return the information in the following JSON format:

        {
        "education_target_ids": ["<The string ID(s) of the EducationSystemAgent>"],
        "healthcare_target_ids": ["<The string ID(s) of the HealthcareSystemAgent>"]
        }
        """
        observation = f"Socioeconomic Status: {socioeconomic_status}, Initial Health Status: {initial_health_status}, Current Life Stage: {new_stage}"

        result = await self.generate_reaction(instruction, observation)

        education_target_ids = result.get('education_target_ids', [])
        healthcare_target_ids = result.get('healthcare_target_ids', [])
        if not isinstance(education_target_ids, list):
            education_target_ids = [education_target_ids]
        if not isinstance(healthcare_target_ids, list):
            healthcare_target_ids = [healthcare_target_ids]

        events = []
        for education_target_id in education_target_ids:
            life_stage_progress_event = LifeStageProgressEvent(
                self.profile_id, education_target_id, educational_impact=0.0, life_stage=new_stage
            )
            events.append(life_stage_progress_event)
        for healthcare_target_id in healthcare_target_ids:
            life_stage_health_event = LifeStageHealthEvent(
                self.profile_id, healthcare_target_id, health_services_impact=0.0, health_status=initial_health_status
            )
            events.append(life_stage_health_event)

        return events

    async def receive_family_support(self, event: Event) -> List[Event]:
        support_type = event.support_type
        support_level = event.support_level

        instruction = """
        You are processing a family support event for an individual agent. 
        The event includes support_type and support_level which impact the individual's state.
        Your task is to determine the integration status of the family support and decide the target_ids for sending a final event.
        Return the information in the following JSON format:

        {
        "family_support_status": "<The status of family support integration>",
        "target_ids": ["<The string ID of the EnvAgent>"]
        }
        """

        observation = f"Support Type: {support_type}, Support Level: {support_level}"
        result = await self.generate_reaction(instruction, observation)

        family_support_status = result.get('family_support_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("family_support_status", family_support_status)

        events = []
        for target_id in target_ids:
            integration_event = FamilySupportIntegratedEvent(self.profile_id, target_id, integration_status=family_support_status)
            events.append(integration_event)

        return events

    async def adjust_to_policy_changes(self, event: Event) -> List[Event]:
        policy_effect = event.policy_effect
        impact_level = event.impact_level

        observation = f"Policy effect: {policy_effect}, Impact level: {impact_level}"

        instruction = """Based on the policy effect and impact level, determine how the individual agent should adjust its decisions and behaviors. 
        This adjustment should be reflected in the agent's profile by updating the 'adjustment_status'. 
        The agent's relationships are provided, and you need to decide which target_ids should receive the outgoing event. 
        Return the information in the following JSON format:

        {
        "adjustment_status": "<Updated status of policy adjustment>",
        "target_ids": ["<The string ID(s) of target agents>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        adjustment_status = result.get('adjustment_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("adjustment_status", adjustment_status)

        events = []
        for target_id in target_ids:
            adjustment_event = PolicyAdjustmentCompletedEvent(self.profile_id, target_id, adjustment_status=adjustment_status)
            events.append(adjustment_event)

        return events

    async def adapt_to_education_outcome(self, event: Event) -> List[Event]:
        education_outcome = event.education_outcome
        adaptation_level = event.adaptation_level

        instruction = """
        You are tasked with adapting an individual's behavior and decisions based on educational outcomes.
        Use the 'education_outcome' and 'adaptation_level' to determine the adaptation status.
        Please return the information in the following JSON format:

        {
        "education_adaptation_status": "<Status of the individual's adaptation>",
        "target_ids": ["<The string ID(s) of the target agent(s) or 'ENV'>"]
        }
        """
        observation = f"Education Outcome: {education_outcome}, Adaptation Level: {adaptation_level}"
        result = await self.generate_reaction(instruction, observation)

        education_adaptation_status = result.get('education_adaptation_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("education_adaptation_status", education_adaptation_status)

        events = []
        for target_id in target_ids:
            adaptation_event = EducationAdaptationCompletedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                adaptation_status=education_adaptation_status
            )
            events.append(adaptation_event)

        return events

    async def integrate_health_outcome(self, event: Event) -> List[Event]:
        health_outcome = event.health_outcome
        service_quality = event.service_quality

        observation = f"Health outcome: {health_outcome}, Service quality: {service_quality}"
        instruction = """Integrate the received health service outcome into the individual's life. 
        Update the 'health_integration_status' based on the health outcome and service quality. 
        Determine the appropriate target_ids for sending the HealthIntegrationCompletedEvent. 
        Please return the information in the following JSON format:

        {
        "health_integration_status": "<Updated status of health service outcome integration>",
        "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        health_integration_status = result.get('health_integration_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("health_integration_status", health_integration_status)

        events = []
        for target_id in target_ids:
            integration_event = HealthIntegrationCompletedEvent(self.profile_id, target_id, integration_status=health_integration_status)
            events.append(integration_event)

        return events