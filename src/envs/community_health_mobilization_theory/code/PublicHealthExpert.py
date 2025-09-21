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

class PublicHealthExpert(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "provide_guidance")

    async def provide_guidance(self, event: Event) -> List[Event]:
        # Condition Check: Since the condition is "null", we proceed directly.

        # Extract necessary data from the event with default values
        guidance_details = getattr(event, 'guidance_details', 'None')
        expert_id = getattr(event, 'expert_id', 'unknown')

        # Instruction for LLM to determine the next steps
        instruction = """
        You are a Public Health Expert in a community health mobilization simulation. Your task is to provide guidance and resources to support community leaders in health mobilization efforts. Based on the current guidance details and your expert ID, decide the target community leaders who should receive this guidance. Also, update the guidance status.
        
        Please return the information in the following JSON format:
        {
            "guidance_status": "<Status of the guidance dissemination>",
            "target_ids": ["<The string ID(s) of the CommunityLeader agent(s)>"]
        }
        """

        # Generate reaction using the LLM
        observation = f"Guidance Details: {guidance_details}, Expert ID: {expert_id}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's response
        guidance_status = result.get('guidance_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids] if target_ids else []

        # Update the agent's profile with the new guidance status
        self.profile.update_data("guidance_status", guidance_status)

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            guidance_event = GuidanceEvent(self.profile_id, target_id, guidance_details=guidance_details, expert_id=expert_id)
            events.append(guidance_event)

        # Additionally, send a GuidanceCompletedEvent to the EnvAgent
        guidance_completed_event = GuidanceCompletedEvent(self.profile_id, "ENV", completion_status="completed", results_summary="Guidance provided to community leaders.")
        events.append(guidance_completed_event)

        return events