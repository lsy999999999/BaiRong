
from typing import Any, List,Optional
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


class Employee(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "request_overtime_pay")

    async def request_overtime_pay(self, event: Event) -> List[Event]:
        # No specific condition for this action, proceed directly
        employee_id = self.profile.get_data("employee_id", "")
        overtime_hours = self.profile.get_data("overtime_hours", 0.0)
        overtime_reason = self.profile.get_data("overtime_reason", "")
    
        # Prepare instruction for LLM reaction
        instruction = """Generate the next steps for the Employee requesting overtime pay.
        Please return the information in the following JSON format:
    
        {
        "target_ids": ["<The string ID of the Employer agent>"],
        "details": {
            "employee_id": "<Unique identifier of the employee>",
            "overtime_hours": <Number of overtime hours claimed>,
            "overtime_reason": "<Reason for overtime work>"
        }
        }
        """
        
        observation = f"Employee ID: {employee_id}, Overtime Hours: {overtime_hours}, Overtime Reason: {overtime_reason}"
        result = await self.generate_reaction(instruction, observation)
    
        # Extract details and target_ids from the LLM's response
        target_ids = result.get('target_ids', [])
        details = result.get('details', {})
    
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Create and send OvertimeRequestEvent to each target
        events = []
        for target_id in target_ids:
            overtime_event = OvertimeRequestEvent(self.profile_id, target_id, **details)
            events.append(overtime_event)
    
        return events
