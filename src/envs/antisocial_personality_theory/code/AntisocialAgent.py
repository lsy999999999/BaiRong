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

class AntisocialAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_interaction")
        self.register_event("EnvironmentResponseEvent", "manipulate_or_disrespect")

    async def initiate_interaction(self, event: Event) -> List[Event]:
        personal_goal = self.profile.get_data("personal_goal", "undefined")
        candidate_ids = await self.env.get_agent_data_by_type("SocialEnvironmentAgent", "id")

        instruction = f"""
        You are an AntisocialAgent with a personal goal of '{personal_goal}'. 
        You are tasked with initiating a social interaction that aligns with your antisocial personality traits, 
        such as manipulation or disrespect, to achieve your personal gain. 
        Please determine the target_id(s) for this interaction and provide any relevant interaction details. 
        Candidate IDs of SocialEnvironmentAgent: {candidate_ids}
        Return the response in the following JSON format:
    
        {{
            "target_ids": ["<Target agent IDs>"]
        }}
        """
        
        result = await self.generate_reaction(instruction)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        self.profile.update_data("interaction_status", "initiated")
    
        events = []
        for target_id in target_ids:
            interaction_event = InteractionInitiatedEvent(self.profile_id, target_id)
            events.append(interaction_event)
    
        return events

    async def manipulate_or_disrespect(self, event: Event) -> List[Event]:
        if not isinstance(event, EnvironmentResponseEvent):
            return []
        
        if self.profile.get_data("event_processed", False):
            return []
        
        response_type = event.response_type
        response_intensity = event.response_intensity
    
        instruction = f"""
        The agent is interacting within a social environment and has received a response.
        The response type is '{response_type}' and its intensity is {response_intensity}.
        The agent needs to decide on a 'manipulation_strategy' to either manipulate or disrespect.
        Based on the response intensity, for high intensity, prefer manipulation; for low intensity, prefer disrespect.
        Return the decision in the following JSON format:
    
        {{
            "manipulation_strategy": "<The chosen strategy for manipulation or disrespect>",
            "target_ids": ["<List of target agent IDs or a single target ID>"]
        }}
        """
        observation = f"Response received: Type={response_type}, Intensity={response_intensity}"
        result = await self.generate_reaction(instruction, observation)
    
        manipulation_strategy = result.get('manipulation_strategy', "coercion")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        self.profile.update_data('manipulation_strategy', manipulation_strategy)
    
        events = []
        if manipulation_strategy == "manipulation":
            for target_id in target_ids:
                manipulation_event = ManipulationAttemptEvent(
                    self.profile_id, target_id, manipulation_strategy
                )
                events.append(manipulation_event)
        else:
            for target_id in target_ids:
                disrespect_event = DisrespectActionEvent(
                    self.profile_id, target_id, disrespect_type="verbal", severity_level=1
                )
                events.append(disrespect_event)
        
        self.profile.update_data("event_processed", False)
    
        return events