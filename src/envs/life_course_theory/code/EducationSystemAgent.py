from typing import Any, List, Optional
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

class EducationSystemAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("LifeStageProgressEvent", "assess_education_impact")

    async def assess_education_impact(self, event: Event) -> List[Event]:
        # Condition Check
        current_life_stage = event.life_stage
        socioeconomic_background = self.profile.get_data("socioeconomic_background", "default")
        
        if not (current_life_stage and socioeconomic_background):
            return []  # Return an empty list if condition is not met
    
        # Data Access
        educational_resources = await self.get_env_data("educational_resources", 0.0)
        educational_impact = event.educational_impact
    
        # Decision Making
        instruction = """Evaluate the impact of educational systems on individual agents based on their current life stage and socioeconomic background.
        Provide details on the educational outcome and adaptation level for the individual.
        Return the information in the following JSON format:
    
        {
            "education_outcome": "<Description of the educational outcome>",
            "adaptation_level": <Quantitative measure of adaptation>,
            "target_ids": ["<ID of the target IndividualAgent>"]
        }
        """
        
        observation = f"Life Stage: {current_life_stage}, Socioeconomic Background: {socioeconomic_background}, Educational Impact: {educational_impact}, Resources: {educational_resources}"
        
        result = await self.generate_reaction(instruction, observation)
        
        education_outcome = result.get('education_outcome', "")
        adaptation_level = result.get('adaptation_level', 0.0)
        self.profile.update_data("education_impact_assessed", True)
        target_ids = result.get('target_ids', [])
        
        if target_ids is None:
            target_ids = []
        elif not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Response Processing
        events = []
        for target_id in target_ids:
            education_event = EducationOutcomeEvent(self.profile_id, target_id, education_outcome, adaptation_level)
            events.append(education_event)
        
        return events