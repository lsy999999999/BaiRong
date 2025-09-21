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

class Employer(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("OvertimeRequestEvent", "defend_overtime_claim")

    async def defend_overtime_claim(self, event: Event) -> List[Event]:
        # Check if the event is of the correct type
        if event.__class__.__name__ != "OvertimeRequestEvent":
            return []

        # Extract necessary data from the event
        employee_id = event.employee_id
        overtime_hours = event.overtime_hours
        overtime_reason = event.overtime_reason

        # Retrieve required variables from agent context
        employer_id = self.profile.get_data("employer_id", "")

        # Formulate the instruction for LLM
        instruction = """
        The Employer needs to formulate a defense against an overtime pay claim.
        Please provide the defense arguments and evidence documents in response to the employee's claim.
        The response should include the following JSON format:
        {
            "defense_arguments": "<Arguments against the overtime claim>",
            "evidence_documents": ["<List of evidence document identifiers>"],
            "target_ids": ["<The string ID of the Judge agent(s)>"]
        }
        """
        observation = f"Employee ID: {employee_id}, Overtime Hours: {overtime_hours}, Reason: {overtime_reason}"

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract results
        defense_arguments = result.get('defense_arguments', "")
        evidence_documents = result.get('evidence_documents', [])
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the DefenseSubmissionEvent to the Judge(s)
        events = []
        for target_id in target_ids:
            defense_event = DefenseSubmissionEvent(employer_id, target_id, employer_id, defense_arguments, evidence_documents)
            events.append(defense_event)

        return events