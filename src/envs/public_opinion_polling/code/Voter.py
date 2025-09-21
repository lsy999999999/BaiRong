from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class Voter(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("VoterSelectedEvent", "participate_in_poll")

    async def participate_in_poll(self, event: Event) -> List[Event]:
        # Check if voter_id is present in the event
        if not event.voter_id:
            return []  # Return empty list if voter_id is not provided

        # Retrieve necessary data from the event and agent profile
        selected_voter_id = event.voter_id
        pollster_id = event.pollster_id
    
        # Generate the instruction for LLM
        instruction = """You are a voter participating in a poll. Based on your current policy preferences, 
        decide how to express these preferences during the poll. Additionally, determine if your preferences 
        should be adjusted based on the interaction with the pollster. The response should be in the following JSON format:
        
        {
        "expressed_preferences": "<A data structure containing your expressed policy preferences>",
        "adjusted_preferences": "<A data structure containing adjusted policy preferences>",
        "interaction_trust_level": <A float value representing the trust level in the interaction>,
        "target_ids": ["<The string ID of the Pollster agent>", "ENV"]
        }
        """
        
        observation = f"Selected voter ID: {selected_voter_id}, Pollster ID: {pollster_id}"
        
        # Generate reaction using the instruction
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's response
        expressed_preferences = result.get('expressed_preferences', {})
        adjusted_preferences = result.get('adjusted_preferences', {})
        interaction_trust_level = result.get('interaction_trust_level', 0.0)
        target_ids = result.get('target_ids', [])
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Create and send appropriate events
        events = []
        env_agent_id = self.profile.get_data("env_agent_id", "EnvAgent")  # Use configuration or constant for "EnvAgent"
        for target_id in target_ids:
            if target_id == pollster_id:
                # Create ExpressOpinionEvent
                opinion_event = ExpressOpinionEvent(selected_voter_id, pollster_id, expressed_preferences)
                events.append(opinion_event)
            elif target_id == env_agent_id:
                # Create PreferencesAdjustedEvent
                adjusted_event = PreferencesAdjustedEvent(selected_voter_id, env_agent_id, adjusted_preferences, interaction_trust_level)
                events.append(adjusted_event)
    
        return events