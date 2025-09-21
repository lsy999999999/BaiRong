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

class IndividualAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "evaluate_social_capital")
        self.register_event("SocialCapitalEvaluatedEvent", "decide_cooperation")

    async def evaluate_social_capital(self, event: Event) -> List[Event]:
        # Retrieve required variables from event or initialize
        individual_id = self.profile.get_data("individual_id", "")
        initial_social_capital = self.profile.get_data("initial_social_capital", 0.0)

        # Prepare instruction for LLM
        instruction = """
        Evaluate the social capital of the individual based on the initial social capital and any additional criteria you deem necessary. 
        Determine the updated social capital value and whether the individual has the potential to cooperate.
        Please return the information in the following JSON format:
    
        {
        "social_capital_value": <Updated social capital value as a float>,
        "cooperation_potential": <Boolean indicating cooperation potential>,
        "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """
        
        # Generate reaction using LLM
        observation = f"Individual ID: {individual_id}, Initial Social Capital: {initial_social_capital}"
        result = await self.generate_reaction(instruction=instruction, observation=observation)
        
        # Extract results from LLM response
        social_capital_value = result.get('social_capital_value', initial_social_capital)
        cooperation_potential = result.get('cooperation_potential', False)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update agent profile with new values
        self.profile.update_data("social_capital_value", social_capital_value)
        self.profile.update_data("cooperation_potential", cooperation_potential)
        
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            event = SocialCapitalEvaluatedEvent(
                self.profile_id, target_id, individual_id, social_capital_value, cooperation_potential
            )
            events.append(event)
        
        return events

    async def decide_cooperation(self, event: Event) -> List[Event]:
        # Condition Check: Ensure event is an instance of SocialCapitalEvaluatedEvent
        if not isinstance(event, SocialCapitalEvaluatedEvent):
            return []
    
        individual_id = event.individual_id
        social_capital_value = event.social_capital_value
        cooperation_potential = event.cooperation_potential
    
        # Decision Making using generate_reaction
        observation = f"Individual ID: {individual_id}, Social Capital Value: {social_capital_value}, Cooperation Potential: {cooperation_potential}"
        instruction = """
        Evaluate the social capital and trust levels of the individual to decide on cooperation. 
        If the social capital value is above a certain threshold and the cooperation potential is true, decide to cooperate. 
        Otherwise, decide not to cooperate. Return the result in the following JSON format:
        {
            "decision": "<'cooperate' or 'not_cooperate'>",
            "impact_on_network": "<The expected impact based on the decision>",
            "target_ids": ["<The string ID(s) of the SocialNetworkAgent(s)>"]
        }
        """
    
        result = await self.generate_reaction(instruction=instruction, observation=observation)
    
        decision = result.get('decision', 'not_cooperate')
        impact_on_network = result.get('impact_on_network', 'none')
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state with the decision
        self.profile.update_data("decision", decision)
    
        # Prepare and send the CooperationDecisionEvent to the SocialNetworkAgent
        events = []
        for target_id in target_ids:
            cooperation_event = CooperationDecisionEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                individual_id=individual_id,
                decision=decision,
                impact_on_network=impact_on_network
            )
            events.append(cooperation_event)
    
        return events