from typing import Any, List, Optional
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class Family(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "decide_education_investment")
        self.register_event("StudentsSelectedEvent", "receive_admission_decision")
        self.register_event("AdmissionDecisionReceivedEvent", "allocate_education_resources")

    async def decide_education_investment(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "StartEvent":
            return []

        collective_resources = self.profile.get_data("collective_resources", 0.0)
        education_strategy = self.profile.get_data("education_strategy", "")


        instruction = """You are tasked with deciding on education investments for a family. 
        Based on the available collective resources and the family's education strategy, 
        determine the investment amount and the target educational institutions. 
        Please provide the response in the following JSON format:

        {
            "investment_amount": <float value representing the amount of resources allocated>,
            "target_ids": ["<List of string IDs of the educational institutions to apply to>"]
        }
        """

        observation = f"Collective resources: {collective_resources}, Education strategy: {education_strategy}"
        result = await self.generate_reaction(instruction, observation)

        investment_amount = result.get('investment_amount', 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        if not all(item.isdigit() for item in target_ids):
            target_ids = []

        self.profile.update_data("education_investment", investment_amount)

        events = []
        family_id = self.profile_id
        for institution_id in target_ids:
            event = EducationInvestmentDecidedEvent(from_agent_id=family_id, to_agent_id=institution_id, family_id=family_id, institution_id=institution_id, investment_amount=investment_amount)
            events.append(event)

        return events

    async def receive_admission_decision(self, event: Event) -> List[Event]:
        # if not hasattr(event, 'admission_status') or event.admission_status not in ["accepted", "rejected"]:
        #     return []

        admission_decisions = self.profile.get_data("admission_decisions", "None")

        instruction = """You have received an admission decision from an educational institution.
        If you decide to go to the institution, please update the admission_status and put the ID of the institution in an empty list. Else return an unchanged admission status.

        Please return the information in the following JSON format:
        {
            "new_admission_status": "<The educational institution ID that you will go (only one ID).>",
        }
        """

        observation = f"Current admission status: {admission_decisions}, Institution ID: {event.institution_id}"
        result = await self.generate_reaction(instruction, observation)

        admission_status = result.get('new_admission_status', "None")
        target_ids = [self.profile_id]
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("admission_decisions", admission_decisions)

        events = []
        for target_id in target_ids:
            admission_event = AdmissionDecisionReceivedEvent(self.profile_id, target_id, family_id=self.profile_id, admission_status=admission_status)
            events.append(admission_event)

        return events

    async def allocate_education_resources(self, event: Event) -> List[Event]:
        admission_decisions = self.profile.get_data("admission_decisions", [])

        observation = f"Admission decisions: {admission_decisions}, Event family_id: {event.family_id}, Admission status: {event.admission_status}"

        instruction = """
        Based on the admission decisions received and the current event data, calculate the total resources allocated for education.
        Please return the information in the following JSON format:

        {
        "allocated_resources": "<Calculated float value of resources allocated>",
        "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        allocated_resources = result.get('allocated_resources', 0.0)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("allocated_resources", allocated_resources)

        events = []
        for target_id in target_ids:
            resources_event = EducationResourcesAllocatedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                family_id=event.family_id,
                resources_allocated=allocated_resources
            )
            events.append(resources_event)

        return events