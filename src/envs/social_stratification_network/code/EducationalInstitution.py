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

class EducationalInstitution(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "select_students")
        self.register_event("ApplicationReceivedEvent", "select_students")
        self.register_event("EducationInvestmentDecidedEvent", "receive_application")

    async def select_students(self, event: Event) -> List[Event]:
        # Check the condition: Applications received from families
        applications_received = self.profile.get_data("applications_received", [])
        if not applications_received:
            return []

        # Retrieve admission criteria
        admission_criteria = self.profile.get_data("admission_criteria", {})

        # Prepare the instruction for the LLM
        # You can only choose at most one student at a time. 
        instruction = """
        Based on the admission criteria provided, evaluate the application in the received list.
        If the student is selected, return the list of IDs of selected students. Else return an empty list.

        {
        "selected_students_id": ["<List of student IDs who meet the criteria>"],
        }
        """

        # Generate a reaction using the admission criteria and applications received
        observation = f"Admission Criteria: {admission_criteria}, Application: {applications_received}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the result
        selected_students_ids = result.get('selected_students_id', [])
        target_ids = selected_students_ids
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the selected students in the agent's profile
        self.profile.update_data("selected_students", selected_students_ids)
        all_selected_student = list(set(self.profile.get_data("all_selected_students", []) + selected_students_ids))
        self.profile.update_data("all_selected_students", all_selected_student)

        for student in selected_students_ids:
            applications_received = list(filter(lambda x: x != student, applications_received))

        self.profile.update_data("applications_received", applications_received)


        # Prepare and send the StudentsSelectedEvent to the relevant Family agents
        events = []
        for target_id in target_ids:
            students_selected_event = StudentsSelectedEvent(
                self.profile_id,
                target_id,
                institution_id=self.profile_id,
                selected_students_ids=selected_students_ids
            )
            events.append(students_selected_event)

        return events

    async def receive_application(self, event: Event) -> List[Event]:
        # Extract application data from the event
        from_agent_id = event.from_agent_id

        # Update the applications_received list in the agent's profile
        applications_received = self.profile.get_data("applications_received", [])
        applications_received.append(from_agent_id)
        self.profile.update_data("applications_received", applications_received)
        all_applications_received = list(set(self.profile.get_data("all_applications_received", []) + applications_received))
        self.profile.update_data("all_applications_received", all_applications_received)
        

        # Generate a reaction to decide on target_ids and application_id
        # observation = f"Application data received from: {application_data}"
        # instruction = """Please process the application data and determine the appropriate target institution IDs for the application.
        # Return a JSON response with the following format:
        # {
        #     "target_ids": ["<List of institution IDs or a single institution ID>"],
        #     "application_id": "<Unique ID for the application>"
        # }
        # """

        # result = await self.generate_reaction(instruction, observation)

        # # Extract target_ids and application_id from the LLM's response
        # target_ids = result.get('target_ids', None)
        # application_id = result.get('application_id', None)
        # if not isinstance(target_ids, list):
        #     target_ids = [target_ids]

        # # Prepare and send ApplicationReceivedEvent to each target institution
        # events = []
        # for target_id in target_ids:
        #     application_received_event = ApplicationReceivedEvent(
        #         self.profile_id,
        #         target_id,
        #         institution_id=self.profile_id,
        #         application_id=application_id
        #     )
        #     events.append(application_received_event)

        events = []
        target_ids = [self.profile_id]
        for target_id in target_ids:
            application_received_event = ApplicationReceivedEvent(
                self.profile_id,
                target_id,
                institution_id=self.profile_id,
                # application_id=application_id
            )
            events.append(application_received_event)


        return events