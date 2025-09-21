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

class SocialAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_social_needs")

    async def evaluate_social_needs(self, event: Event) -> List[Event]:
        # Condition Check: No specific condition, proceed with the action
        # Data Access: Retrieve agent's current social needs status and interactions needed
        social_needs_status = self.profile.get_data("social_needs_status", "unknown")
        social_interactions_needed = self.profile.get_data("social_interactions_needed", [])
    
        # Decision Making: Generate reaction using LLM
        instruction = """Evaluate the agent's social environment and determine if social needs are being met.
        Return the updated status of social needs, the list of social interactions needed, and target_ids for further actions.
        Respond in the following JSON format:
        {
            "social_needs_status": "<Updated status>",
            "social_interactions_needed": ["<List of interactions>"],
            "target_ids": ["<Target agent IDs>"]
        }
        """
        observation = f"Current social needs status: {social_needs_status}, Social interactions needed: {social_interactions_needed}"
        
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM's JSON response
        updated_social_needs_status = result.get("social_needs_status", "unknown")
        updated_social_interactions_needed = result.get("social_interactions_needed", [])
        target_ids = result.get("target_ids", [])
        
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Data Modification: Update agent's profile with new social needs status and interactions needed
        self.profile.update_data("social_needs_status", updated_social_needs_status)
        self.profile.update_data("social_interactions_needed", updated_social_interactions_needed)
    
        # Response Processing: Prepare outgoing events based on evaluation
        events = []
        satisfaction_level = 1.0 if updated_social_needs_status == "satisfied" else 0.0
        for target_id in target_ids:
            social_needs_event = SocialNeedsSatisfiedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                agent_id=self.profile_id,
                social_interactions=updated_social_interactions_needed,
                satisfaction_level=satisfaction_level
            )
            events.append(social_needs_event)
    
        return events