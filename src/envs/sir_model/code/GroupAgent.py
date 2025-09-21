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

class GroupAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("RiskAssessmentEvent", "update_social_contact_pattern")
        self.register_event("PolicyImpactEvent", "update_social_contact_pattern")

    async def update_social_contact_pattern(self, event: Event) -> List[Event]:
        # No condition specified for this action, proceed with handler logic

        # Retrieve required data
        contact_pattern = self.profile.get_data("contact_pattern", "normal")
        impact_level = getattr(event, 'impact_level', 0.0)

        # Check validity of impact_level
        if impact_level < 0.0 or impact_level > 1.0:
            logger.error(f"Invalid impact_level: {impact_level}")
            return []  # Return empty list if impact_level is invalid

        # Prepare instruction for generate_reaction
        instruction = """Modify the social contact pattern within the group based on external influences like policies.
        Return the updated contact pattern and the target_ids as a list of IDs affected by this change.
        Please provide the information in the following JSON format:
        {
            "updated_contact_pattern": "<new contact pattern>",
            "target_ids": ["<list of target IndividualAgent IDs>"]
        }
        Note: The target_ids should be the IDs of the IndividualAgent(s) that are affected by the policy impact.
        """
        observation = f"Current contact pattern: {contact_pattern}, Impact level: {impact_level}"

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        updated_contact_pattern = result.get('updated_contact_pattern', contact_pattern)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state with the updated contact pattern
        self.profile.update_data("contact_pattern", updated_contact_pattern)

        # Prepare and send the SocialContactPatternEvent to each target_id
        events = []
        for target_id in target_ids:
            social_contact_event = SocialContactPatternEvent(self.profile_id, target_id, group_id=self.profile_id, contact_pattern=updated_contact_pattern)
            events.append(social_contact_event)

        return events