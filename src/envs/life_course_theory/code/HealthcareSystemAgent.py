from typing import Any, List, Optional
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import *

class HealthcareSystemAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("LifeStageHealthEvent", "evaluate_health_services")

    async def evaluate_health_services(self, event: Event) -> List[Event]:
        # Condition Check
        healthcare_resources = await self.get_env_data("healthcare_resources", 0.0)
        current_health_status = event.health_status

        if not current_health_status or healthcare_resources <= 0.0:
            return []

        # Instruction for LLM
        instruction = """Evaluate the impact of healthcare services on the individual's health status.
        Consider the healthcare resources available and the individual's current health status.
        Return the results in the following JSON format:

        {
        "health_outcome": "<Description of the healthcare service outcome>",
        "service_quality": <Quantitative measure of healthcare service quality>,
        "target_ids": ["<The string ID(s) of the target Individual agent(s)>"]
        }
        """
        observation = f"Current health status: {current_health_status}, Healthcare resources: {healthcare_resources}"

        result = await self.generate_reaction(instruction, observation)

        # Parse LLM response
        health_outcome = result.get('health_outcome', "")
        service_quality = result.get('service_quality', 0.0)
        target_ids = result.get('target_ids', None)

        if target_ids is None:
            target_ids = []
        elif not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent state
        self.profile.update_data("health_services_evaluated", True)

        # Prepare and send HealthServiceOutcomeEvent
        events = []
        for target_id in target_ids:
            outcome_event = HealthServiceOutcomeEvent(self.profile_id, target_id, health_outcome, service_quality)
            events.append(outcome_event)

        return events